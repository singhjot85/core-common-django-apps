"""
Authentication attempt tracking, account lockout, and unlock services.
Enforces zero-enumeration security semantics to prevent account discovery.
"""

import logging
import secrets
import typing

from django.core.cache import cache
from django.db import connection
from django.utils.translation import gettext_lazy as _

from core.apps.users import app_settings, get_user_model
from core.utils.tasks import queue_task

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractUser

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class AuthLockoutService:
    """
    Service for tracking failed authentication attempts, locking accounts upon
    exhaustion, and dispatching one-time unlock links via email.
    """

    LOCKOUT_TOKEN_TIMEOUT: int = app_settings.LOCKOUT_TOKEN_TIMEOUT
    DEFAULT_UNLOCK_FAILURE_MSG = _("The unlock link is invalid or has expired.")

    @classmethod
    def get_lockout_token_timeout(cls) -> int:
        """
        Return the configured cache validity timeout for unlock tokens.

        Returns:
            int: Timeout duration in seconds.
        """
        return getattr(app_settings, "LOCKOUT_TOKEN_TIMEOUT", cls.LOCKOUT_TOKEN_TIMEOUT)

    @classmethod
    def _clean_identifier(cls, identifier: str) -> str:
        """
        Normalize identifier string for consistent cache key generation.

        Args:
            identifier (str): Username, email, or phone number.

        Returns:
            str: Stripped and lowercased string representation.
        """
        return identifier.strip().lower()

    @classmethod
    def _attempts_key(cls, identifier: str) -> str:
        """
        Generate schema-isolated cache key for tracking failed authentication attempts.

        Args:
            identifier (str): User identifier (username, email, or phone).

        Returns:
            str: Cache key partitioned by tenant schema.
        """
        clean = cls._clean_identifier(identifier)
        return f"{connection.schema_name}:auth_attempts:{clean}"

    @classmethod
    def _lockout_key(cls, identifier: str) -> str:
        """
        Generate schema-isolated cache key indicating locked status.

        Args:
            identifier (str): User identifier.

        Returns:
            str: Cache key partitioned by tenant schema.
        """
        clean = cls._clean_identifier(identifier)
        return f"{connection.schema_name}:auth_locked:{clean}"

    @classmethod
    def _unlock_token_key(cls, token: str) -> str:
        """
        Generate schema-isolated cache key for account unlock token verification.

        Args:
            token (str): Random URL-safe unlock token.

        Returns:
            str: Cache key partitioned by tenant schema.
        """
        return f"{connection.schema_name}:auth_unlock_token:{token}"

    @classmethod
    def get_max_attempts(cls) -> int:
        """
        Retrieve maximum failed attempts threshold before triggering lockout.

        Returns:
            int: Maximum allowed attempts. Defaults to 5.
        """
        return getattr(app_settings, "OTP_MAX_ATTEMPTS", 5)

    @classmethod
    def get_attempt_timeout(cls) -> int:
        """
        Retrieve cache time-to-live in seconds for failed attempt tracking window.

        Returns:
            int: Expiry duration in seconds. Defaults to 300.
        """
        return getattr(app_settings, "OTP_EXPIRY_SECONDS", 300)

    @classmethod
    def is_locked(cls, identifier: str) -> bool:
        """
        Check if the identifier is marked as locked out in the cache.

        Args:
            identifier (str): Username, email, or phone number.

        Returns:
            bool: True if lockout flag is active in cache, False otherwise.
        """
        clean = cls._clean_identifier(identifier)
        return bool(cache.get(cls._lockout_key(clean)))

    @classmethod
    def _find_user(cls, identifier: str) -> typing.Optional["AbstractUser"]:
        """
        Locate user by username, email, or phone number without leaking existence.

        Args:
            identifier (str): Value to match against username, email, or phone.

        Returns:
            AbstractUser | None: Matched user instance or None if not found.
        """
        try:
            clean = cls._clean_identifier(identifier)
            return (
                User.objects.filter(username__iexact=clean).first()
                or User.objects.filter(email__iexact=clean).first()
                or User.objects.filter(phone_number=identifier.strip()).first()
            )
        except Exception:
            return None

    @classmethod
    def record_failed_attempt(cls, identifier: str) -> tuple[int, bool]:
        """
        Record a failed authentication attempt and lock account if limit exceeded.

        Increments cache failure count within the sliding time window. If the limit
        is exceeded, activates lockout in cache and triggers account deactivation
        and unlock email dispatch.

        Side effects:
            - Updates or deletes attempt counter in cache.
            - Sets lockout key in cache if limit reached.
            - Triggers ``lock_account_and_dispatch_unlock`` on lockout.

        Args:
            identifier (str): User identifier (username, email, phone).

        Returns:
            tuple[int, bool]: Tuple of (remaining_attempts, is_locked).
        """
        clean = cls._clean_identifier(identifier)
        key = cls._attempts_key(clean)
        attempts = cache.get(key, 0) + 1
        max_attempts = cls.get_max_attempts()

        if attempts >= max_attempts:
            # Invalidate attempts and lock
            cache.delete(key)
            cache.set(cls._lockout_key(clean), True, timeout=cls.LOCKOUT_TOKEN_TIMEOUT)
            cls.lock_account_and_dispatch_unlock(identifier)
            return 0, True

        cache.set(key, attempts, timeout=cls.get_attempt_timeout())
        return max(0, max_attempts - attempts), False

    @classmethod
    def clear_attempts(cls, identifier: str) -> None:
        """
        Reset failed attempt counters and lockout state upon successful authentication.

        Side effects:
            - Deletes attempt counter and lockout keys from cache.

        Args:
            identifier (str): User identifier.
        """
        clean = cls._clean_identifier(identifier)
        cache.delete(cls._attempts_key(clean))
        cache.delete(cls._lockout_key(clean))

    @classmethod
    def lock_account_and_dispatch_unlock(cls, identifier: str) -> None:
        """
        Invalidate cached OTP codes, deactivate user account, and queue unlock email.

        Under zero-enumeration design, executes silently if the user does not exist.

        Side effects:
            - Evicts cached OTP and OTP attempts.
            - Sets ``user.is_active = False`` in database if user exists.
            - Stores one-time unlock token in cache.
            - Queues asynchronous Celery task to send unlock email.

        Args:
            identifier (str): Target user identifier.
        """
        clean = cls._clean_identifier(identifier)
        # 1. Invalidate OTP cache
        otp_cache_key = f"{connection.schema_name}:users_otp:{clean}"
        otp_attempts_key = f"{connection.schema_name}:users_otp_attempts:{clean}"
        cache.delete(otp_cache_key)
        cache.delete(otp_attempts_key)

        # 2. Lock user if exists
        user = cls._find_user(clean)
        if user:
            try:
                user.is_active = False
                user.save(update_fields=["is_active"])
                LOGGER.warning(
                    f"User {user.pk} ({clean}) locked out due to failed attempts."
                )

                # Generate secure one-time unlock token
                token = secrets.token_urlsafe(32)
                cache.set(
                    cls._unlock_token_key(token),
                    str(user.pk),
                    timeout=cls.get_lockout_token_timeout(),
                )

                # Dispatch unlock email task via queue_task
                queue_task(
                    "core.apps.users.tasks.send_account_unlock_email_task",
                    task_kwargs={
                        "user_id": str(user.pk),
                        "token": token,
                        "recipient_email": user.email,
                    },
                    on_commit=False,
                )
            except Exception as e:
                LOGGER.error(
                    f"Failed to lock user {user.pk} and dispatch unlock email: {e}"
                )

    @classmethod
    def verify_and_unlock_account(cls, token: str) -> tuple[bool, str]:
        """
        Verify one-time unlock token and reactivate the user account.

        Side effects:
            - Sets ``user.is_active = True`` in database.
            - Evicts unlock token from cache.
            - Clears failed attempt counters across username, email, and phone.

        Args:
            token (str): URL-safe token supplied from unlock link.

        Returns:
            tuple[bool, str]: Tuple of (success, message).
        """
        if not token or not token.strip():
            return False, str(_("Invalid or missing unlock token."))

        token_key = cls._unlock_token_key(token.strip())
        user_id = cache.get(token_key)
        if not user_id:
            return False, str(cls.DEFAULT_UNLOCK_FAILURE_MSG)

        user = User.objects.filter(pk=user_id).first()
        if not user:
            LOGGER.error(f"User not found for given user_id: {user_id}")
            return False, str(cls.DEFAULT_UNLOCK_FAILURE_MSG)

        user.is_active = True
        user.save(update_fields=["is_active"])

        # Clear token and attempts
        cache.delete(token_key)
        cls.clear_attempts(user.username)
        if user.email:
            cls.clear_attempts(user.email)
        if user.phone_number:
            cls.clear_attempts(user.phone_number)

        LOGGER.info(f"User {user.pk} successfully unlocked via unlock token.")
        return True, str(_("Account successfully unlocked. You may now sign in."))
