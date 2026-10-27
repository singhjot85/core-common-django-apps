import logging
from typing import Any

from core.apps.integrations.sms import app_settings

from .base import BaseSMSService

LOGGER = logging.getLogger(__name__)


class SMSService(BaseSMSService):
    """
    Standard SMS delivery service delegating transport to configured backend.
    """

    def _send(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Deliver SMS using configured SMS backend.
        """
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else backend_class
        return backend.send_sms(to=to, message=message)

    def get_backend_name(self) -> str:
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__
        return str(backend_class)
