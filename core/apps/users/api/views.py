import logging
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users import app_settings, get_user_model
from core.apps.users.api.serializers import (
    GoogleLoginSerializer,
    LoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
)
from core.apps.users.constants import OTPChannelChoices, SocialProviderChoices
from core.apps.users.services.otp import OTPServiceFactory
from core.apps.users.services.social import SocialAuthServiceFactory
from core.utils.tasks import queue_task

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

LOGGER = logging.getLogger(__name__)
User = get_user_model()


def get_jwt_tokens_for_user(user: "AbstractUser") -> dict:
    """Helper to generate SimpleJWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class SignupView(APIView):
    """
    API view to register new user accounts.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer_class = app_settings.SIGNUP_SERIALIZER
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        tokens = get_jwt_tokens_for_user(user)
        user_serializer_class = app_settings.USER_DETAILS_SERIALIZER
        user_data = user_serializer_class(user).data

        return Response(
            {
                **tokens,
                "user": user_data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    API view for username/password login.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not app_settings.ENABLE_PASSWORD_LOGIN:
            raise PermissionDenied(
                _("Password-based authentication is currently disabled.")
            )

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        tokens = get_jwt_tokens_for_user(user)
        user_serializer_class = app_settings.USER_DETAILS_SERIALIZER
        user_data = user_serializer_class(user).data

        return Response(
            {
                **tokens,
                "user": user_data,
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
                task="core.apps.users.tasks.send_otp_task",
                task_kwargs={
                    "identifier": identifier,
                    "channel": channel,
                    "purpose": purpose,
                },
                on_commit=False,
            )
        except Exception as e:
            LOGGER.error(f"Failed to queue OTP task for {identifier}: {e}")

        return Response(
            {"detail": _("If the account exists, an OTP has been dispatched.")},
            status=status.HTTP_202_ACCEPTED,
        )


class OTPVerifyView(APIView):
    """
    API view for verifying OTP codes and authenticating/provisioning users.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        if not app_settings.ENABLE_OTP_LOGIN:
            raise PermissionDenied(_("OTP authentication is currently disabled."))

        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]
        channel = serializer.validated_data["channel"]

        is_valid, msg = OTPServiceFactory.verify_otp(identifier=identifier, code=code)
        if not is_valid:
            raise ValidationError({"code": msg})

        user = None

        if channel == OTPChannelChoices.PHONE:
            user = User.objects.filter(phone_number=identifier).first()
        elif channel == OTPChannelChoices.EMAIL:
            user = User.objects.filter(email__iexact=identifier).first()

        created = False
        if not user:
            if not app_settings.ALLOW_AUTO_REGISTRATION_ON_OTP:
                return Response(
                    {"detail": _("Account not found. Please register first.")},
                    status=status.HTTP_404_NOT_FOUND,
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
        user_serializer_class = app_settings.USER_DETAILS_SERIALIZER
        user_data = user_serializer_class(user).data

        return Response(
            {
                **tokens,
                "user": user_data,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
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

        tokens = get_jwt_tokens_for_user(user)
        user_serializer_class = app_settings.USER_DETAILS_SERIALIZER
        user_data = user_serializer_class(user).data

        return Response(
            {
                **tokens,
                "user": user_data,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
