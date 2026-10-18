import re
import typing

from django.contrib.auth import authenticate
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import get_user_model
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

User = get_user_model()


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


class SignupSerializer(serializers.Serializer):
    """
    Serializer for creating new user accounts.
    Captures basic info; username, password, email, and phone are all optional
    (with at least one contact/username identifier required).
    """

    first_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    last_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    username = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
        style={"input_type": "password"},
    )
    email = serializers.EmailField(required=False, allow_null=True, default=None)
    phone_number = serializers.CharField(
        max_length=32, required=False, allow_null=True, default=None
    )

    def validate_username(self, value: str) -> str:
        if value and value.strip():
            if User.objects.filter(username__iexact=value.strip()).exists():
                raise serializers.ValidationError(
                    _("A user with this username already exists.")
                )
            return value.strip()
        return ""

    def validate_email(self, value: typing.Optional[str]) -> typing.Optional[str]:
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
        if value and value.strip():
            clean_phone = value.strip()
            digits = re.sub(r"\D", "", clean_phone)
            if len(digits) < 7:
                raise serializers.ValidationError(_("Invalid phone number format."))
            if User.objects.filter(phone_number=clean_phone).exists():
                raise serializers.ValidationError(
                    _("A user with this phone number already exists.")
                )
            return clean_phone
        return None

    def validate(self, attrs: dict) -> dict:
        username = attrs.get("username", "")
        email = attrs.get("email")
        phone_number = attrs.get("phone_number")

        if not username and not email and not phone_number:
            raise serializers.ValidationError(
                _(
                    "At least one contact identifier (email or phone) or username must be provided."
                )
            )
        return attrs

    def create(self, validated_data: dict) -> "AbstractUser":
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for username and password login.
    Checks that the user possesses a usable password.
    """

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    def validate(self, attrs: dict) -> dict:
        username = attrs.get("username", "").strip()
        password = attrs.get("password", "")

        # Check if login identifier is email or phone number
        user = None
        if "@" in username:
            user = User.objects.filter(email__iexact=username).first()
        elif re.sub(r"\D", "", username) and len(re.sub(r"\D", "", username)) >= 7:
            user = User.objects.filter(phone_number=username).first()

        actual_username = user.username if user else username

        user = authenticate(username=actual_username, password=password)

        if not user:
            # Check if user exists but has no usable password
            target_user = (
                user
                or User.objects.filter(username__iexact=actual_username).first()
                or (
                    User.objects.filter(email__iexact=username).first()
                    if "@" in username
                    else None
                )
            )
            if target_user and not target_user.has_usable_password():
                raise serializers.ValidationError(
                    _(
                        "This account does not have a password configured. Please log in with a different method."
                    )
                )
            raise serializers.ValidationError(
                _("Unable to log in with provided credentials.")
            )

        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled."))

        attrs["user"] = user
        return attrs


class OTPSendSerializer(serializers.Serializer):
    """
    Serializer for requesting an OTP code via phone SMS or Email.
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
            except Exception:
                raise serializers.ValidationError(
                    {"identifier": _("Invalid email address format.")}
                )

        attrs["identifier"] = identifier
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying an OTP code.
    """

    identifier = serializers.CharField(required=True)
    code = serializers.CharField(max_length=10, required=True)
    channel = serializers.ChoiceField(
        choices=OTPChannelChoices.choices,
        default=OTPChannelChoices.PHONE,
    )

    def validate(self, attrs: dict) -> dict:
        attrs["identifier"] = attrs.get("identifier", "").strip()
        attrs["code"] = attrs.get("code", "").strip()
        return attrs


class GoogleLoginSerializer(serializers.Serializer):
    """
    Serializer for authenticating via Google ID Token.
    """

    id_token = serializers.CharField(required=True, write_only=True)
