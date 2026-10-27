import abc

from django.conf import settings


class BaseSMSBackend(abc.ABC):
    """
    Abstract interface for SMS delivery adapter backends.

    Subclasses must implement `send_sms(to, message)`.
    """

    def __init__(self, _from: str = None):
        """
        Initialize SMS backend with sender number.

        Args:
            _from (str, optional): The sender phone number.
        """
        if not _from:
            _from = getattr(settings, "DEFAULT_FROM_PHONE_NUMBER", None)

        self._from = _from

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
