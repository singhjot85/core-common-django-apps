import logging
import typing

from core.apps.integrations.sms import app_settings

from .base import BaseSMSService

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from core.backends.sms import BaseSMSBackend


class SMSService(BaseSMSService):
    """
    Standard SMS delivery service delegating transport to configured backend.
    """

    def _send(self, to: str, message: str, **kwargs) -> bool:
        """
        Deliver SMS using configured SMS backend.
        """
        backend_class = app_settings.BACKEND
        backend: "BaseSMSBackend" = (
            backend_class() if callable(backend_class) else backend_class
        )
        return backend.send_sms(to=to, message=message, **kwargs)

    def get_backend_name(self) -> str:
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__
        return str(backend_class)
