"""
Abstract base definitions for SMS delivery backends.
"""

import abc


class BaseSMSBackend(abc.ABC):
    """
    Abstract interface for SMS delivery adapter backends.

    Subclasses must implement the ``send_sms`` method to interface with specific
    SMS transport providers (e.g. Twilio, AWS SNS, Console).
    """

    @abc.abstractmethod
    def send_sms(self, to: str, message: str) -> bool:
        """
        Send an SMS message to the recipient phone number.

        Args:
            to (str): Recipient phone number in E.164 or normalized format.
            message (str): SMS payload message string.

        Returns:
            bool: True if dispatch succeeded, False otherwise.
        """
        raise NotImplementedError
