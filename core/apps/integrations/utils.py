"""
Unified dispatch facade utilities for email and SMS integrations.
"""

from typing import Any, Dict, Optional

from core.apps.integrations.email.service import get_email_service
from core.apps.integrations.sms.service import get_sms_service


def send_email(
    to: str,
    template: Optional[str] = None,
    subject: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    plain_body: Optional[str] = None,
    html_body: Optional[str] = None,
    **kwargs: Any,
) -> bool:
    """
    Dispatch an email via the active email integration service.

    Resolves the tenant's configured email service and dispatches the message using
    either a registered template key or direct subject/body content.

    Args:
        to (str): Recipient email address.
        template (str, optional): Key identifying the email template to render.
            Defaults to None.
        subject (str, optional): Email subject when not using a template.
            Defaults to None.
        context (dict, optional): Template context dictionary for placeholder substitution.
            Defaults to None.
        plain_body (str, optional): Plain text email content when not using a template.
            Defaults to None.
        html_body (str, optional): HTML email content when not using a template.
            Defaults to None.
        **kwargs (Any): Additional parameters passed to the underlying email backend.

    Side effects:
        - Asynchronously queues an EmailLog audit record via Celery.
        - May perform external network I/O depending on configured backend.

    Returns:
        bool: True if dispatch succeeded, False otherwise.
    """
    service = get_email_service()
    return service.send(
        to=to,
        template=template,
        subject=subject,
        context=context,
        plain_body=plain_body,
        html_body=html_body,
        **kwargs,
    )


def send_sms(
    to: str,
    message: Optional[str] = None,
    template: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> bool:
    """
    Dispatch an SMS via the active SMS integration service.

    Resolves the tenant's configured SMS service and dispatches the message using
    either a registered template key or direct message content.

    Args:
        to (str): Recipient phone number in E.164 or normalized format.
        message (str, optional): Direct SMS message body when not using a template.
            Defaults to None.
        template (str, optional): Key identifying the SMS template to render.
            Defaults to None.
        context (dict, optional): Template context dictionary for placeholder substitution.
            Defaults to None.
        **kwargs (Any): Additional parameters passed to the underlying SMS backend.

    Side effects:
        - Asynchronously queues an SMSLog audit record via Celery.
        - May perform external network I/O depending on configured backend.

    Returns:
        bool: True if dispatch succeeded, False otherwise.
    """
    service = get_sms_service()
    return service.send(
        to=to,
        message=message,
        template=template,
        context=context,
        **kwargs,
    )
