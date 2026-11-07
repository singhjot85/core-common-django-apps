"""
Mock email delivery service for simulation and testing environments.
"""

import logging
from typing import Any, Optional

from .base import BaseEmailService

LOGGER = logging.getLogger(__name__)


class MockEmailService(BaseEmailService):
    """
    Mock email delivery service active when integration.mock == True.

    Logs message content without conducting network I/O or invoking external gateways.
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

        Args:
            to (str): Recipient email address.
            subject (str): Rendered subject line.
            plain_body (str): Rendered plain text body.
            html_body (str, optional): Rendered HTML body. Defaults to None.
            **kwargs (Any): Additional ignored arguments.

        Side effects:
            - Emits info log record with email delivery details.

        Returns:
            bool: Always returns True.
        """
        LOGGER.info(
            "[MockEmailService] Simulating email delivery \n"
            "-----------------------------------------------\n"
            "To: %s\n"
            "Subject: %s\n"
            "Content: %s\n"
            "-----------------------------------------------",
            to,
            subject,
            plain_body,
        )
        return True
