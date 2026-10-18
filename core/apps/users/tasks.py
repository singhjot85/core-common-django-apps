import logging
from contextlib import nullcontext

from celery import shared_task
from django.core.cache import cache

from core.apps.users import get_otp_log_model
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices
from core.apps.users.services.otp.factory import OTPServiceFactory

LOGGER = logging.getLogger(__name__)

OTPLog = get_otp_log_model()


@shared_task(bind=True, name="core.apps.users.tasks.send_otp_task")
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
        cache_key = OTPServiceFactory.cache_lock_key(identifier)
        # TODO: Implement custom LocalMemCache backend for tests, and then avoid this nullcontext(...)
        lock = cache.lock(cache_key) if hasattr(cache, "lock") else nullcontext()
        with lock:
            OTPServiceFactory.send_otp(
                identifier=identifier, channel=channel, purpose=purpose
            )
    except Exception as exc:
        LOGGER.error(f"Error in send_otp_task for {identifier}: {exc}", exc_info=exc)
        raise self.retry(exc=exc)

    return f"OTP sent successfully to {identifier} via {channel} ({purpose})"


@shared_task(bind=True, name="core.apps.users.tasks.create_otp_log_task")
def create_otp_log_task(
    self,
    identifier: str = None,
    recipient: str = "",
    channel: str = OTPChannelChoices.PHONE,
    purpose: str = OTPPurposeChoices.LOGIN,
    status: str = "",
    message: str = "",
    traceback: str = "",
):
    """
    Asynchronous worker task to create an OTP log entry in the database.
    """
    target = recipient or identifier
    LOGGER.info(f"Executing create_otp_log_task for {target} via {channel} ({purpose})")
    try:
        cache_key = OTPServiceFactory.cache_lock_key(target)
        # TODO: Implement custom LocalMemCache backend for tests, and then avoid this nullcontext(...)
        lock = cache.lock(cache_key) if hasattr(cache, "lock") else nullcontext()
        with lock:
            OTPLog.objects.create(
                recipient=target,
                channel=channel,
                purpose=purpose,
                status=status,
                message=message,
                traceback=traceback,
            )
    except Exception as exc:
        LOGGER.error(f"Error in create_otp_log_task for {target}: {exc}", exc_info=exc)
        raise self.retry(exc=exc)

    return f"OTP log created successfully for {target} via {channel} ({purpose})"
