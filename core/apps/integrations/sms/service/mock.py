"""
Mock SMS delivery service for simulation and testing environments.
"""

import logging
from typing import Any

from .base import BaseSMSService

LOGGER = logging.getLogger(__name__)


class MockSMSService(BaseSMSService):
    """
    Mock SMS delivery service active when integration.mock == True.

    Logs message content without conducting network I/O or invoking external providers.
    """

    def _send(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Simulate SMS delivery by logging content without network I/O.

        Args:
            to (str): Recipient phone number.
            message (str): Rendered message body text.
            **kwargs (Any): Additional ignored arguments.

        Side effects:
            - Emits info log record with SMS details.

        Returns:
            bool: Always returns True.
        """
        LOGGER.info(
            "[MockSMSService] Simulating SMS \n"
            "----------------------------------------\n"
            "To: %s\n"
            "Message: %s\n"
            "----------------------------------------",
            to,
            message,
        )
        return True
