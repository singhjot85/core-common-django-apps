import logging
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import get_user_model
from core.apps.users.api.serializers.base import (
    BaseOTPVerificationSerializer,
    BaseSignupSerializer,
)

User = get_user_model()
LOGGER = logging.getLogger(__name__)


class EmailOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """
    Serializer for signup via Email OTP verification.
    Requires first_name, email, and otp_code.
    """

    email = serializers.EmailField(required=True, allow_null=False)

    def validate_email(self, value: typing.Optional[str]) -> str:
        """
        Validate that email is provided and unique.
        """
        if not value:
            raise serializers.ValidationError({"email": _("Email is required field")})
        return super().validate_email(value)

    def validate(self, attrs: dict) -> dict:
        """
        Verify submitted OTP code against email.
        """
        is_valid, usr_msg = self.verify_otp(
            identifier=attrs.get("email"), code=attrs.get("otp_code")
        )
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        attrs["is_email_verified"] = True
        return attrs

    def create(self, validated_data: dict) -> "User":
        """
        Remove otp_code before persisting user.
        """
        validated_data.pop("otp_code", None)
        return super().create(validated_data)


class EmailOTPLoginSerializer(BaseOTPVerificationSerializer, serializers.Serializer):
    """
    Serializer for logging in existing users via Email OTP.
    Requires email and otp_code.
    """

    email = serializers.EmailField(required=True, allow_null=False)

    def validate_email(self, value: typing.Optional[str]) -> str:
        """
        Validate email syntax.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Email is required."))
        return value.strip().lower()

    def validate(self, attrs: dict) -> dict:
        """
        Verify OTP code and retrieve matching user.
        """
        email = attrs.get("email")
        code = attrs.get("otp_code")

        is_valid, usr_msg = self.verify_otp(identifier=email, code=code)
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        user: typing.Optional["User"] = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError(
                {"email": _("No user found with this email address.")}
            )

        if not user.is_active:
            raise serializers.ValidationError(_("This account is disabled."))

        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified", "modified"])

        attrs["user"] = user
        return attrs
