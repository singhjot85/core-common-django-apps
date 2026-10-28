import abc
import logging
import traceback
import uuid
from typing import Any, Dict, Optional, Tuple

from core.apps.integrations.email import get_email_log_model, get_email_template_model
from core.apps.integrations.email.constants import EmailLogStatusChoices
from core.apps.integrations.email.tasks import log_email_dispatch
from core.utils.tasks import queue_task

LOGGER = logging.getLogger(__name__)

EmailTemplate = get_email_template_model()
EmailLog = get_email_log_model()


class BaseEmailService(abc.ABC):
    """
    Template and execution workflow for email delivery services.
    """

    def __init__(self, integration=None):
        self.integration = integration

    def load_template(self, template_key: str) -> Dict[str, Any]:
        """
        Fetch the cached active template dictionary for an interface type.
        """
        return EmailTemplate.get_template(template_key)

    def render_template(
        self, template_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        Render subject, plain text, and HTML body from cached template data.
        """
        raw_subject = template_data.get("subject", "")
        subject = EmailTemplate.render_template(raw_subject, context)

        raw_plain = template_data.get("template", "")
        plain_content = EmailTemplate.render_template(raw_plain, context)

        raw_html = template_data.get("html_template", "")
        html_content = EmailTemplate.render_template(raw_html, context)

        return subject, plain_content, html_content

    def send(
        self,
        to: str,
        template: Optional[str] = None,
        subject: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        plain_body: Optional[str] = None,
        html_body: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Execute email dispatch and asynchronously queue delivery audit logging.
        Strict two paths: template-driven rendering OR raw content values.
        """
        context = context or {}
        if template:
            template_data = self.load_template(template)
            if template_data:
                subject, plain_body, html_body = self.render_template(
                    template_data, context
                )

        subject = subject or ""
        plain_body = plain_body or ""
        tracking_id = str(uuid.uuid4())

        status = EmailLogStatusChoices.FAILED
        log_message = "Failed"
        traceback_str = ""

        try:
            success = self._send(
                to=to,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body,
                tracking_id=tracking_id**kwargs,
            )
            if success:
                log_message = "Delivered"
                status = EmailLogStatusChoices.SUCCESS

            return success

        except Exception as exc:
            LOGGER.exception("Failed to send email to %s: %s", to, exc)
            log_message = str(exc)
            traceback_str = traceback.format_exc()
            return False
        finally:
            queue_task(
                log_email_dispatch,
                recipient=to,
                subject=subject,
                status=status,
                backend=self.get_backend_name(),
                message=log_message,
                traceback=traceback_str,
                context=context,
                tracking_id=tracking_id,
            )

    def get_backend_name(self) -> str:
        """
        Identifier name of the underlying backend.
        """
        return self.__class__.__name__

    @abc.abstractmethod
    def _send(
        self,
        to: str,
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Subclasses implement concrete delivery transport.
        """
        raise NotImplementedError
