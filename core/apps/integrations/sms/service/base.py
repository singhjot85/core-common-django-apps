"""
Abstract base service and template workflow for SMS delivery.
"""

import abc
import logging
import uuid
from typing import Any, Dict, Optional

from core.apps.integrations.sms import get_sms_template_model
from core.apps.integrations.sms.constants import SMSLogStatusChoices
from core.apps.integrations.sms.tasks import log_sms_dispatch
from core.utils.tasks import queue_task

LOGGER = logging.getLogger(__name__)

SMSTemplate = get_sms_template_model()


class BaseSMSService(abc.ABC):
    """
    Template rendering and execution workflow for SMS delivery services.

    Handles template resolution from Redis cache, context rendering for plain text,
    error handling, and asynchronous audit log dispatch via Celery.
    """

    def __init__(self, integration=None):
        """
        Initialize the SMS service with an optional Integration model instance.

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
            dict: Cached template mapping containing 'template' string.
        """
        return SMSTemplate.get_template(template_key)

    def render_template(
        self, template_data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """
        Render SMS text payload using template data.

        Args:
            template_data (dict): Dictionary containing raw template string.
            context (dict): Context variables used for placeholder substitution.

        Returns:
            str: Rendered SMS message body string.
        """
        plain_template = template_data.get("template", "") or ""
        return SMSTemplate.render_template(plain_template, context)

    def send(
        self,
        to: str,
        message: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Execute SMS dispatch and asynchronously queue delivery audit logging.

        Supports two dispatch paths: template-driven rendering using a registered template
        key, or raw message content.

        Args:
            to (str): Recipient phone number in E.164 or normalized format.
            message (str, optional): Direct SMS message body if not using template.
                Defaults to None.
            template (str, optional): Key identifying the SMS template to load.
                Defaults to None.
            context (dict, optional): Context dictionary for template substitution.
                Defaults to None.
            **kwargs (Any): Additional options passed through to underlying delivery backend.

        Side effects:
            - Asynchronously queues ``log_sms_dispatch`` Celery task to persist an SMSLog.
            - Performs delivery transport via subclass ``_send`` implementation.

        Returns:
            bool: True if dispatch succeeded, False on error.
        """
        context = context or {}
        if template:
            template_data = self.load_template(template)
            if template_data:
                message = self.render_template(template_data, context)

        message = message or ""

        status = SMSLogStatusChoices.FAILED
        log_message = "Failed"
        traceback_str = ""
        tracking_id = str(uuid.uuid4())

        try:
            success = self._send(
                to=to, message=message, tracking_id=tracking_id, **kwargs
            )
            if success:
                status = SMSLogStatusChoices.SUCCESS
                log_message = "Delivered"

            return success
        except Exception as exc:
            LOGGER.exception("Failed to send SMS to %s: %s", to, exc)
            log_message = str(exc)
            traceback_str = str(exc)
            return False

        finally:
            backend_name = self.get_backend_name()
            queue_task(
                log_sms_dispatch,
                recipient=to,
                status=status,
                backend=backend_name,
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
    def _send(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Execute concrete transport delivery for the SMS message.

        Args:
            to (str): Recipient phone number.
            message (str): Rendered message body text.
            **kwargs (Any): Additional transport options.

        Returns:
            bool: True if dispatch succeeded, False otherwise.
        """
        raise NotImplementedError
