"""
Standard SMS delivery service delegating to the configured SMS backend.
"""

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

    Instantiates the backend specified in ``app_settings.BACKEND`` and delegates
    SMS transmission with message payload and tracking metadata.
    """

    def _send(self, to: str, message: str, **kwargs) -> bool:
        """
        Deliver SMS using configured SMS backend.

        Args:
            to (str): Recipient phone number.
            message (str): Rendered message body text.
            **kwargs: Additional parameters passed to backend.

        Side effects:
            - Performs SMS dispatch via backend adapter.

        Returns:
            bool: True if dispatch succeeded, False otherwise.
        """
        backend_class = app_settings.BACKEND
        backend: "BaseSMSBackend" = (
            backend_class() if callable(backend_class) else backend_class
        )
        return backend.send_sms(to=to, message=message, **kwargs)

    def get_backend_name(self) -> str:
        """
        Return the configured SMS backend class name or string identifier.

        Returns:
            str: Name of the backend class or string path.
        """
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__
        return str(backend_class)
