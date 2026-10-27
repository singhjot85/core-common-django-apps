import logging
from typing import Any

from .base import BaseSMSService

LOGGER = logging.getLogger(__name__)


class MockSMSService(BaseSMSService):
    """
    Mock SMS delivery service active when integration.mock == True.
    """

    def _send(self, to: str, message: str, **kwargs: Any) -> bool:
        """
        Simulate SMS delivery by logging content without network I/O.
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
