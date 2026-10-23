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

    LOCKOUT_TOKEN_TIMEOUT: int = 86400  # 24 hours

    @classmethod
    def _clean_identifier(cls, identifier: str) -> str:
        return identifier.strip().lower()

    @classmethod
    def _attempts_key(cls, identifier: str) -> str:
        clean = cls._clean_identifier(identifier)
        return f"{connection.schema_name}:auth_attempts:{clean}"

    @classmethod
    def _lockout_key(cls, identifier: str) -> str:
        clean = cls._clean_identifier(identifier)
        return f"{connection.schema_name}:auth_locked:{clean}"

    @classmethod
    def _unlock_token_key(cls, token: str) -> str:
        return f"{connection.schema_name}:auth_unlock_token:{token}"

    @classmethod
    def get_max_attempts(cls) -> int:
        return getattr(app_settings, "OTP_MAX_ATTEMPTS", 5)

    @classmethod
    def get_attempt_timeout(cls) -> int:
        return getattr(app_settings, "OTP_EXPIRY_SECONDS", 300)

    @classmethod
    def is_locked(cls, identifier: str) -> bool:
        """
        Check if the identifier is marked as locked out in cache.
        """
        clean = cls._clean_identifier(identifier)
        return bool(cache.get(cls._lockout_key(clean)))

    @classmethod
    def _find_user(cls, identifier: str) -> typing.Optional["AbstractUser"]:
        """
        Locate user by username, email, or phone number.
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
        Record a failed authentication attempt.

        Returns:
            tuple[int, bool]: (remaining_attempts, is_locked)
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
        Reset failed attempts upon successful authentication.
        """
        clean = cls._clean_identifier(identifier)
        cache.delete(cls._attempts_key(clean))
        cache.delete(cls._lockout_key(clean))

    @classmethod
    def lock_account_and_dispatch_unlock(cls, identifier: str) -> None:
        """
        Invalidate OTP, lock user account if found, and send unlock email.
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
                    timeout=cls.LOCKOUT_TOKEN_TIMEOUT,
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
        Verify the one-time unlock token and re-enable the user account.

        Returns:
            tuple[bool, str]: (success, message)
        """
        if not token or not token.strip():
            return False, str(_("Invalid or missing unlock token."))

        token_key = cls._unlock_token_key(token.strip())
        user_id = cache.get(token_key)
        if not user_id:
            return False, str(_("The unlock link is invalid or has expired."))

        user = User.objects.filter(pk=user_id).first()
        if not user:
            return False, str(_("User account not found."))

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
