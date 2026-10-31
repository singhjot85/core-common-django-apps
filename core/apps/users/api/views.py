"""
API viewsets and utility views for user authentication, registration,
OTP lifecycle, and lockout recovery.

Organized into modular viewsets:
- PasswordAuthViewSet: login and signup using username and password.
- EmailOTPAuthViewSet: login and signup using email and OTP code.
- SMSOTPAuthViewSet: login and signup using phone number and OTP code.
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
from core.apps.users.api.serializer import (
    GoogleLoginSerializer,
    OTPSendSerializer,
)
from core.apps.users.api.serializers import (
    EmailOTPLoginSerializer,
    EmailOTPSignupSerializer,
    PasswordLoginSerializer,
    PasswordSignupSerializer,
    PhoneOTPLoginSerializer,
    PhoneOTPSignupSerializer,
)
from core.apps.users.constants import SocialProviderChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
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
    request, user: "AbstractUser", status_code=status.HTTP_200_OK
) -> Response:
    """
    Helper to establish session login, generate JWT tokens, serialize user details,
    and return a standardized authentication Response.
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
    Endpoints:
    - POST auth/password/login/
    - POST auth/password/signup/
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "signup":
            return PasswordSignupSerializer
        return PasswordLoginSerializer

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request, *args, **kwargs):
        """
        Authenticate user with username and password.
        Enforces account lockout checks.
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
    ViewSet handling Email OTP-based login and signup.
    Endpoints:
    - POST auth/otp/email-login/
    - POST auth/otp/email-signup/
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "signup":
            return EmailOTPSignupSerializer
        return EmailOTPLoginSerializer

    @action(detail=False, methods=["post"], url_path="email-login")
    def login(self, request, *args, **kwargs):
        """
        Verify Email OTP and authenticate user.
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

    @action(detail=False, methods=["post"], url_path="email-signup")
    def signup(self, request, *args, **kwargs):
        """
        Verify Email OTP and register a new user account.
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
    ViewSet handling SMS/Phone OTP-based login and signup.
    Endpoints:
    - POST auth/otp/phone-login/
    - POST auth/otp/phone-signup/
    """

    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "signup":
            return PhoneOTPSignupSerializer
        return PhoneOTPLoginSerializer

    @action(detail=False, methods=["post"], url_path="phone-login")
    def login(self, request, *args, **kwargs):
        """
        Verify Phone OTP and authenticate user.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        phone_number = request.data.get("phone_number", "").strip()
        if AuthLockoutService.is_locked(phone_number):
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
        AuthLockoutService.clear_attempts(phone_number)
        return _build_auth_response(request, user, status_code=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="phone-signup")
    def signup(self, request, *args, **kwargs):
        """
        Verify Phone OTP and register a new user account.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        phone_number = serializer.validated_data.get("phone_number")
        if phone_number:
            AuthLockoutService.clear_attempts(phone_number)
        return _build_auth_response(request, user, status_code=status.HTTP_201_CREATED)


# ============================================================================
# Auxiliary Auth Endpoints: OTP Dispatch, Social Auth, Account Unlock
# ============================================================================


class OTPSendView(APIView):
    """
    Dispatch one-time passcodes (OTP) via SMS or Email asynchronously.
    """

    permission_classes = [AllowAny]
    serializer_class = OTPSendSerializer

    def post(self, request, *args, **kwargs):
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        channel = serializer.validated_data["channel"]
        purpose = serializer.validated_data["purpose"]

        try:
            queue_task(
                task=send_otp_task,
                task_kwargs={
                    "identifier": identifier,
                    "channel": channel,
                    "purpose": purpose,
                },
                on_commit=True,
            )
        except Exception as e:
            LOGGER.error(f"Failed to queue OTP task for {identifier}: {e}")

        return Response(
            {"detail": _("If the account exists, an OTP has been dispatched.")},
            status=status.HTTP_202_ACCEPTED,
        )


class GoogleLoginView(APIView):
    """
    API view for Google social authentication.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
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
    API view to verify an account unlock token and reactivate the user account.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
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
