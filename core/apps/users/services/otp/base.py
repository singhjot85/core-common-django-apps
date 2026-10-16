import abc
import hashlib
import hmac
import logging
import secrets
import typing

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from core.apps.users import app_settings, get_otp_log_model
from core.apps.users.constants import OTPDeliveryStatusChoices, OTPPurposeChoices

if typing.TYPE_CHECKING:
    from core.apps.users.models_abstract import AbstractOTPLog  # noqa: F401

LOGGER = logging.getLogger(__name__)
OTPLog = get_otp_log_model()


class BaseOTPService(abc.ABC):
    """
    Template method pattern base class for OTP dispatch and verification.

    Subclasses implement channel-specific existence checks (`check_user_exists`)
    and delivery execution (`deliver`).
    """

    channel: str

    @classmethod
    def _make_cache_key(cls, identifier: str) -> str:
        clean = identifier.strip().lower()
        return f"users_otp:{clean}"

    @classmethod
    def _make_attempts_key(cls, identifier: str) -> str:
        clean = identifier.strip().lower()
        return f"users_otp_attempts:{clean}"

    @classmethod
    def generate_code(cls, length: int = 6) -> str:
        """Generate a cryptographically secure numeric string."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @classmethod
    def hash_code(cls, code: str) -> str:
        """Hash OTP code with SECRET_KEY for secure cache storage."""
        secret = getattr(settings, "SECRET_KEY", "core-secret").encode("utf-8")
        return hmac.new(
            secret, code.strip().encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @classmethod
    def set_otp_cache(cls, identifier: str, code: str, timeout: int) -> None:
        """Store hashed OTP code in cache with expiration."""
        cache.set(cls._make_cache_key(identifier), cls.hash_code(code), timeout=timeout)
        cache.delete(cls._make_attempts_key(identifier))

    def build_message(self, code: str, timeout: int) -> str:
        """Hook to construct the user-facing OTP notification text."""
        return (
            f"Your verification code is: {code}. It expires in {timeout // 60} minutes."
        )

    @abc.abstractmethod
    def check_user_exists(self, identifier: str) -> bool:
        """
        Hook to check whether a user exists for the given identifier.

        Args:
            identifier (str): Phone number or email.

        Returns:
            bool: True if user exists in the database.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def deliver(self, identifier: str, code: str, message: str) -> bool:
        """
        Hook to perform actual delivery via SMS, Email, or other channel.

        Args:
            identifier (str): Recipient address or phone number.
            code (str): The raw OTP code.
            message (str): Formatted message string.

        Returns:
            bool: True on successful dispatch, False otherwise.
        """
        raise NotImplementedError

    def send_otp(self, identifier: str, purpose: str = OTPPurposeChoices.LOGIN) -> bool:
        """
        Template method defining the standardized OTP dispatch workflow:
        1. If purpose is LOGIN, verify user existence via `check_user_exists`.
        2. Generate numeric OTP code.
        3. Store hashed code in cache with expiration.
        4. Construct message text.
        5. Invoke channel delivery hook `deliver(identifier, code, message)`.
        6. Record delivery audit log in OTPLog.
        7. Return success boolean.
        """
        clean_identifier = identifier.strip()

        if purpose == OTPPurposeChoices.LOGIN and not self.check_user_exists(
            clean_identifier
        ):
            LOGGER.info(
                f"OTP login requested for non-existent {self.channel}: {clean_identifier}"
            )
            OTPLog.objects.create(
                recipient=clean_identifier,
                channel=self.channel,
                purpose=purpose,
                status=OTPDeliveryStatusChoices.FAILED,
            )
            return False

        length = app_settings.OTP_LENGTH
        timeout = app_settings.OTP_EXPIRY_SECONDS
        code = self.generate_code(length=length)
        self.set_otp_cache(clean_identifier, code, timeout=timeout)

        message = self.build_message(code=code, timeout=timeout)
        success = self.deliver(identifier=clean_identifier, code=code, message=message)

        OTPLog.objects.create(
            recipient=clean_identifier,
            channel=self.channel,
            purpose=purpose,
            status=(
                OTPDeliveryStatusChoices.SENT
                if success
                else OTPDeliveryStatusChoices.FAILED
            ),
        )
        return success

    @classmethod
    def verify_otp(cls, identifier: str, code: str) -> tuple[bool, str]:
        """
        Verify the provided OTP against the cached code for the given identifier.

        Returns:
            tuple[bool, str]: (is_valid, human_readable_message)
        """
        clean_id = identifier.strip().lower()
        cache_key = cls._make_cache_key(clean_id)
        attempts_key = cls._make_attempts_key(clean_id)

        stored_hash = cache.get(cache_key)
        if not stored_hash:
            return False, str(_("OTP has expired or was never requested."))

        attempts = cache.get(attempts_key, 0)
        max_attempts = app_settings.OTP_MAX_ATTEMPTS
        if attempts >= max_attempts:
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return False, str(_("Too many failed attempts. Please request a new OTP."))

        expected_hash = cls.hash_code(code)
        if hmac.compare_digest(stored_hash, expected_hash):
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return True, str(_("OTP verified successfully."))

        # Increment failed attempts
        cache.set(attempts_key, attempts + 1, timeout=app_settings.OTP_EXPIRY_SECONDS)
        return False, str(_("Invalid OTP code."))
