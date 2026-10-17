import logging

from core.apps.users import app_settings, get_user_model
from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.otp.base import BaseOTPService
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
        return User.objects.filter(phone_number=identifier.strip()).exists()

    def deliver(self, identifier: str, code: str, message: str) -> bool:
        """
        Deliver the OTP code via configured SMS backend.

        TODO: Build out sms service, that sends email's from template's and effectively
            Keep swappable backends on that sms service and move this backend.send_sms there
        """
        try:
            sms_backend_class = app_settings.SMS_BACKEND
            sms_backend: BaseSMSBackend = sms_backend_class()
            result = sms_backend.send_sms(to=identifier.strip(), message=message)
            return True if result is None else bool(result)
        except Exception as e:
            LOGGER.exception(f"Failed to send OTP SMS to {identifier}: {e}")
            return False
