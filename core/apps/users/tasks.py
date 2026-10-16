import logging

from celery import shared_task

from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.otp import OTPService

LOGGER = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="core.apps.users.tasks.send_otp_task",
    max_retries=2,
    default_retry_delay=5,
)
def send_otp_task(
    self, identifier: str, channel: str = "phone", purpose: str = "login"
):
    """
    Asynchronous worker task to generate and dispatch OTP codes to phone or email.
    """
    LOGGER.info(f"Executing send_otp_task for {identifier} via {channel} ({purpose})")

    try:
        if channel == OTPChannelChoices.PHONE:
            return OTPService.send_phone_otp(phone_number=identifier, purpose=purpose)
        elif channel == OTPChannelChoices.EMAIL:
            return OTPService.send_email_otp(email=identifier, purpose=purpose)
        else:
            LOGGER.error(f"Unsupported OTP delivery channel: {channel}")
            return False
    except Exception as exc:
        LOGGER.error(f"Error in send_otp_task for {identifier}: {exc}", exc_info=exc)
        raise self.retry(exc=exc)
