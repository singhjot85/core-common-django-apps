import logging
from typing import Any, Dict, Optional

from celery import shared_task

from core.apps.integrations.email import get_email_log_model

LOGGER = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="core.apps.integrations.email.tasks.log_email_dispatch",
)
def log_email_dispatch(
    self,
    recipient: str,
    subject: str,
    status: str,
    template_id: Optional[str] = None,
    backend: str = "",
    message: str = "",
    traceback: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist an EmailLog record asynchronously within the current tenant schema.
    """
    EmailLog = get_email_log_model()
    log = EmailLog.objects.create(
        recipient=recipient,
        subject=subject,
        status=status,
        template_id=template_id,
        backend=backend,
        message=message[:255] if message else "",
        traceback=traceback,
        context=context or {},
    )
    return str(log.id)
