import logging

from django.core.mail.backends.console import EmailBackend

LOGGER = logging.getLogger(__name__)


class CoreConsoleEmailBackend(EmailBackend):
    """
    Django write's the logs to sys.stdout stream, overriding to LOG the emails
    """

    def send_messages(self, email_messages):
        LOGGER.info("[%s]: %s", self.__class__.__name__, email_messages)
        return super().send_messages(email_messages)
