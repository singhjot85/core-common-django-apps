"""
Console payment backend for development, testing, and debugging.
"""

import logging
import uuid
from decimal import Decimal
from typing import Any, Dict

from .base import BasePaymentBackend

LOGGER = logging.getLogger(__name__)


class ConsolePaymentBackend(BasePaymentBackend):
    """
    Simulated payment backend logging transaction details to application logger.

    Used for development and testing environments without contacting external payment gateways.
    """

    def charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simulate a successful charge and return a generated mock transaction identifier.

        Args:
            amount (Decimal): Transaction amount to simulate charging.
            currency (str): ISO 3-letter currency code.
            source (str): Payment source or token identifier.
            **kwargs (Any): Additional ignored parameters.

        Returns:
            dict: Response payload containing 'success', 'transaction_id', 'amount', and 'currency'.
        """
        tx_id = f"mock_tx_{uuid.uuid4().hex[:12]}"
        LOGGER.info(
            "[ConsolePaymentBackend] Charge %s %s on source %s -> %s",
            amount,
            currency,
            source,
            tx_id,
        )
        return {
            "success": True,
            "transaction_id": tx_id,
            "amount": str(amount),
            "currency": currency,
        }

    def refund(
        self, transaction_id: str, amount: Decimal = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simulate a successful refund and return a generated mock refund identifier.

        Args:
            transaction_id (str): Original simulated transaction identifier.
            amount (Decimal, optional): Refund amount. None for full refund.
                Defaults to None.
            **kwargs (Any): Additional ignored parameters.

        Returns:
            dict: Response payload containing 'success', 'refund_id', 'transaction_id', and 'amount'.
        """
        refund_id = f"mock_ref_{uuid.uuid4().hex[:12]}"
        LOGGER.info(
            "[ConsolePaymentBackend] Refund %s for tx %s -> %s",
            amount,
            transaction_id,
            refund_id,
        )
        return {
            "success": True,
            "refund_id": refund_id,
            "transaction_id": transaction_id,
            "amount": str(amount) if amount else None,
        }
