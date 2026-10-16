import logging

from celery import shared_task

from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices
from core.apps.users.services.otp import OTPServiceFactory

LOGGER = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="core.apps.users.tasks.send_otp_task",
    max_retries=2,
    default_retry_delay=5,
)
def send_otp_task(
    self,
    identifier: str,
    channel: str = OTPChannelChoices.PHONE,
    purpose: str = OTPPurposeChoices.LOGIN,
):
    """
    Asynchronous worker task to generate and dispatch OTP codes to phone or email.
    """
    LOGGER.info(f"Executing send_otp_task for {identifier} via {channel} ({purpose})")

    try:
        return OTPServiceFactory.send_otp(
            identifier=identifier, channel=channel, purpose=purpose
        )
    except Exception as exc:
        LOGGER.error(f"Error in send_otp_task for {identifier}: {exc}", exc_info=exc)
        raise self.retry(exc=exc)
