"""
Console email backend for development and test logging.
"""

import logging

from django.core.mail.backends.console import EmailBackend

LOGGER = logging.getLogger(__name__)


class CoreConsoleEmailBackend(EmailBackend):
    """
    Log email messages to standard application logger and stdout stream.

    Extends Django's standard console email backend to capture dispatch details
    in application logs instead of writing exclusively to the stdout stream.
    """

    def send_messages(self, email_messages):
        """
        Log email messages and delegate dispatch to Django's console email backend.

        Args:
            email_messages (list): Iterable of EmailMessage or EmailMultiAlternatives instances.

        Side effects:
            - Emits info log records for each message.
            - Writes message text to stdout stream via superclass.

        Returns:
            int: Number of successfully dispatched messages.
        """
        LOGGER.info("[%s]: %s", self.__class__.__name__, email_messages)
        return super().send_messages(email_messages)
