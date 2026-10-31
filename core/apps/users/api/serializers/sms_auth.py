import logging
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import get_user_model
from core.apps.users.api.serializers.base import (
    BaseOTPVerificationSerializer,
    BaseSignupSerializer,
    validate_clean_phone_number,
)

User = get_user_model()
LOGGER = logging.getLogger(__name__)


class PhoneOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """
    Serializer for signup via Phone/SMS OTP verification.
    Requires first_name, phone_number, and otp_code.
    """

    phone_number = serializers.CharField(max_length=32, required=True, allow_null=False)

    def validate_phone_number(self, value: typing.Optional[str]) -> str:
        """
        Validate that phone number is provided, valid, and unique.
        """
        if not value:
            raise serializers.ValidationError(
                {"phone_number": _("Phone Number is required field")}
            )
        return super().validate_phone_number(value)

    def validate(self, attrs: dict) -> dict:
        """
        Verify submitted OTP code against phone number.
        """
        is_valid, usr_msg = self.verify_otp(
            identifier=attrs.get("phone_number"), code=attrs.get("otp_code")
        )
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        attrs["is_phone_verified"] = True
        return attrs

    def create(self, validated_data: dict) -> "User":
        """
        Remove otp_code before persisting user.
        """
        validated_data.pop("otp_code", None)
        return super().create(validated_data)


class PhoneOTPLoginSerializer(BaseOTPVerificationSerializer, serializers.Serializer):
    """
    Serializer for logging in existing users via Phone/SMS OTP.
    Requires phone_number and otp_code.
    """

    phone_number = serializers.CharField(max_length=32, required=True, allow_null=False)

    def validate_phone_number(self, value: typing.Optional[str]) -> str:
        """
        Validate phone number format.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Phone number is required."))

        return validate_clean_phone_number(value)

    def validate(self, attrs: dict) -> dict:
        """
        Verify OTP code and retrieve matching user.
        """
        phone_number = attrs.get("phone_number")
        code = attrs.get("otp_code")

        is_valid, usr_msg = self.verify_otp(identifier=phone_number, code=code)
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        user: typing.Optional["User"] = User.objects.filter(
            phone_number=phone_number
        ).first()
        if not user:
            raise serializers.ValidationError(
                {"phone_number": _("No user found with this phone number.")}
            )

        if not user.is_active:
            raise serializers.ValidationError(_("This account is disabled."))

        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified", "modified"])

        attrs["user"] = user
        return attrs
