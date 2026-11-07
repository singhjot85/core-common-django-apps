"""
Twilio SMS backend using the Twilio REST SDK.
"""

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
    Deliver SMS messages via the Twilio REST API using the Twilio Python SDK.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        _from: Optional[str] = None,
    ):
        """
        Initialize Twilio client credentials and default sender phone number.

        Args:
            account_sid (str, optional): Twilio Account SID identifier.
                Defaults to None.
            auth_token (str, optional): Twilio Auth Token credential.
                Defaults to None.
            _from (str, optional): Sender phone number or Twilio Messaging Service SID.
                Defaults to None.
        """
        super().__init__(_from=_from)
        self.account_sid = account_sid
        self.auth_token = auth_token

    def send_sms(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Send an SMS through the Twilio SDK.

        Args:
            to (str): Recipient phone number in E.164 format.
            message (str): Rendered message body to send.
            **kwargs (Any): Additional delivery parameters.

        Side effects:
            - Performs external network HTTP request to Twilio API.

        Returns:
            bool: True representing success, False on failure.

        Raises:
            ImproperlyConfigured:
            - When the ``twilio`` package is not installed.
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
