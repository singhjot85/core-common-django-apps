"""
Serializers for username and password authentication and registration.

Provides:
- PasswordSignupSerializer: Validates credentials and provisions users via password.
- PasswordLoginSerializer: Authenticates existing users via username and password.
"""

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
    Validate registration details and create users using password authentication.

    Requires an explicit username, first name, and a password meeting minimum complexity rules.

    Validation rules:
    - ``username`` is required, non-blank, and unique.
    - ``password`` is required, at least 8 characters long, and must be alphanumeric
      (cannot be purely numeric or purely alphabetic).
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
        Validate password complexity and length requirements.

        Enforces that the password is non-empty, contains at least 8 characters,
        and includes a mix of characters and digits.

        Args:
            value (str): Raw password string.

        Returns:
            str: Trimmed password string.

        Raises:
            ValidationError:
            - Password is missing or blank.
            - Password is shorter than 8 characters.
            - Password is purely alphabetic or purely numeric.
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
    Validate username and password credentials for existing users.

    Authenticates user credentials using constant-time password comparison.
    Preserves zero-enumeration security by returning a generic error message
    whether the user does not exist or provided the wrong password.

    Validation rules:
    - Both ``username`` and ``password`` are required and non-empty.
    - User account must be active (``is_active=True``).
    """

    USER_NOT_FOUND_ERROR = _("Username or password combination is incorrect.")

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    def validate_username(self, value: str) -> str:
        """
        Validate that the submitted username is not blank.

        Args:
            value (str): Raw username string.

        Returns:
            str: Trimmed username string.

        Raises:
            ValidationError: If the username is blank.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Username is required."))
        return value

    def validate_password(self, value: str) -> str:
        """
        Validate that the submitted password is not blank.

        Args:
            value (str): Raw password string.

        Returns:
            str: Trimmed password string.

        Raises:
            ValidationError: If the password is blank.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError(_("Password is required."))
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Verify credentials and retrieve the authenticated active user.

        Checks credentials against the database. If valid, attaches the resolved
        user instance to ``attrs['user']``.

        Args:
            attrs (dict): Dictionary with ``username`` and ``password``.

        Returns:
            dict: Attribute dictionary containing verified ``attrs['user']``.

        Raises:
            ValidationError:
            - Credentials do not match any existing record.
            - Matching user account is deactivated (``is_active=False``).
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
