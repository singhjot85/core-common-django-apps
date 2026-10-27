import logging

from backends.sms.base import BaseSMSBackend

LOGGER = logging.getLogger(__name__)


class ConsoleSMSBackend(BaseSMSBackend):
    """
    Development and testing SMS backend that outputs SMS content to logs and stdout.
    """

    def send_sms(self, to: str, message: str) -> bool:
        """
        Log and print SMS content to stdout.

        Args:
            to (str): Recipient phone number.
            message (str): SMS payload message string.

        Returns:
            bool: Always returns True.
        """
        LOGGER.info(f"[ConsoleSMSBackend] Sending SMS to {to}: {message}")
        print(  # noqa: T201
            f"\n========================================\n"
            f"[SMS to {to}]: {message}\n"
            f"========================================\n"
        )
        return True
