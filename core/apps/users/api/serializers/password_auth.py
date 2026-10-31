import logging
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import get_user_model
from core.apps.users.api.serializers.base import BaseSignupSerializer

User = get_user_model()
LOGGER = logging.getLogger(__name__)


class PasswordSignupSerializer(BaseSignupSerializer):
    """
    Serializer for password-based signup.
    Requires first_name, username, and password.
    """

    _WEAK_PASSWORD = _(
        "Password is weak. Please create an alphanumeric password with at least 8 digits."
    )

    username = serializers.CharField(max_length=150, required=True, allow_blank=False)
    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        style={"input_type": "password"},
    )

    def validate_password(self, value: str) -> str:
        """
        Validate password requirements: non-empty, min 8 chars, alphanumeric.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                {
                    "password": _("Password is required field.")
                }  # pragma: allowlist secret
            )

        trimmed = value.strip()
        if len(trimmed) < 8 or trimmed.isalpha() or trimmed.isdigit():
            raise serializers.ValidationError({"password": self._WEAK_PASSWORD})

        return trimmed


class PasswordLoginSerializer(serializers.Serializer):
    """
    Serializer for username/password login.
    Authenticates active users without leaking account enumeration details.
    """

    USER_NOT_FOUND_ERROR = _("Username or password combination is incorrect.")

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    def validate_username(self, value: str) -> str:
        """
        Validate username is non-empty.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Username is required."))
        return value

    def validate_password(self, value: str) -> str:
        """
        Validate password is non-empty.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Password is required."))
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Authenticate credentials and verify the user account status.
        """
        username = attrs.get("username")
        password = attrs.get("password")

        user: typing.Optional["User"] = None
        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            LOGGER.debug(f"User not found for username: {username}")

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError(_("This account is disabled."))
            attrs["user"] = user
            return attrs

        raise serializers.ValidationError(self.USER_NOT_FOUND_ERROR)
