"""
Abstract base definitions for SMS delivery backends.
"""

import abc

from django.conf import settings


class BaseSMSBackend(abc.ABC):
    """
    Abstract interface for SMS delivery adapter backends.

    Subclasses must implement the ``send_sms`` method to interface with specific
    SMS transport providers (e.g. Twilio, AWS SNS, Console).
    """

    def __init__(self, _from: str = None):
        """
        Initialize the SMS backend with an optional default sender identifier.

        Args:
            _from (str, optional): Default sender phone number or alphanumeric ID.
                Defaults to settings.DEFAULT_FROM_PHONE_NUMBER if not provided.
        """
        if not _from:
            _from = getattr(settings, "DEFAULT_FROM_PHONE_NUMBER", None)

        self._from = _from

    @abc.abstractmethod
    def send_sms(self, to: str, message: str, **kwargs) -> bool:
        """
        Send an SMS message to the recipient phone number.

        Args:
            to (str): Recipient phone number in E.164 or normalized format.
            message (str): SMS message text payload.
            **kwargs: Provider-specific delivery parameters.

        Returns:
            bool: True if dispatch succeeded, False otherwise.
        """
        raise NotImplementedError
