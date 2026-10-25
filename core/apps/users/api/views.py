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
    Asynchronous OTP dispatch view.
    Validates identifier syntax and immediately returns HTTP 202 Accepted,
    queuing actual dispatch to background worker without leaking user existence.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Dispatch an OTP verification code to the given identifier asynchronously.

        Always returns 202 Accepted to prevent user enumeration regardless of
        whether the identifier exists in the database.

        API details:
        - POST ``/api/v1/auth/otp/send/``
            - **202**: Request accepted and dispatched to background queue.
            - **400**: Invalid identifier syntax or channel parameters.
            - **403**: OTP authentication is disabled by configuration.

        Side effects:
            - Queues ``send_otp_task`` Celery job for asynchronous code generation and delivery.

        Args:
            request (Request): DRF request containing ``identifier``, ``channel``, and ``purpose``.

        Returns:
            Response: HTTP 202 status with generic confirmation message.

        Raises:
            PermissionDenied: If OTP login is disabled in application settings.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = OTPSendSerializer(data=request.data)
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
    API view for verifying OTP codes and authenticating/provisioning users with zero enumeration.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Verify submitted OTP code and authenticate or provision the user.

        API details:
        - POST ``/api/v1/auth/otp/verify/``
            - **200**: OTP verified; existing user authenticated.
            - **201**: OTP verified; new user provisioned and authenticated.
            - **400**: Invalid OTP, expired OTP, or auto-registration disabled.
            - **403**: OTP authentication disabled by configuration.
            - **423**: Identity temporarily locked due to excessive failed verification attempts.

        Side effects:
            - Increments failed verification counter in cache on incorrect code.
            - Resets failed attempt counter on successful verification.
            - May create a new user record if auto-registration is enabled.
            - Updates ``is_phone_verified`` or ``is_email_verified`` flags on user.

        Args:
            request (Request): DRF request containing ``identifier``, ``code``, and ``channel``.

        Returns:
            Response: Auth tokens, user profile, created flag, and redirect URL.

        Raises:
            PermissionDenied: If OTP login is disabled in application settings.
        """
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = OTPVerifySerializer(data=request.data)
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
                if serializer.validated_data.get("email"):
                    create_kwargs["email"] = serializer.validated_data["email"].lower()
            elif channel == OTPChannelChoices.EMAIL:
                create_kwargs["email"] = identifier.lower()
                create_kwargs["is_email_verified"] = True

            if serializer.validated_data.get("first_name"):
                create_kwargs["first_name"] = serializer.validated_data["first_name"]
            if serializer.validated_data.get("last_name"):
                create_kwargs["last_name"] = serializer.validated_data["last_name"]

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
