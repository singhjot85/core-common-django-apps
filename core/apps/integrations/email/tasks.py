"""
Asynchronous Celery tasks for persisting email delivery logs.
"""

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
    tracking_id: str = None,
    template_id: Optional[str] = None,
    backend: str = "",
    message: str = "",
    traceback: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist an EmailLog record asynchronously within the current tenant schema.

    Args:
        recipient (str): Destination email address.
        subject (str): Rendered email subject line.
        status (str): Delivery status choice string from ``EmailLogStatusChoices``.
        tracking_id (str, optional): Correlation identifier for tracking and webhooks.
            Defaults to None.
        template_id (str, optional): Primary key of the EmailTemplate used, if any.
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
        - Creates a new ``EmailLog`` record in the database.

    Returns:
        str: String representation of the newly created EmailLog UUID primary key.
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
        reference_id=tracking_id,
    )
    return str(log.id)
