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
    """ """

    def __init__(self, fail_silently=..., **kwargs):
        """ """
        self.api_key = kwargs.pop("api_key", None)
        if not self.api_key:
            raise ImproperlyConfigured("API Key not configured for sendgrid.")

        super().__init__(fail_silently, **kwargs)

        self.sendgrid_client = None

    def open(self):
        """ """
        self.sendgrid_client = self._get_sendgrid_client()

    def close(self):
        """ """
        self.api_key = None
        self.sendgrid_client = None

    def _get_sendgrid_client(self):
        """ """
        if SendGridAPIClient is None:
            raise ImproperlyConfigured("sendgrid not installed.")

        self.sendgrid_client = SendGridAPIClient(self.api_key)

    def _build_sendgrid_messages(self, email_message: "EmailMultiAlternatives") -> dict:
        """ """
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
        """ """

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
