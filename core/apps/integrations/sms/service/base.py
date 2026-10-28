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
    Template and execution workflow for SMS delivery services.
    """

    def __init__(self, integration=None):
        self.integration = integration

    def load_template(self, template_key: str) -> Dict[str, Any]:
        """
        Fetch the cached active template dictionary for an interface type.
        """
        return SMSTemplate.get_template(template_key)

    def render_template(
        self, template_data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """
        Render SMS text payload using template data.
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
        Strict two paths: template-driven rendering OR raw message value.
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
        Identifier name of the underlying backend.
        """
        return self.__class__.__name__

    @abc.abstractmethod
    def _send(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Subclasses implement concrete delivery transport.
        """
        raise NotImplementedError
