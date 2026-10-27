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
    integration=None,
    **kwargs: Any,
) -> bool:
    """
    Unified facade to dispatch an email via the active email integration service.
    """
    service = get_email_service(integration=integration)
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
    integration=None,
    **kwargs: Any,
) -> bool:
    """
    Unified facade to dispatch an SMS via the active SMS integration service.
    """
    service = get_sms_service(integration=integration)
    return service.send(
        to=to,
        message=message,
        template=template,
        context=context,
        **kwargs,
    )
