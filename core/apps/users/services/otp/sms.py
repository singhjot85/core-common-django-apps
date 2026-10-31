import logging
import typing

from core.apps.users import app_settings, get_user_model
from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.otp.base import BaseOTPService
from core.apps.users.utils import normalize_to_e164

if typing.TYPE_CHECKING:
    from core.utils.backends.sms import BaseSMSBackend

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class PhoneOTPService(BaseOTPService):
    """
    SMS / Phone-based OTP service implementing the BaseOTPService template.
    """

    channel = OTPChannelChoices.PHONE

    def check_user_exists(self, identifier: str) -> bool:
        """Check if user exists with the given phone number."""
        clean_id = identifier.strip()
        e164_phone = normalize_to_e164(clean_id) or clean_id
        return User.objects.filter(phone_number=e164_phone).exists()

    def deliver(self, identifier: str, code: str, message: str) -> bool:
        """
        Deliver the OTP code via configured SMS backend.

        TODO: Build out sms service, that sends email's from template's and effectively
            Keep swappable backends on that sms service and move this backend.send_sms there
        """
        try:
            clean_id = identifier.strip()
            e164_phone = normalize_to_e164(clean_id) or clean_id
            sms_backend_class = app_settings.SMS_BACKEND
            sms_backend: BaseSMSBackend = sms_backend_class()
            result = sms_backend.send_sms(to=e164_phone, message=message)
            return True if result is None else bool(result)
        except Exception as e:
            LOGGER.exception(f"Failed to send OTP SMS to {identifier}: {e}")
            return False
