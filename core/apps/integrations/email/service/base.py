"""
Abstract base service and template workflow for email delivery.
"""

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
    Template rendering and execution workflow for email delivery services.

    Handles template resolution from Redis cache, context rendering for plain text
    and HTML alternatives, error handling, and asynchronous audit log dispatch via Celery.
    """

    def __init__(self, integration=None):
        """
        Initialize the email service with an optional Integration model instance.

        Args:
            integration (AbstractIntegration, optional): Active integration configuration.
                Defaults to None.
        """
        self.integration = integration

    def load_template(self, template_key: str) -> Dict[str, Any]:
        """
        Fetch the cached active template dictionary for an interface type.

        Args:
            template_key (str): Interface type identifying the template.

        Returns:
            dict: Cached template mapping with 'subject', 'template', and 'html_template'.
        """
        return EmailTemplate.get_template(template_key)

    def render_template(
        self, template_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        Render subject, plain text, and HTML body from cached template data.

        Args:
            template_data (dict): Dictionary containing raw template strings.
            context (dict): Context variables used for placeholder substitution.

        Returns:
            tuple[str, str, str]: Rendered (subject, plain_content, html_content).
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

        Supports two dispatch paths: template-driven rendering using a registered template
        key, or raw subject and body values.

        Args:
            to (str): Recipient email address.
            template (str, optional): Key identifying the email template to load.
                Defaults to None.
            subject (str, optional): Direct email subject line if not using template.
                Defaults to None.
            context (dict, optional): Context dictionary for template substitution.
                Defaults to None.
            plain_body (str, optional): Direct plain text body if not using template.
                Defaults to None.
            html_body (str, optional): Direct HTML body if not using template.
                Defaults to None.
            **kwargs (Any): Additional options passed through to underlying delivery backend.

        Side effects:
            - Asynchronously queues ``log_email_dispatch`` Celery task to persist an EmailLog.
            - Performs delivery transport via subclass ``_send`` implementation.

        Returns:
            bool: True if dispatch succeeded, False on error.
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
                tracking_id=tracking_id,
                **kwargs,
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
        Return the identifier name of the underlying backend.

        Returns:
            str: Class name or configured backend identifier string.
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
        Execute concrete transport delivery for the email message.

        Args:
            to (str): Recipient email address.
            subject (str): Rendered subject line.
            plain_body (str): Rendered plain text body.
            html_body (str, optional): Rendered HTML alternative body. Defaults to None.
            **kwargs (Any): Additional transport options.

        Returns:
            bool: True if message was accepted/sent, False otherwise.
        """
        raise NotImplementedError
