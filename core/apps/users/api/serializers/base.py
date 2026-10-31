"""
Common serializer bases and mixins for authentication and user lifecycle workflows.

Provides:
- UserDetailsSerializer: Serializes authenticated user attributes.
- BaseSignupSerializer: Shared signup field declarations and uniqueness validations.
- BaseOTPVerificationSerializer: Verification, lockout enforcement, and dispatch mixin for OTP workflows.
- validate_clean_phone_number: Phone normalization and minimum length validation utility.
"""

import logging
import re
import typing

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.apps.users import app_settings, get_user_model
from core.apps.users.constants import OTPPurposeChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.apps.users.services.otp import OTPServiceFactory
from core.apps.users.tasks import send_otp_task
from core.utils.tasks import queue_task

User = get_user_model()
LOGGER = logging.getLogger(__name__)


def validate_clean_phone_number(value: str) -> str:
    """
    Validate that phone number contains at least 7 digits.

    Strips whitespace and checks that numeric digits meet the minimum length
    threshold of 7 digits required for valid international or domestic routing.

    Args:
        value (str): Raw input phone number string.

    Returns:
        str: Cleaned, whitespace-trimmed phone number string.

    Raises:
        ValidationError: If stripped phone number contains fewer than 7 digits.
    """
    clean_val = value.strip()
    digits = re.sub(r"\D", "", clean_val)
    if len(digits) < 7:
        raise serializers.ValidationError(_("Invalid phone number format."))
    return clean_val


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Convert authenticated User instances into detailed JSON representations.

    Exposes read-only identity, profile, contact attributes, and verification status flags.
    Never exposes sensitive authentication hashes or security tokens.

    Read-only fields:
    - ``id``, ``full_name``, ``is_phone_verified``, ``is_email_verified``,
      ``has_password``, ``created``, ``modified``.
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
    Base serializer for user registration enforcing core uniqueness and normalization rules.

    Provides common name, contact, and identity fields, validating that usernames,
    emails, and phone numbers are not already associated with existing accounts.

    Validation rules:
    - ``first_name`` is required and non-blank.
    - ``username``, if provided, must be unique across all active and inactive users (case-insensitive).
    - ``email``, if provided, must be a valid email and unique in the database (case-insensitive).
    - ``phone_number``, if provided, must contain at least 7 digits and be unique in the database.
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
        Validate that the submitted username is unique in the database.

        Args:
            value (str): Submitted username string.

        Returns:
            str: Trimmed username string, or empty string if blank.

        Raises:
            ValidationError: If an account with the matching username already exists.
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
        Validate that the submitted email address is unique in the database.

        Args:
            value (str, optional): Submitted email string.

        Returns:
            str or None: Lowercased and trimmed email address, or None if omitted.

        Raises:
            ValidationError: If an account with the matching email already exists.
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
        Validate phone number syntax and verify it does not already exist.

        Args:
            value (str, optional): Raw submitted phone number string.

        Returns:
            str or None: Cleaned phone number string, or None if omitted.

        Raises:
            ValidationError:
            - Phone number contains fewer than 7 digits.
            - An account with the matching phone number already exists.
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
        Create and persist a new user record in the database.

        Delegates to the configured User manager's ``create_user`` method, which
        handles automatic unique username generation when omitted.

        Side effects:
        - Writes a new user row to the database.

        Args:
            validated_data (dict): Sanitized and validated payload dictionary.

        Returns:
            User: The newly created user instance.
        """
        return User.objects.create_user(**validated_data)


class SendOTPMixin:
    """
    A mixin providing send. otp functionality
    """

    @classmethod
    def send_otp(
        cls,
        identifier: str,
        channel: str,
        purpose: str = OTPPurposeChoices.LOGIN,
    ) -> bool:
        """
        Queue background task to generate and dispatch OTP to recipient.

        Enqueues ``send_otp_task`` via ``queue_task`` on commit to avoid blocking
        the HTTP request thread.

        Side effects:
        - Enqueues ``send_otp_task`` background Celery job.

        Args:
            identifier (str): Destination phone number or email address.
            channel (str): Delivery channel (e.g. ``"phone"`` or ``"email"``).
            purpose (str, optional): Purpose of the OTP. Defaults to ``"login"``.

        Returns:
            bool: True if task was successfully queued, False otherwise.
        """
        try:
            queue_task(
                task=send_otp_task,
                task_kwargs={
                    "identifier": identifier,
                    "channel": channel,
                    "purpose": purpose,
                },
                on_commit=True,
            )
            return True
        except Exception as e:
            LOGGER.error(
                f"Failed to queue OTP task for {identifier} via {channel}: {e}"
            )
            return False


class BaseOTPVerificationSerializer(serializers.Serializer):
    """
    Mixin serializer providing OTP dispatch, validation, and lockout handling.

    Enforces account lockout checks against AuthLockoutService before verifying
    the submitted OTP against cache. Records failed verification attempts when invalid.
    Also provides asynchronous OTP dispatch queueing to prevent user enumeration.

    Attributes:
        otp_code (CharField): Verification passcode of length ``app_settings.OTP_LENGTH``.
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
        Verify the submitted OTP code against cache and check lockout status.

        Checks if the identifier is currently locked before attempting verification.
        On invalid code, increments failed attempt counter in cache and returns remaining attempts.

        Side effects:
        - Increments lockout failure counter in cache on incorrect code.
        - Deletes OTP cache entry upon successful match or max attempts reached.

        Args:
            identifier (str): Target phone number or email address.
            code (str): One-time verification passcode.

        Returns:
            tuple[bool, str]: A tuple of ``(is_valid, user_facing_message)``.

        Raises:
            ValidationError: If the identity is locked due to excessive failed attempts.
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
