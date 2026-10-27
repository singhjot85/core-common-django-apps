import logging
from typing import Any, Dict, Optional

from celery import shared_task

from core.apps.integrations.sms import get_sms_log_model

LOGGER = logging.getLogger(__name__)


@shared_task(bind=True, name="core.apps.integrations.sms.tasks.log_sms_dispatch")
def log_sms_dispatch(
    self,
    recipient: str,
    status: str,
    template_id: Optional[str] = None,
    backend: str = "",
    message: str = "",
    traceback: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist an SMSLog record asynchronously within the current tenant schema.
    """
    SMSLog = get_sms_log_model()
    log = SMSLog.objects.create(
        recipient=recipient,
        status=status,
        template_id=template_id,
        backend=backend,
        message=message[:255] if message else "",
        traceback=traceback,
        context=context or {},
    )
    return str(log.id)
