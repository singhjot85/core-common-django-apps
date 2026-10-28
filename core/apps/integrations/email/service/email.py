import logging
from typing import Any, Optional

from django.core.mail import EmailMultiAlternatives

from core.apps.integrations.email import app_settings

from .base import BaseEmailService

LOGGER = logging.getLogger(__name__)


class EmailService(BaseEmailService):
    """
    Standard email delivery service delegating transport to configured backend.
    """

    def _send(
        self,
        to: str,
        subject: str,
        plain_body: str,
        tracking_id: str,
        html_body: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Deliver message using configured email backend.
        """
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else None

        from_email = kwargs.get("from_email") or app_settings.DEFAULT_FROM_EMAIL

        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=from_email,
            to=[to],
            connection=backend,
            headers={"message-id": tracking_id},
        )
        if html_body:
            email.attach_alternative(html_body, "text/html")

        sent_count = email.send(fail_silently=False)
        return sent_count > 0

    def get_backend_name(self) -> str:
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__

        return str(backend_class)
