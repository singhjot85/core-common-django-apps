import logging
from contextlib import nullcontext

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from core.apps.users import get_otp_log_model, get_user_model
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
        raise self.retry(exc=exc) from exc

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
        raise self.retry(exc=exc) from exc

    return f"OTP log created successfully for {target} via {channel} ({purpose})"


@shared_task(bind=True, name="core.apps.users.tasks.send_account_unlock_email_task")
def send_account_unlock_email_task(
    self,
    user_id: str,
    token: str,
    recipient_email: str = None,
):
    """
    Asynchronous task to dispatch an account unlock link email to the locked-out user.
    """
    LOGGER.info(f"Executing send_account_unlock_email_task for user {user_id}")
    try:
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()
        email = recipient_email or (user.email if user else None)
        if not email:
            LOGGER.warning(f"No email available to send unlock link for user {user_id}")
            return "No recipient email available"

        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        unlock_url = f"{frontend_url}/auth/unlock/?token={token}"
        subject = "Action Required: Unlock Your Account"
        message = (
            f"Hello,\n\n"
            f"Your account was temporarily locked due to multiple failed authentication attempts.\n\n"
            f"To unlock your account, please click the following secure link:\n"
            f"{unlock_url}\n\n"
            f"This link is valid for 24 hours. If you did not make these attempts, please contact support.\n"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@core.internal"),
            recipient_list=[email],
            fail_silently=False,
        )
        return f"Unlock email sent to {email}"
    except Exception as exc:
        LOGGER.error(
            f"Failed to send unlock email for user {user_id}: {exc}", exc_info=exc
        )
        raise self.retry(exc=exc) from exc
