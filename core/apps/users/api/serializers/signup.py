import logging
import typing

import phonenumbers
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import app_settings, get_user_model
from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.apps.users.services.otp import OTPServiceFactory

User = get_user_model()

LOGGER = logging.getLogger(__name__)


class BaseSignupSerializer(serializers.Serializer):
    """ """

    first_name = serializers.CharField(
        max_length=150, required=True, allow_blank=False, default=""
    )
    last_name = serializers.CharField(
        max_length=150, required=False, allow_blank=False, default=""
    )
    username = serializers.CharField(
        max_length=150, required=False, allow_blank=False, default=""
    )
    email = serializers.EmailField(required=False, allow_null=True, default=None)
    phone_number = serializers.CharField(
        max_length=32, required=False, allow_null=True, default=None
    )

    def validate_username(self, value: str) -> str:
        """
        Validate the username and make sure, one doesn't exist in db.
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
        Validate the email and make sure, one doesn't exist in db.
        """
        if value and value.strip():
            clean_email = value.strip().lower()
            if User.objects.filter(email__iexact=clean_email).exists():
                raise serializers.ValidationError(
                    _("A user with this email address already exists.")
                )
            return clean_email

        return ""

    def validate_phone_number(
        self, value: typing.Optional[str]
    ) -> typing.Optional[str]:
        """
        Validate and format the phone_number
        """

        if value and value.strip():
            region = None
            if not value.startswith("+"):
                region = "IN"

            phone = phonenumbers.parse(value, region)
            if not phonenumbers.is_valid_number(phone):
                raise serializers.ValidationError(
                    {"phone_number": "Invalid phone number."}
                )

            if User.objects.filter(phone_number=value.strip()).exists():
                raise serializers.ValidationError(
                    {"phone_number": "Phone Number already exists."}
                )

        return value

    def create(self, validated_data):
        """
        Create a user instance, override to user create_user
        """
        return User.objects.create_user(**validated_data)


class PasswordSignupSerializer(BaseSignupSerializer):
    """ """

    _WEAK_PASSWORD = _(
        "Password is weak. Please create a alphanumeric password with atleast 8 digits."
    )

    username = serializers.CharField(max_length=150, required=True, allow_blank=False)

    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        style={"input_type": "password"},
    )

    def validate_password(self, value: str):
        """ """
        if not value or not value.strip():
            raise serializers.ValidationError(
                {"password": "Password is required field."}  # pragma: allowlist secret
            )

        if len(value) < 8 or value.isalpha() or value.isdigit():
            raise serializers.ValidationError({"password": self._WEAK_PASSWORD})

        return value


class BaseOTPVerificationSerializer:
    """ """

    _ACCOUNT_LOCKED_MSG = _(
        "This account has been locked due to too many failed attempts. Please contact support fot further assisstance."
    )
    _INCORRECT_OTP_MSG = _(
        "Either this OTP is incorrect or it has expired. Attempts left: {attempts}"
    )

    otp_code = serializers.CharField(
        max_length=app_settings.OTP_LENGTH, required=True, allow_null=False
    )

    def verify_otp(self, identifier: str, code: str):
        """ """
        is_valid = False

        if AuthLockoutService.is_locked(identifier):
            raise serializers.ValidationError(self._ACCOUNT_LOCKED_MSG)

        is_valid, otp_msg = OTPServiceFactory.verify_otp(
            identifier=identifier, code=code
        )

        usr_msg = ""
        remaining = None
        if not is_valid:
            LOGGER.warning(f"OTP login failed for {identifier}: {otp_msg}")
            remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
            usr_msg = self._INCORRECT_OTP_MSG.__format__(attempts=remaining)
            if is_locked:
                usr_msg = self._ACCOUNT_LOCKED_MSG

        return is_valid, usr_msg


class EmailOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """ """

    email = serializers.EmailField(required=True, allow_null=False)

    def validate_email(self, value):
        """ """
        if not value:
            raise serializers.ValidationError({"email": "Email is required field"})

        return super().validate_email(value)

    def validate(self, attrs):
        """ """
        is_valid, usr_msg = self.verify_otp(
            identifier=attrs.get("email"), code=attrs.get("otp_code")
        )
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        return super().validate(attrs)


class PhoneOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """ """

    phone_number = serializers.CharField(
        max_length=32, required=True, allow_null=False, default=None
    )

    def validate_phone_number(self, value):
        """ """
        if not value:
            raise serializers.ValidationError(
                {"phone_number": "Phone Number is required field"}
            )

        return super().validate_phone_number(value)

    def validate(self, attrs):
        """ """
        is_valid, usr_msg = self.verify_otp(
            identifier=attrs.get("phone_number"), code=attrs.get("otp_code")
        )
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        return super().validate(attrs)


class SignupDocSerializer(BaseSignupSerializer, BaseOTPVerificationSerializer):
    """
    Serializer for documentation.
    """

    otp_channel = serializers.ChoiceField(
        choices=OTPChannelChoices, required=False, allow_null=True, default=None
    )
