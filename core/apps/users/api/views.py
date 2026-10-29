"""
API endpoints for user authentication, registration, OTP lifecycle, and lockout recovery.

Implements zero-enumeration login, asynchronous OTP delivery via task queueing,
and JWT token distribution into client cookies.
"""

import datetime
import logging
import secrets
import typing

from rest_framework import permissions, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from core.apps.users import app_settings, get_user_model
from core.apps.users.api.serializers import (
    EmailOTPSignupSerializer,
    PasswordSignupSerializer,
    PhoneOTPSignupSerializer,
    SignupDocSerializer,
)
from core.apps.users.constants import OTPChannelChoices

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


class SignupView(viewsets.generics.CreateAPIView):
    """
    API view to register new user accounts.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = SignupDocSerializer

    def get_serializer_class(self):
        """ """
        channel = self.request.data.get("otp_channel")
        if not channel and app_settings.ENABLE_PASSWORD_LOGIN:
            return PasswordSignupSerializer

        elif (
            channel
            and app_settings.ENABLE_OTP_LOGIN
            and channel == OTPChannelChoices.EMAIL.value
        ):
            return EmailOTPSignupSerializer

        elif (
            channel
            and app_settings.ENABLE_OTP_LOGIN
            and channel == OTPChannelChoices.PHONE.value
        ):
            return PhoneOTPSignupSerializer

        raise NotFound()

    def create(self, request, *args, **kwargs):
        """
        Override create to send a jwt for currently created user instead
        """
        request_data = request.data.copy()
        otp_channel = request_data.pop("otp_channel", None)

        serializer = self.get_serializer(data=request_data, otp_channel=otp_channel)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(get_jwt_tokens_for_user(serializer.instance))
