"""
API viewsets and utility views for user authentication, registration,
OTP lifecycle, and lockout recovery.

Organized into modular viewsets:
- PasswordAuthViewSet: login and signup using username and password.
- EmailOTPAuthViewSet: send OTP, login, and signup using email.
- SMSOTPAuthViewSet: send OTP, login, and signup using phone number.
"""

import datetime
import logging
import secrets
import typing

from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users import app_settings, get_user_model
from core.apps.users.api.serializers import (
    EmailOTPLoginSerializer,
    EmailOTPSendSerializer,
    EmailOTPSignupSerializer,
    GoogleLoginSerializer,
    PasswordLoginSerializer,
    PasswordSignupSerializer,
    PhoneOTPLoginSerializer,
    PhoneOTPSendSerializer,
    PhoneOTPSignupSerializer,
)
from core.apps.users.constants import SocialProviderChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.apps.users.services.social import SocialAuthServiceFactory
from core.apps.users.utils import get_auth_redirect_url

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

LOGGER = logging.getLogger(__name__)
User = get_user_model()


def get_jwt_tokens_for_user(user: "AbstractUser") -> dict:
    """
    Generate SimpleJWT access and refresh tokens for a user.

    Applies lifetime jitter between 65% and 75% of the configured lifetime
    to prevent synchronized token expiration stampedes.

    Args:
        user (AbstractUser): Authenticated user instance.

    Returns:
        dict: Dictionary containing ``access`` token, ``refresh`` token, and ``access_expires_in`` seconds.
    """

    def get_jitter_expiry():
        base_lifetime = jwt_settings.ACCESS_TOKEN_LIFETIME
        jitter_factor = secrets.SystemRandom().uniform(0.65, 0.75)
        return max(60, int(base_lifetime.total_seconds() * jitter_factor))

    refresh = RefreshToken.for_user(user)
    token_expiry = get_jitter_expiry()
    refresh.access_token.set_exp(lifetime=datetime.timedelta(seconds=token_expiry))

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "access_expires_in": token_expiry,
    }


def _build_auth_response(
    request, user: "AbstractUser", status_code=status.HTTP_200_OK, **extra_data
) -> Response:
    """
    Establish session login, generate JWT tokens, and return a standardized response.

    Attaches user data, access/refresh tokens, and post-authentication redirect URL.
    Optionally starts a Django request session if session middleware is active.

    Side effects:
    - Initiates Django session login if session middleware is present.

    Args:
        request (Request): DRF request object.
        user (AbstractUser): Authenticated user model instance.
        status_code (int, optional): HTTP status code. Defaults to 200 OK.

    Returns:
        Response: HTTP Response containing tokens, serialized user details, and redirect URL.
    """
    if hasattr(request, "session"):
        login(getattr(request, "_request", request), user)

    tokens = get_jwt_tokens_for_user(user)
    UserDetailSerializer = app_settings.USER_DETAILS_SERIALIZER
    user_data = UserDetailSerializer(user).data

    return Response(
        {
            **tokens,
            "user": user_data,
            "redirect_url": get_auth_redirect_url(request),
        },
        status=status_code,
    )


class PasswordAuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet handling password-based login and signup.

    Permissions: AllowAny.

    API details:
    - POST ``/api/users/v1/auth/password/login/``
        - **200**: User authenticated; JWT tokens and user profile returned.
        - **400**: Missing credentials or invalid username/password.
        - **403**: Password authentication disabled by configuration.
        - **423**: Account locked due to excessive failed attempts.
    - POST ``/api/users/v1/auth/password/signup/``
        - **201**: User created and authenticated; JWT tokens returned.
        - **400**: Payload validation failed (duplicate username, weak password).
        - **403**: Password authentication disabled by configuration.
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == "signup":
            return PasswordSignupSerializer
        return PasswordLoginSerializer

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request, *args, **kwargs):
        """
        Authenticate user with username and password.

        Validates credentials and enforces account lockout checks on consecutive failures.

        Side effects:
        - Increments failed attempt counter in cache on invalid credentials.
        - Clears failed attempt counter on successful login.

        Args:
            request (Request): DRF request with ``username`` and ``password``.

        Returns:
            Response: Auth tokens, user details, and redirect URL on success; error response otherwise.

        Raises:
            PermissionDenied: If password authentication is disabled.
        """
        if not app_settings.ENABLE_PASSWORD_LOGIN:
            raise PermissionDenied(
                _("Password-based authentication is currently disabled.")
            )

        username = request.data.get("username", "").strip()

        if AuthLockoutService.is_locked(username):
            return Response(
                {
                    "detail": _(
                        "Account locked due to too many failed attempts. If an account is associated with this identity, an unlock link has been emailed to you."
                    ),
                    "remaining_attempts": 0,
                    "is_locked": True,
                },
                status=status.HTTP_423_LOCKED,
            )

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            LOGGER.warning(f"Login failed for username {username}: {serializer.errors}")
            remaining, is_locked = AuthLockoutService.record_failed_attempt(username)
            if is_locked:
                return Response(
                    {
                        "detail": _("Account locked due to too many failed attempts."),
                        "remaining_attempts": 0,
                        "is_locked": True,
                    },
                    status=status.HTTP_423_LOCKED,
                )
            return Response(
                {
                    "detail": PasswordLoginSerializer.USER_NOT_FOUND_ERROR,
                    "remaining_attempts": remaining,
                    "is_locked": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        AuthLockoutService.clear_attempts(username)
        return _build_auth_response(request, user, status_code=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="signup")
    def signup(self, request, *args, **kwargs):
        """
        Register a new user account with username and password.

        Side effects:
        - Creates a new User row in the database.

        Args:
            request (Request): DRF request with registration fields.

        Returns:
            Response: HTTP 201 Created containing tokens and user profile.

        Raises:
            PermissionDenied: If password authentication is disabled.
        """
        if not app_settings.ENABLE_PASSWORD_LOGIN:
            raise PermissionDenied(
                _("Password-based authentication is currently disabled.")
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _build_auth_response(request, user, status_code=status.HTTP_201_CREATED)


class EmailOTPAuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet handling Email OTP-based dispatch, login, and signup.

    Permissions: AllowAny.

    API details:
    - POST ``/api/users/v1/auth/otp/email/send/``
        - **202**: OTP code generated and queued for background email delivery.
        - **400**: Invalid email address format.
        - **403**: OTP authentication disabled by configuration.
    - POST ``/api/users/v1/auth/otp/email/login/``
        - **200**: User authenticated via email OTP; JWT tokens returned.
        - **400**: Invalid OTP or unregistered email address.
        - **403**: OTP authentication disabled by configuration.
        - **423**: Email address temporarily locked due to excessive failed attempts.
    - POST ``/api/users/v1/auth/otp/email/signup/``
        - **201**: User created and authenticated with verified email.
        - **400**: Invalid OTP, missing fields, or email already registered.
        - **403**: OTP authentication disabled by configuration.
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == "send":
            return EmailOTPSendSerializer
        if self.action == "signup":
            return EmailOTPSignupSerializer
        return EmailOTPLoginSerializer

    @action(detail=False, methods=["post"], url_path="send")
    def send(self, request, *args, **kwargs):
        """
        Dispatch an OTP verification code to the target email address asynchronously.

        Side effects:
        - Queues ``send_otp_task`` Celery job for asynchronous email delivery.

        Args:
            request (Request): DRF request with ``email`` and optional ``purpose``.

        Returns:
            Response: HTTP 202 Accepted response.

        Raises:
            PermissionDenied: If OTP authentication is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send()

        return Response(
            {"detail": _("If the account exists, an OTP has been dispatched.")},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request, *args, **kwargs):
        """
        Verify Email OTP and authenticate existing user.

        Side effects:
        - Resets failed attempt counter in cache on successful verification.
        - Marks ``is_email_verified=True`` on user model if previously False.

        Args:
            request (Request): DRF request with ``email`` and ``otp_code``.

        Returns:
            Response: HTTP 200 OK containing JWT tokens and serialized user profile.

        Raises:
            PermissionDenied: If OTP login is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        email = request.data.get("email", "").strip().lower()
        if AuthLockoutService.is_locked(email):
            return Response(
                {
                    "detail": _("Account locked due to too many failed attempts."),
                    "remaining_attempts": 0,
                    "is_locked": True,
                },
                status=status.HTTP_423_LOCKED,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        AuthLockoutService.clear_attempts(email)
        return _build_auth_response(request, user, status_code=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="signup")
    def signup(self, request, *args, **kwargs):
        """
        Verify Email OTP and register a new user account.

        Side effects:
        - Creates a new User row with ``is_email_verified=True``.
        - Clears any lockout attempt counters for the registered email.

        Args:
            request (Request): DRF request with profile data, ``email``, and ``otp_code``.

        Returns:
            Response: HTTP 201 Created containing tokens and user profile.

        Raises:
            PermissionDenied: If OTP registration is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        email = serializer.validated_data.get("email")
        if email:
            AuthLockoutService.clear_attempts(email)
        return _build_auth_response(request, user, status_code=status.HTTP_201_CREATED)


class SMSOTPAuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet handling SMS/Phone OTP-based dispatch, login, and signup.

    Permissions: AllowAny.

    API details:
    - POST ``/api/users/v1/auth/otp/sms/send/``
        - **202**: OTP code generated and queued for background SMS delivery.
        - **400**: Invalid phone number format.
        - **403**: OTP authentication disabled by configuration.
    - POST ``/api/users/v1/auth/otp/sms/login/``
        - **200**: User authenticated via SMS OTP; JWT tokens returned.
        - **400**: Invalid OTP or unregistered phone number.
        - **403**: OTP authentication disabled by configuration.
        - **423**: Phone number temporarily locked due to excessive failed attempts.
    - POST ``/api/users/v1/auth/otp/sms/signup/``
        - **201**: User created and authenticated with verified phone number.
        - **400**: Invalid OTP, missing fields, or phone number already registered.
        - **403**: OTP authentication disabled by configuration.
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == "send":
            return PhoneOTPSendSerializer
        if self.action == "signup":
            return PhoneOTPSignupSerializer
        return PhoneOTPLoginSerializer

    @action(detail=False, methods=["post"], url_path="send")
    def send(self, request, *args, **kwargs):
        """
        Dispatch an OTP verification code to the target phone number asynchronously.

        Side effects:
        - Queues ``send_otp_task`` Celery job for asynchronous SMS delivery.

        Args:
            request (Request): DRF request with ``phone_number`` and optional ``purpose``.

        Returns:
            Response: HTTP 202 Accepted response.

        Raises:
            PermissionDenied: If OTP authentication is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send()

        return Response(
            {"detail": _("If the account exists, an OTP has been dispatched.")},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request, *args, **kwargs):
        """
        Verify Phone OTP and authenticate existing user.

        Side effects:
        - Resets failed attempt counter in cache on successful verification.
        - Marks ``is_phone_verified=True`` on user model if previously False.

        Args:
            request (Request): DRF request with ``phone_number`` and ``otp_code``.

        Returns:
            Response: HTTP 200 OK containing JWT tokens and serialized user profile.

        Raises:
            PermissionDenied: If OTP login is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        raw_phone = request.data.get("phone_number", "")
        if AuthLockoutService.is_locked(raw_phone):
            return Response(
                {
                    "detail": _("Account locked due to too many failed attempts."),
                    "remaining_attempts": 0,
                    "is_locked": True,
                },
                status=status.HTTP_423_LOCKED,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        validated_phone = serializer.validated_data.get("phone_number")
        AuthLockoutService.clear_attempts(validated_phone)
        return _build_auth_response(request, user, status_code=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="signup")
    def signup(self, request, *args, **kwargs):
        """
        Verify Phone OTP and register a new user account.

        Side effects:
        - Creates a new User row with ``is_phone_verified=True``.
        - Clears any lockout attempt counters for the registered phone number.

        Args:
            request (Request): DRF request with profile data, ``phone_number``, and ``otp_code``.

        Returns:
            Response: HTTP 201 Created containing tokens and user profile.

        Raises:
            PermissionDenied: If OTP registration is disabled.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        validated_phone = serializer.validated_data.get("phone_number")
        if validated_phone:
            clear_target = (
                validated_phone.as_e164
                if hasattr(validated_phone, "as_e164")
                else str(validated_phone)
            )
            AuthLockoutService.clear_attempts(clear_target)

        return _build_auth_response(request, user, status_code=status.HTTP_201_CREATED)


# ============================================================================
# Auxiliary Auth Endpoints: Social Auth, Account Unlock
# ============================================================================


class GoogleLoginView(APIView):
    """
    Authenticate or register a user using a Google OAuth2 ID token.

    API details:
    - POST ``/api/users/v1/auth/social/google/``
        - **200**: Google token verified; existing user authenticated.
        - **201**: Google token verified; new user created and authenticated.
        - **400**: Invalid or expired Google ID token.
        - **403**: Social authentication disabled by configuration.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Verify Google ID token and return session and JWT tokens.

        Side effects:
        - Creates user record and social auth link if first-time signin.

        Args:
            request (Request): DRF request with ``id_token``.

        Returns:
            Response: Auth tokens, user details, and redirect URL.

        Raises:
            PermissionDenied: If social login is disabled.
        """
        if not app_settings.ENABLE_SOCIAL_LOGIN:
            raise PermissionDenied(_("Social authentication is currently disabled."))

        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token_str = serializer.validated_data["id_token"]
        user, created = SocialAuthServiceFactory.authenticate_or_register(
            provider=SocialProviderChoices.GOOGLE, token_str=id_token_str
        )

        return _build_auth_response(
            request,
            user,
            status_code=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AccountUnlockView(APIView):
    """
    Verify an account unlock token and reactivate the user account.

    API details:
    - GET ``/api/users/v1/auth/unlock/?token={token}``
        - **200**: Account successfully unlocked.
        - **400**: Unlock token is invalid, expired, or already used.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Verify an account unlock token and clear lockout status.

        Side effects:
        - Removes lockout state and failure counters from cache.
        - Deletes used unlock token from cache.

        Args:
            request (Request): DRF request with ``token`` query parameter.

        Returns:
            Response: JSON payload indicating success and unlock status.
        """
        token = request.query_params.get("token", "")
        success, message = AuthLockoutService.verify_and_unlock_account(token)
        if success:
            return Response(
                {"detail": message, "unlocked": True},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": message, "unlocked": False},
            status=status.HTTP_400_BAD_REQUEST,
        )
