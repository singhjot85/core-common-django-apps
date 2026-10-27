import logging
from typing import Any, Optional

from .base import BaseEmailService

LOGGER = logging.getLogger(__name__)


class MockEmailService(BaseEmailService):
    """
    Mock email delivery service active when integration.mock == True.
    """

    def _send(
        self,
        to: str,
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Simulate email delivery by logging message contents without network I/O.
        """
        LOGGER.info(
            "[MockEmailService] Simulating email delivery \n" \
            "-----------------------------------------------\n" \
            "To: %s\n" \
            "Subject: %s\n"
            "Content: %s\n" \
            "-----------------------------------------------",
            to,
            subject,
            plain_body,
        )
        return True
