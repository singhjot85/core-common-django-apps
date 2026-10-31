import logging
import re
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import app_settings, get_user_model
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.apps.users.services.otp import OTPServiceFactory

User = get_user_model()
LOGGER = logging.getLogger(__name__)


def validate_clean_phone_number(value: str) -> str:
    """
    Validate that phone number contains at least 7 digits.
    Optionally preserves leading '+' for international format.
    """
    clean_val = value.strip()
    digits = re.sub(r"\D", "", clean_val)
    if len(digits) < 7:
        raise serializers.ValidationError(_("Invalid phone number format."))
    return clean_val


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for authenticated user details.
    """

    full_name = serializers.CharField(read_only=True)
    has_password = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "full_name",
            "is_phone_verified",
            "is_email_verified",
            "has_password",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "is_phone_verified",
            "is_email_verified",
            "has_password",
            "created",
            "modified",
        ]


class BaseSignupSerializer(serializers.Serializer):
    """
    Base serializer for user signup providing common field declarations,
    uniqueness checks, phone normalization, and user creation logic.
    """

    first_name = serializers.CharField(max_length=150, required=True, allow_blank=False)
    last_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    username = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    email = serializers.EmailField(required=False, allow_null=True, default=None)
    phone_number = serializers.CharField(
        max_length=32, required=False, allow_null=True, default=None
    )

    def validate_username(self, value: str) -> str:
        """
        Validate the username and ensure it is unique in the database.
        """
        if value and value.strip():
            if User.objects.filter(username__iexact=value.strip()).exists():
                raise serializers.ValidationError(
                    _("A user with this username already exists.")
                )
            return value.strip()
        return ""

    def validate_email(self, value: typing.Optional[str]) -> typing.Optional[str]:
        """
        Validate the email and ensure it is unique in the database.
        """
        if value and value.strip():
            clean_email = value.strip().lower()
            if User.objects.filter(email__iexact=clean_email).exists():
                raise serializers.ValidationError(
                    _("A user with this email address already exists.")
                )
            return clean_email
        return None

    def validate_phone_number(
        self, value: typing.Optional[str]
    ) -> typing.Optional[str]:
        """
        Validate and check uniqueness of the phone number.
        """
        if value and value.strip():
            clean_phone = validate_clean_phone_number(value)
            if User.objects.filter(phone_number=clean_phone).exists():
                raise serializers.ValidationError(
                    {"phone_number": _("Phone Number already exists.")}
                )
            return clean_phone
        return None

    def create(self, validated_data: dict) -> "User":
        """
        Create a user instance via User.objects.create_user.
        """
        return User.objects.create_user(**validated_data)


class BaseOTPVerificationSerializer:
    """
    Mixin serializer providing OTP validation and lockout handling for auth workflows.
    """

    _ACCOUNT_LOCKED_MSG = _(
        "This account has been locked due to too many failed attempts. Please contact support for further assistance."
    )
    _INCORRECT_OTP_MSG = _(
        "Either this OTP is incorrect or it has expired. Attempts left: {attempts}"
    )

    otp_code = serializers.CharField(
        max_length=app_settings.OTP_LENGTH, required=True, allow_null=False
    )

    def verify_otp(self, identifier: str, code: str) -> tuple[bool, str]:
        """
        Validate submitted OTP code against cache and check lockout status.
        """
        if AuthLockoutService.is_locked(identifier):
            raise serializers.ValidationError(self._ACCOUNT_LOCKED_MSG)

        is_valid, otp_msg = OTPServiceFactory.verify_otp(
            identifier=identifier, code=code
        )

        usr_msg = ""
        if not is_valid:
            LOGGER.warning(f"OTP verification failed for {identifier}: {otp_msg}")
            remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
            usr_msg = self._INCORRECT_OTP_MSG.format(attempts=remaining)
            if is_locked:
                usr_msg = self._ACCOUNT_LOCKED_MSG

        return is_valid, usr_msg
