"""
API endpoints for user authentication, registration, OTP lifecycle, and lockout recovery.

Implements zero-enumeration login, asynchronous OTP delivery via task queueing,
and JWT token distribution into client cookies.
"""

import datetime
import logging
import secrets
import typing

from django.contrib.auth import login
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError as DRFValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users import app_settings, get_user_model
from core.apps.users.api.serializers import (
    GoogleLoginSerializer,
    LoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
)
from core.apps.users.constants import OTPChannelChoices, SocialProviderChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.apps.users.services.otp import OTPServiceFactory
from core.apps.users.services.social import SocialAuthServiceFactory
from core.apps.users.tasks import send_otp_task
from core.apps.users.utils import get_auth_redirect_url
from core.utils.tasks import queue_task

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
        # Random jitter: 65% to 75% of configured lifetime
        base_lifetime = jwt_settings.ACCESS_TOKEN_LIFETIME
        jitter_factor = secrets.SystemRandom().uniform(0.65, 0.75)
        return max(60, int(base_lifetime.total_seconds() * jitter_factor))

    refresh = RefreshToken.for_user(user)
    token_expiry = get_jitter_expiry()
    # TODO: Figure out a better way to do this, currently this only send wrong expiry to user
    # In database the expiry is still the one issued by RefreshToken.from_user(...)
    refresh.access_token.set_exp(lifetime=datetime.timedelta(seconds=token_expiry))

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "access_expires_in": token_expiry,
    }


class SignupView(APIView):
    """
    API view to register new user accounts.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Register a new user account with validated credentials.

        API details:
        - POST ``/api/v1/auth/signup/``
            - **201**: User created and authenticated; JWT cookies attached.
            - **400**: Payload validation failed (e.g. invalid email format, weak password).

        Args:
            request (Request): DRF request with user registration payload.

        Returns:
            Response: Serialized user details, tokens, and redirect URL.
        """
        SingupSerializer = app_settings.SIGNUP_SERIALIZER
        serializer = SingupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

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
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    API view for username/password login with attempt tracking and zero enumeration.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Authenticate user with username and password under zero-enumeration rules.

        Tracks failed attempts and locks out excessive failures to mitigate brute-force attacks.

        API details:
        - POST ``/api/v1/auth/login/``
            - **200**: Successfully authenticated; JWT cookies attached.
            - **400**: Missing credentials or incorrect username/password combination.
            - **403**: Password login disabled by configuration.
            - **423**: Account temporarily locked due to excessive failed attempts.

        Side effects:
            - Increments failed attempt counters in cache on invalid credentials.
            - Triggers lockout notification email and generates unlock token when lockout threshold is met.
            - Resets failed attempt counter on successful login.

        Args:
            request (Request): DRF request with ``username`` and ``password``.

        Returns:
            Response: Auth tokens, user details, and redirect URL on success; error message otherwise.

        Raises:
            PermissionDenied: If password login is disabled in application settings.
        """
        if not app_settings.ENABLE_PASSWORD_LOGIN:
            raise PermissionDenied(
                _("Password-based authentication is currently disabled.")
            )

        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if not username or not password:
            return Response(
                {"detail": _("Username and password are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check existing lockout
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

        serializer = LoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            LOGGER.warning(f"Login failed for username {username}: {e}")
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
                    "detail": LoginSerializer.USER_NOT_FOUND_ERROR,
                    "remaining_attempts": remaining,
                    "is_locked": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        AuthLockoutService.clear_attempts(username)

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
            status=status.HTTP_200_OK,
        )


class OTPSendView(APIView):
    """
    Dispatch one-time passcodes (OTP) via SMS or Email asynchronously.

    Validates identifier syntax and immediately returns HTTP 202 Accepted,
    queuing actual dispatch to a background worker to prevent user enumeration.
    """

    permission_classes = [AllowAny]
    serializer_class = OTPSendSerializer

    def post(self, request, *args, **kwargs):
        """
        Dispatch an OTP verification code to the given identifier asynchronously.

        Always returns 202 Accepted to prevent user enumeration regardless of
        whether the identifier exists in the database. The actual generation
        and delivery of the OTP is handled by a background Celery worker.

        API details:
        - POST ``/api/v1/auth/otp/send/``
            - **Request Body**:
                - ``identifier`` (string, required): Destination phone number (min 7 digits) or valid email address.
                - ``channel`` (string, optional): Delivery channel (``"phone"`` or ``"email"``). Defaults to ``"phone"``.
                - ``purpose`` (string, optional): Purpose of the OTP (``"login"``, ``"verification"``, ``"reset_password"``). Defaults to ``"login"``.
            - **202 Accepted**: Request accepted and dispatched to background queue.
                - ``detail`` (string): Generic confirmation message (e.g. ``"If the account exists, an OTP has been dispatched."``).
            - **400 Bad Request**: Invalid identifier syntax or channel parameters.
                - Validation error dict (e.g. ``{"identifier": ["Invalid phone number format."]}``).
            - **403 Forbidden**: OTP authentication is disabled by configuration.
                - ``detail`` (string): ``"OTP authentication is currently disabled."``

        Side effects:
            - Queues ``send_otp_task`` Celery job for asynchronous code generation and delivery.

        Args:
            request (Request): DRF request containing JSON body with:
                - ``identifier`` (str): Target phone number or email address.
                - ``channel`` (str, optional): Delivery channel (``"phone"`` or ``"email"``). Defaults to ``"phone"``.
                - ``purpose`` (str, optional): Purpose of OTP (``"login"``, ``"verification"``, or ``"reset_password"``). Defaults to ``"login"``.

        Returns:
            Response: HTTP 202 Accepted response containing:
                - ``detail`` (str): Generic status confirmation message.

        Raises:
            PermissionDenied:
                - OTP authentication is disabled in application settings.
            ValidationError:
                - Request body contains invalid phone/email syntax or invalid choice values.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        channel = serializer.validated_data["channel"]
        purpose = serializer.validated_data["purpose"]

        # Dispatch via standardized queue_task
        try:
            queue_task(
                task=send_otp_task,
                task_kwargs={
                    "identifier": identifier,
                    "channel": channel,
                    "purpose": purpose,
                },
                on_commit=True,  # API failure should not queue task
            )
        except Exception as e:
            LOGGER.error(f"Failed to queue OTP task for {identifier}: {e}")

        return Response(
            {"detail": _("If the account exists, an OTP has been dispatched.")},
            status=status.HTTP_202_ACCEPTED,
        )


class OTPVerifyView(APIView):
    """
    Verify OTP codes and authenticate or provision users with zero enumeration.

    Validates submitted passcodes, tracks failed attempts to prevent brute-force attacks,
    and returns JWT tokens upon successful verification.
    """

    permission_classes = [AllowAny]
    serializer_class = OTPVerifySerializer

    def post(self, request, *args, **kwargs):
        """
        Verify submitted OTP code and authenticate or provision the user.

        Validates the submitted OTP against the cache for the given identifier,
        enforces account lockout on excessive failed attempts, and authenticates
        the user upon successful verification. If the user does not exist and
        auto-registration is enabled, automatically creates and verifies a new user account.

        API details:
        - POST ``/api/v1/auth/otp/verify/``
            - **Request Body**:
                - ``identifier`` (string, required): Phone number or email address that received the code.
                - ``code`` (string, required): The OTP verification code (max 10 characters).
                - ``channel`` (string, optional): Delivery channel (``"phone"`` or ``"email"``). Defaults to ``"phone"``.
            - **200 OK**: OTP verified; existing user authenticated.
                - ``refresh`` (string): JWT refresh token.
                - ``access`` (string): JWT access token.
                - ``access_expires_in`` (int): Token expiry duration in seconds.
                - ``user`` (dict): Serialized user profile per ``USER_DETAILS_SERIALIZER``.
                - ``created`` (bool): ``False`` indicating an existing user account.
                - ``redirect_url`` (string): Post-authentication redirect target URL.
            - **201 Created**: OTP verified; new user provisioned and authenticated.
                - Payload schema matches **200 OK**, with ``created`` set to ``True``.
            - **400 Bad Request**: Invalid OTP, expired OTP, or auto-registration disabled.
                - On incorrect OTP: ``{"detail": "Incorrect OTP.", "remaining_attempts": int, "is_locked": false}``.
                - On validation error: Field error dictionary (e.g. ``{"code": ["This field is required."]}``).
            - **403 Forbidden**: OTP authentication disabled by configuration.
                - ``detail`` (string): ``"OTP authentication is currently disabled."``
            - **423 Locked**: Identity temporarily locked due to excessive failed verification attempts.
                - ``{"detail": "Account locked due to too many failed attempts.", "remaining_attempts": 0, "is_locked": true}``.

        Side effects:
            - Increments failed verification counter in cache on incorrect code.
            - Resets failed attempt counter on successful verification.
            - May create a new user record if auto-registration is enabled.
            - Updates ``is_phone_verified`` or ``is_email_verified`` flags on user.
            - Initiates Django session login if session middleware is active.

        Args:
            request (Request): DRF request containing JSON body with:
                - ``identifier`` (str): Phone number or email address that received the OTP code.
                - ``code`` (str): OTP verification code to validate.
                - ``channel`` (str, optional): Channel used for delivery (``"phone"`` or ``"email"``). Defaults to ``"phone"``.

        Returns:
            Response: HTTP 200 OK (existing user) or HTTP 201 Created (new user) containing:
                - ``refresh`` (str): JWT refresh token.
                - ``access`` (str): JWT access token.
                - ``access_expires_in`` (int): Token lifetime in seconds.
                - ``user`` (dict): Serialized user profile from ``USER_DETAILS_SERIALIZER``.
                - ``created`` (bool): True if user was newly provisioned, False otherwise.
                - ``redirect_url`` (str): Target redirect URL post-authentication.
                On error:
                - HTTP 400 Bad Request with ``detail``, ``remaining_attempts``, and ``is_locked`` (or field errors).
                - HTTP 403 Forbidden with ``detail`` if OTP is disabled.
                - HTTP 423 Locked with ``detail``, ``remaining_attempts``, and ``is_locked`` if account is locked.

        Raises:
            PermissionDenied:
                - OTP authentication is disabled in application settings.
            ValidationError:
                - Request body contains missing required fields or invalid choices.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]
        channel = serializer.validated_data["channel"]

        # Check existing lockout
        if AuthLockoutService.is_locked(identifier):
            return Response(
                {
                    "detail": _("Account locked due to too many failed attempts."),
                    "remaining_attempts": 0,
                    "is_locked": True,
                },
                status=status.HTTP_423_LOCKED,
            )

        is_valid, otp_msg = OTPServiceFactory.verify_otp(
            identifier=identifier, code=code
        )

        if not is_valid:
            LOGGER.warning(f"OTP login failed for {identifier}: {otp_msg}")
            remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
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
                    "detail": _("Incorrect OTP."),
                    "remaining_attempts": remaining,
                    "is_locked": False,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        AuthLockoutService.clear_attempts(identifier)

        user = None
        if channel == OTPChannelChoices.PHONE:
            user = User.objects.filter(phone_number=identifier).first()
        elif channel == OTPChannelChoices.EMAIL:
            user = User.objects.filter(email__iexact=identifier).first()

        created = False
        if not user:
            if not app_settings.ALLOW_AUTO_REGISTRATION_ON_OTP:
                return Response(
                    {
                        "detail": _("Incorrect OTP."),
                        "remaining_attempts": 0,
                        "is_locked": False,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Auto-register new user
            create_kwargs = {}
            if channel == OTPChannelChoices.PHONE:
                create_kwargs["phone_number"] = identifier
                create_kwargs["is_phone_verified"] = True
            elif channel == OTPChannelChoices.EMAIL:
                create_kwargs["email"] = identifier.lower()
                create_kwargs["is_email_verified"] = True

            user = User.objects.create_user(**create_kwargs)
            created = True
        else:
            # Mark verified if not already
            update_fields = []
            if channel == OTPChannelChoices.PHONE and not user.is_phone_verified:
                user.is_phone_verified = True
                update_fields.append("is_phone_verified")
            elif channel == OTPChannelChoices.EMAIL and not user.is_email_verified:
                user.is_email_verified = True
                update_fields.append("is_email_verified")

            if update_fields:
                update_fields.append("modified")
                user.save(update_fields=update_fields)

        tokens = get_jwt_tokens_for_user(user)
        UserDetailSerializer = app_settings.USER_DETAILS_SERIALIZER
        user_data = UserDetailSerializer(user).data

        if hasattr(request, "session"):
            login(getattr(request, "_request", request), user)

        return Response(
            {
                **tokens,
                "user": user_data,
                "created": created,
                "redirect_url": get_auth_redirect_url(request),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class GoogleLoginView(APIView):
    """
    API view for Google social authentication.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Authenticate or register a user using a Google OAuth2 ID token.

        API details:
        - POST ``/api/v1/auth/google/``
            - **200**: Google token verified; existing user authenticated.
            - **201**: Google token verified; new user created and authenticated.
            - **400**: Invalid or expired Google ID token.
            - **403**: Social authentication disabled by configuration.

        Side effects:
            - Validates ID token against Google's verification endpoint.
            - Creates user record and social auth link if first-time signin.

        Args:
            request (Request): DRF request with ``id_token``.

        Returns:
            Response: Auth tokens, user details, created flag, and redirect URL.

        Raises:
            PermissionDenied: If social login is disabled in application settings.
        """
        if not app_settings.ENABLE_SOCIAL_LOGIN:
            raise PermissionDenied(_("Social authentication is currently disabled."))

        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token_str = serializer.validated_data["id_token"]
        user, created = SocialAuthServiceFactory.authenticate_or_register(
            provider=SocialProviderChoices.GOOGLE, token_str=id_token_str
        )

        tokens = get_jwt_tokens_for_user(user)
        UserDetailSerializer = app_settings.USER_DETAILS_SERIALIZER
        user_data = UserDetailSerializer(user).data

        if hasattr(request, "session"):
            login(getattr(request, "_request", request), user)

        return Response(
            {
                **tokens,
                "user": user_data,
                "created": created,
                "redirect_url": get_auth_redirect_url(request),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AccountUnlockView(APIView):
    """
    API view to verify an account unlock token and reactivate the user account.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        Verify an account unlock token and clear lockout status.

        API details:
        - GET ``/api/v1/auth/unlock/?token={token}``
            - **200**: Account successfully unlocked.
            - **400**: Unlock token is invalid, expired, or already used.

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
