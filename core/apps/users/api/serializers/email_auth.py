"""
Serializers for email OTP authentication, registration, and dispatch workflows.

Provides:
- EmailOTPSendSerializer: Validates email destination for requesting an OTP code.
- EmailOTPSignupSerializer: Provisions new users after verifying email OTP code.
- EmailOTPLoginSerializer: Authenticates existing users upon email OTP verification.
"""

import logging
import typing

from django.utils.translation import gettext_lazy as _
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


class EmailOTPSendSerializer(serializers.Serializer, SendOTPMixin):
    """
    Validate parameters for requesting an OTP code dispatched to an email address.

    Fields:
    - ``email`` (EmailField): Target recipient email address.
    - ``purpose`` (ChoiceField): Purpose of the OTP (login, signup, etc.). Defaults to ``"login"``.
    """

    email = serializers.EmailField(required=True, allow_null=False)
    purpose = serializers.ChoiceField(
        choices=OTPPurposeChoices.choices,
        default=OTPPurposeChoices.LOGIN,
    )

    def validate_email(self, value: typing.Optional[str]) -> str:
        """
        Validate and normalize email address.

        Args:
            value (str, optional): Raw email address.

        Returns:
            str: Trimmed, lowercased email string.

        Raises:
            ValidationError: If email is blank or missing.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Email is required."))
        return value.strip().lower()

    def send(self) -> bool:
        """
        Dispatch OTP code to the validated email address.

        Returns:
            bool: True if task was successfully queued, False otherwise.
        """
        return self.send_otp(
            identifier=self.validated_data["email"],
            channel=OTPChannelChoices.EMAIL,
            purpose=self.validated_data["purpose"],
        )


class EmailOTPSignupSerializer(BaseOTPVerificationSerializer, BaseSignupSerializer):
    """
    Validate and provision a new user via verified Email OTP passcode.

    Requires ``first_name``, ``email``, and ``otp_code``.
    Marks the created user's ``is_email_verified`` flag as True upon creation.

    Validation rules:
    - ``email`` is required, valid syntax, and must not exist in database.
    - ``otp_code`` must match the active code issued to the email address.
    """

    email = serializers.EmailField(required=True, allow_null=False)

    def validate_email(self, value: typing.Optional[str]) -> str:
        """
        Validate that email is provided, valid syntax, and not already registered.

        Args:
            value (str, optional): Raw email string.

        Returns:
            str: Normalized lowercased email address.

        Raises:
            ValidationError:
            - Email is empty or omitted.
            - Email already exists in the database.
        """
        if not value:
            raise serializers.ValidationError({"email": _("Email is required field")})
        return super().validate_email(value)

    def validate(self, attrs: dict) -> dict:
        """
        Verify the submitted OTP code against the recipient email address.

        Args:
            attrs (dict): Deserialized attributes including ``email`` and ``otp_code``.

        Returns:
            dict: Validated attributes dictionary with ``is_email_verified=True``.

        Raises:
            ValidationError: If OTP verification fails or the email identity is locked.
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
        Create and persist the verified user record.

        Pops the transient ``otp_code`` field before calling ``create_user``.

        Side effects:
        - Writes a new user row with ``is_email_verified=True`` to the database.

        Args:
            validated_data (dict): Sanitized validated attributes.

        Returns:
            User: Newly provisioned user instance.
        """
        validated_data.pop("otp_code", None)
        return super().create(validated_data)


class EmailOTPLoginSerializer(BaseOTPVerificationSerializer):
    """
    Authenticate an existing active user via verified Email OTP passcode.

    Requires an existing registered ``email`` and matching ``otp_code``.
    Updates ``is_email_verified`` on the user record if not already marked.

    Validation rules:
    - ``email`` is required and must belong to an existing active account.
    - ``otp_code`` must match the active code stored in cache.
    """

    email = serializers.EmailField(required=True, allow_null=False)

    def validate_email(self, value: typing.Optional[str]) -> str:
        """
        Validate that the email string is not empty.

        Args:
            value (str, optional): Raw email address.

        Returns:
            str: Trimmed, lowercased email string.

        Raises:
            ValidationError: If email is blank or missing.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(_("Email is required."))
        return value.strip().lower()

    def validate(self, attrs: dict) -> dict:
        """
        Verify OTP code and authenticate the matching existing user.

        Side effects:
        - Updates ``is_email_verified=True`` on the user model if previously False.

        Args:
            attrs (dict): Dictionary with ``email`` and ``otp_code``.

        Returns:
            dict: Attribute dictionary with authenticated ``attrs['user']``.

        Raises:
            ValidationError:
            - OTP code is invalid, expired, or locked out.
            - No user account exists with the provided email.
            - User account is deactivated (``is_active=False``).
        """
        email = attrs.get("email")
        code = attrs.get("otp_code")

        is_valid, usr_msg = self.verify_otp(identifier=email, code=code)
        if not is_valid:
            raise serializers.ValidationError({"otp_code": usr_msg})

        user = User.objects.filter(email__iexact=email).first()
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
