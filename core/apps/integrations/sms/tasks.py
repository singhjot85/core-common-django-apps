"""
Asynchronous Celery tasks for persisting SMS delivery logs.
"""

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
    tracking_id: str = None,
    backend: str = "",
    message: str = "",
    traceback: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist an SMSLog record asynchronously within the current tenant schema.

    Args:
        recipient (str): Destination phone number.
        status (str): Delivery status choice string from ``SMSLogStatusChoices``.
        template_id (str, optional): Primary key of the SMSTemplate used, if any.
            Defaults to None.
        tracking_id (str, optional): Correlation identifier for tracking and logs.
            Defaults to None.
        backend (str, optional): Identifier name of the backend adapter.
            Defaults to "".
        message (str, optional): Status summary or error message.
            Defaults to "".
        traceback (str, optional): Exception stack trace on failure.
            Defaults to "".
        context (dict, optional): Context parameters used during rendering.
            Defaults to None.

    Side effects:
        - Creates a new ``SMSLog`` record in the database.

    Returns:
        str: String representation of the newly created SMSLog UUID primary key.
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
        reference_id=tracking_id,
    )
    return str(log.id)
