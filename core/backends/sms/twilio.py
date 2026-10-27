import logging
from typing import Any, Optional

from django.core.exceptions import ImproperlyConfigured

from .base import BaseSMSBackend

LOGGER = logging.getLogger(__name__)

try:
    from twilio.rest import Client
except ImportError:
    Client = None


class TwilioSMSBackend(BaseSMSBackend):
    """
    Twilio SMS Backend, based on Twilio REST APIs using the Twilio SDK to send an SMS.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        _from: Optional[str] = None,
    ):
        super().__init__(_from=_from)
        self.account_sid = account_sid
        self.auth_token = auth_token

    def send_sms(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Send an SMS through the Twilio SDK.

        Args:
            to (str): Recipient phone number.
            message (str): Rendered message to send.

        Returns:
            bool: True representing success, False on failure.
        """
        if not Client:
            raise ImproperlyConfigured("twilio package is not installed.")

        try:
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(body=message, from_=self._from, to=to)
            return True
        except Exception as exc:
            LOGGER.exception("Failed to send SMS via Twilio: %s", exc)
            return False
