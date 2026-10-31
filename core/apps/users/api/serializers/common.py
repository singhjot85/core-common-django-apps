"""
Serializers for OTP dispatch, verification, and third-party social authentication.

Provides:
- OTPSendSerializer: Validates parameters for requesting OTP generation and dispatch.
- OTPVerifySerializer: Validates parameters for manual OTP code verification.
- GoogleLoginSerializer: Validates incoming Google OAuth2 ID tokens.
"""

import re

from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices


class OTPSendSerializer(serializers.Serializer):
    """
    Validate parameters for requesting an OTP code via SMS or Email.

    Fields:
    - ``identifier`` (CharField): Phone number (minimum 7 digits) or valid email address.
    - ``channel`` (ChoiceField): Delivery channel, either ``"phone"`` or ``"email"``. Defaults to ``"phone"``.
    - ``purpose`` (ChoiceField): Purpose of the OTP (``"login"``, ``"signup"``, ``"verification"``, ``"reset_password"``). Defaults to ``"login"``.
    """

    identifier = serializers.CharField(required=True)
    channel = serializers.ChoiceField(
        choices=OTPChannelChoices.choices,
        default=OTPChannelChoices.PHONE,
    )
    purpose = serializers.ChoiceField(
        choices=OTPPurposeChoices.choices,
        default=OTPPurposeChoices.LOGIN,
    )

    def validate(self, attrs: dict) -> dict:
        """
        Validate that the identifier conforms to the format expected for the chosen channel.

        Args:
            attrs (dict): Input dictionary containing identifier, channel, and purpose.

        Returns:
            dict: Validated dictionary with trimmed identifier.

        Raises:
            ValidationError: If phone number has fewer than 7 digits or email is malformed.
        """
        identifier = attrs.get("identifier", "").strip()
        channel = attrs.get("channel")

        if channel == OTPChannelChoices.PHONE:
            digits = re.sub(r"\D", "", identifier)
            if len(digits) < 7:
                raise serializers.ValidationError(
                    {"identifier": _("Invalid phone number format.")}
                )
        elif channel == OTPChannelChoices.EMAIL:
            validator = EmailValidator()
            try:
                validator(identifier)
            except Exception as e:
                raise serializers.ValidationError(
                    {"identifier": _("Invalid email address format.")}
                ) from e

        attrs["identifier"] = identifier
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    """
    Validate parameters for verifying a submitted OTP code.

    Fields:
    - ``identifier`` (CharField): Phone number or email address that received the OTP.
    - ``code`` (CharField): One-time verification passcode (max length 10).
    - ``channel`` (ChoiceField): Delivery channel, either ``"phone"`` or ``"email"``. Defaults to ``"phone"``.
    """

    identifier = serializers.CharField(required=True)
    code = serializers.CharField(max_length=10, required=True)
    channel = serializers.ChoiceField(
        choices=OTPChannelChoices.choices,
        default=OTPChannelChoices.PHONE,
    )

    def validate(self, attrs: dict) -> dict:
        """
        Trim whitespace from identifier and passcode.

        Args:
            attrs (dict): Deserialized attributes.

        Returns:
            dict: Sanitized attributes dictionary.
        """
        attrs["identifier"] = attrs.get("identifier", "").strip()
        attrs["code"] = attrs.get("code", "").strip()
        return attrs


class GoogleLoginSerializer(serializers.Serializer):
    """
    Serializer for authenticating via Google OAuth2 ID token.

    Fields:
    - ``id_token`` (CharField, write-only): Google OpenID Connect token issued by Google Identity.
    """

    id_token = serializers.CharField(required=True, write_only=True)
