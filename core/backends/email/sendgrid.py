"""
SendGrid email backend using the SendGrid Web API client.
"""

import logging
import typing
import uuid

from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

try:
    from sendgrid import SendGridAPIClient
except ImportError:
    SendGridAPIClient = None

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from django.core.mail import EmailMultiAlternatives


class SendGridEmailBackend(BaseEmailBackend):
    """
    Dispatch emails via the SendGrid REST API v3 using the SendGrid Python client.

    Extracts HTML alternatives and attaches custom arguments (such as message-id and
    group-id headers) for downstream tracking and webhook attribution.
    """

    def __init__(self, fail_silently=False, **kwargs):
        """
        Initialize SendGrid backend and extract API credentials.

        Args:
            fail_silently (bool, optional): Whether to suppress exceptions during dispatch.
                Defaults to False.
            **kwargs: Backend configuration options including ``api_key``.

        Raises:
            ImproperlyConfigured:
            - When ``api_key`` is not provided in kwargs.
        """
        self.api_key = kwargs.pop("api_key", None)
        if not self.api_key:
            raise ImproperlyConfigured("API Key not configured for sendgrid.")

        super().__init__(fail_silently, **kwargs)

        self.sendgrid_client = None

    def open(self):
        """
        Initialize and validate connection to the SendGrid client.
        """
        self.sendgrid_client = self._get_sendgrid_client()

    def close(self):
        """
        Tear down and clear active SendGrid client credentials.
        """
        self.api_key = None
        self.sendgrid_client = None

    def _get_sendgrid_client(self):
        """
        Instantiate SendGridAPIClient using the configured API key.

        Returns:
            SendGridAPIClient: Authenticated client instance.

        Raises:
            ImproperlyConfigured:
            - When the ``sendgrid`` package is not installed.
        """
        if SendGridAPIClient is None:
            raise ImproperlyConfigured("sendgrid not installed.")

        self.sendgrid_client = SendGridAPIClient(self.api_key)

    def _build_sendgrid_messages(self, email_message: "EmailMultiAlternatives") -> dict:
        """
        Convert a Django EmailMultiAlternatives instance into a dict of SendGrid Mail objects.

        Maps subject, body, text/html alternatives, and recipient addresses into
        individual SendGrid Mail objects tagged with tracking metadata.

        Args:
            email_message (EmailMultiAlternatives): Django email message instance to convert.

        Returns:
            dict: Mapping of message_id strings to SendGrid Mail object instances.
        """
        from sendgrid.helpers.mail import Mail  # noqa: PLC0415

        sendgrid_messages = {}

        html_content = ""
        for alt in email_message.alternatives:
            if alt.mimetype == "text/html":
                html_content = alt.content

        group_id = str(email_message.extra_headers.get("group-id", uuid.uuid4()))
        for to in email_message.to:
            # Build out message object
            message = Mail(
                from_email=email_message.from_email,
                to_emails=to,
                subject=email_message.subject,
                plain_text_content=email_message.body,
                html_content=html_content,
            )

            # Append a platform specific, unique-identifier and group-identifier
            message_id = str(
                email_message.extra_headers.get("message-id", uuid.uuid4())
            )
            message.custom_args = {"message_id": message_id, "group_id": group_id}

            sendgrid_messages[message_id] = message

        return sendgrid_messages

    def send_messages(self, email_messages: "EmailMultiAlternatives"):
        """
        Send an iterable of email messages via SendGrid Web API.

        Args:
            email_messages (Sequence[EmailMultiAlternatives]): Email messages to dispatch.

        Side effects:
            - Makes external HTTP API requests to the SendGrid API endpoint.

        Returns:
            int: Number of successfully sent email messages.
        """
        if not hasattr(self, "sendgrid_client"):
            self.sendgrid_client = self._get_sendgrid_client()

        success = 0
        for message in self._build_sendgrid_messages(email_messages[0]):
            try:
                response = self.sendgrid_client.send(message)
                LOGGER.info("Successfully sent mail >>> %s", response)
                if response.status_code >= 400:
                    LOGGER.warning("Email send failed >>> %s", response)
                success += 1
            except Exception as e:
                LOGGER.error("Exception in sending mail", exc_info=e)

        return success
