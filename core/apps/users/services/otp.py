import abc
import hashlib
import hmac
import logging
import secrets

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _

from core.apps.users import app_settings, get_otp_log_model, get_user_model
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
)

LOGGER = logging.getLogger(__name__)

User = get_user_model()
OTPLog = get_otp_log_model()


class BaseSMSBackend(abc.ABC):
    """Abstract interface for sending SMS messages."""

    @abc.abstractmethod
    def send_sms(self, to: str, message: str) -> bool:
        """Send an SMS message to a phone number. Returns True on success."""
        raise NotImplementedError


class ConsoleSMSBackend(BaseSMSBackend):
    """Development/Testing SMS backend that outputs to logs/console."""

    def send_sms(self, to: str, message: str) -> bool:
        LOGGER.info(f"[ConsoleSMSBackend] Sending SMS to {to}: {message}")
        print(  # noqa: T201
            f"\n========================================\n[SMS to {to}]: {message}\n========================================\n"
        )
        return True


class OTPService:
    """Service handling generation, caching, dispatch, and verification of OTP codes."""

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

    @classmethod
    def send_phone_otp(cls, phone_number: str, purpose: str = "login") -> bool:
        """
        Generate and dispatch OTP to a phone number via configured SMS backend.
        """
        # If login flow, verify user exists
        user_exists = User.objects.filter(phone_number=phone_number).exists()
        if purpose == OTPPurposeChoices.LOGIN and not user_exists:
            LOGGER.info(f"OTP login requested for non-existent phone: {phone_number}")
            OTPLog.objects.create(
                recipient=phone_number,
                channel=OTPChannelChoices.PHONE,
                purpose=purpose,
                status=OTPDeliveryStatusChoices.FAILED,
            )
            return False

        length = app_settings.OTP_LENGTH
        timeout = app_settings.OTP_EXPIRY_SECONDS
        code = cls.generate_code(length=length)
        cls.set_otp_cache(phone_number, code, timeout=timeout)

        sms_backend: BaseSMSBackend = app_settings.SMS_BACKEND()
        message = (
            f"Your verification code is: {code}. It expires in {timeout // 60} minutes."
        )
        success = sms_backend.send_sms(to=phone_number, message=message)

        OTPLog.objects.create(
            recipient=phone_number,
            channel=OTPChannelChoices.PHONE,
            purpose=purpose,
            status=(
                OTPDeliveryStatusChoices.SENT
                if success
                else OTPDeliveryStatusChoices.FAILED
            ),
        )
        return success

    @classmethod
    def send_email_otp(cls, email: str, purpose: str = "login") -> bool:
        """
        Generate and dispatch OTP to an email address.
        """
        user_exists = User.objects.filter(email__iexact=email.strip()).exists()
        if purpose == OTPPurposeChoices.LOGIN and not user_exists:
            LOGGER.info(f"OTP login requested for non-existent email: {email}")
            OTPLog.objects.create(
                recipient=email,
                channel=OTPChannelChoices.EMAIL,
                purpose=purpose,
                status=OTPDeliveryStatusChoices.FAILED,
            )
            return False

        length = app_settings.OTP_LENGTH
        timeout = app_settings.OTP_EXPIRY_SECONDS
        code = cls.generate_code(length=length)
        cls.set_otp_cache(email, code, timeout=timeout)

        subject = _("Your Verification Code")
        message = f"Your verification code is: {code}. It will expire in {timeout // 60} minutes."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email.strip()],
                fail_silently=False,
            )
            success = True
        except Exception as e:
            LOGGER.error(f"Failed to send OTP email to {email}: {e}")
            success = False

        OTPLog.objects.create(
            recipient=email,
            channel=OTPChannelChoices.EMAIL,
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
        Returns (is_valid, message).
        """
        clean_id = identifier.strip().lower()
        cache_key = cls._make_cache_key(clean_id)
        attempts_key = cls._make_attempts_key(clean_id)

        stored_hash = cache.get(cache_key)
        if not stored_hash:
            return False, _("OTP has expired or was never requested.")

        attempts = cache.get(attempts_key, 0)
        max_attempts = app_settings.OTP_MAX_ATTEMPTS
        if attempts >= max_attempts:
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return False, _("Too many failed attempts. Please request a new OTP.")

        expected_hash = cls.hash_code(code)
        if hmac.compare_digest(stored_hash, expected_hash):
            cache.delete(cache_key)
            cache.delete(attempts_key)
            return True, _("OTP verified successfully.")

        # Increment failed attempts
        cache.set(attempts_key, attempts + 1, timeout=app_settings.OTP_EXPIRY_SECONDS)
        return False, _("Invalid OTP code.")
