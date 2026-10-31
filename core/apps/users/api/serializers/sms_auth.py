"""
Serializers for SMS and phone-based OTP authentication, registration, and dispatch workflows.

Provides:
- PhoneOTPSendSerializer: Validates phone number for requesting an OTP code.
- PhoneOTPSignupSerializer: Provisions new users after verifying phone OTP code.
- PhoneOTPLoginSerializer: Authenticates existing users upon phone OTP verification.
"""

import logging

from django.utils.translation import gettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from core.apps.users import get_user_model
from core.apps.users.api.serializers.base import (
    BaseOTPVerificationSerializer,
    BaseSignupSerializer,
    SendOTPMixin,
)
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices

User = get_user_model()
LOGGER = logging.getLogger(__name__)


class PhoneOTPSendSerializer(serializers.Serializer, SendOTPMixin):
    """
    Validate parameters for requesting an OTP code dispatched to a phone number.

    Fields:
    - ``phone_number`` (CharField): Destination phone number (minimum 7 digits).
    - ``purpose`` (ChoiceField): Purpose of the OTP (login, signup, etc.). Defaults to ``"login"``.
    """

    phone_number = PhoneNumberField(required=True, allow_null=False)
    purpose = serializers.ChoiceField(
        choices=OTPPurposeChoices.choices,
        default=OTPPurposeChoices.LOGIN,
    )

    def send(self) -> bool:
        """
        Dispatch OTP code to the validated phone number.

        Returns:
            bool: True if task was successfully queued, False otherwise.
        """
        phone_obj = self.validated_data["phone_number"]
        e164_phone = (
            phone_obj.as_e164 if hasattr(phone_obj, "as_e164") else str(phone_obj)
        )
        return self.send_otp(
            identifier=e164_phone,
            channel=OTPChannelChoices.PHONE,
            purpose=self.validated_data["purpose"],
        )


class PhoneOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """
    Validate and provision a new user via verified Phone OTP passcode.

    Requires ``first_name``, ``phone_number``, and ``otp_code``.
    Marks the created user's ``is_phone_verified`` flag as True upon creation.

    Validation rules:
    - ``phone_number`` is required, must contain at least 7 digits, and must not exist in database.
    - ``otp_code`` must match the active code issued to the phone number.
    """

    phone_number = PhoneNumberField(required=True, allow_null=False)

    def validate(self, attrs: dict) -> dict:
        """
        Verify the submitted OTP code against the recipient phone number.

        Args:
            attrs (dict): Deserialized attributes including ``phone_number`` and ``otp_code``.

        Returns:
            dict: Validated attributes dictionary with ``is_phone_verified=True``.

        Raises:
            ValidationError: If OTP verification fails or the phone identity is locked.
        """
        phone_obj = attrs.get("phone_number")
        e164_phone = (
            phone_obj.as_e164 if hasattr(phone_obj, "as_e164") else str(phone_obj)
        )
        is_valid, usr_msg = self.verify_otp(
            identifier=e164_phone,
            code=attrs.get("otp_code"),
        )
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        attrs["is_phone_verified"] = True
        return attrs

    def create(self, validated_data: dict) -> "User":
        """
        Create and persist the verified user record.

        Pops the transient ``otp_code`` field before calling ``create_user``.

        Side effects:
        - Writes a new user row with ``is_phone_verified=True`` to the database.

        Args:
            validated_data (dict): Sanitized validated attributes.

        Returns:
            User: Newly provisioned user instance.
        """
        validated_data.pop("otp_code", None)
        return super().create(validated_data)


class PhoneOTPLoginSerializer(BaseOTPVerificationSerializer):
    """
    Authenticate an existing active user via verified Phone OTP passcode.

    Requires an existing registered ``phone_number`` and matching ``otp_code``.
    Updates ``is_phone_verified`` on the user record if not already marked.

    Validation rules:
    - ``phone_number`` is required and must belong to an existing active account.
    - ``otp_code`` must match the active code stored in cache.
    """

    phone_number = PhoneNumberField(required=True, allow_null=False)

    def validate(self, attrs: dict) -> dict:
        """
        Verify OTP code and authenticate the matching existing user.

        Side effects:
        - Updates ``is_phone_verified=True`` on the user model if previously False.

        Args:
            attrs (dict): Dictionary with ``phone_number`` and ``otp_code``.

        Returns:
            dict: Attribute dictionary with authenticated ``attrs['user']``.

        Raises:
            ValidationError:
            - OTP code is invalid, expired, or locked out.
            - No user account exists with the provided phone number.
            - User account is deactivated (``is_active=False``).
        """
        phone_number = attrs.get("phone_number")
        code = attrs.get("otp_code")
        e164_phone = (
            phone_number.as_e164
            if hasattr(phone_number, "as_e164")
            else str(phone_number)
        )

        is_valid, usr_msg = self.verify_otp(identifier=e164_phone, code=code)
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        user = User.objects.filter(phone_number=phone_number).first()
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
