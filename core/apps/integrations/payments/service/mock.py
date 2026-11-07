"""
Mock payment service for simulation and testing environments.
"""

import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from .base import BasePaymentService

LOGGER = logging.getLogger(__name__)


class MockPaymentService(BasePaymentService):
    """
    Mock payment processing service active when integration.mock == True.

    Logs transactions and generates deterministic mock identifiers without
    communicating with external payment gateways.
    """

    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simulate a payment charge and return a mock transaction identifier.

        Args:
            amount (Decimal): Transaction amount to simulate charging.
            currency (str): ISO 3-letter currency code.
            source (str): Payment source or token identifier.
            **kwargs (Any): Additional ignored arguments.

        Side effects:
            - Emits info log record with simulated transaction details.

        Returns:
            dict: Simulated success payload containing 'transaction_id', 'amount', and 'currency'.
        """
        tx_id = f"mock_tx_{uuid.uuid4().hex[:12]}"
        LOGGER.info(
            "[MockPaymentService] Charge simulated: amount=%s %s, source=%s, tx=%s",
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

    def _refund(
        self, transaction_id: str, amount: Optional[Decimal] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simulate a payment refund and return a mock refund identifier.

        Args:
            transaction_id (str): Original simulated transaction identifier.
            amount (Decimal, optional): Refund amount. Defaults to None.
            **kwargs (Any): Additional ignored arguments.

        Side effects:
            - Emits info log record with simulated refund details.

        Returns:
            dict: Simulated success payload containing 'refund_id', 'transaction_id', and 'amount'.
        """
        ref_id = f"mock_ref_{uuid.uuid4().hex[:12]}"
        LOGGER.info(
            "[MockPaymentService] Refund simulated: tx=%s, amount=%s, ref=%s",
            transaction_id,
            amount,
            ref_id,
        )
        return {
            "success": True,
            "refund_id": ref_id,
            "transaction_id": transaction_id,
            "amount": str(amount) if amount else None,
        }
