import logging
import uuid
from decimal import Decimal
from typing import Any, Dict

from .base import BasePaymentBackend

LOGGER = logging.getLogger(__name__)


class ConsolePaymentBackend(BasePaymentBackend):
    """
    Development and testing payment backend that outputs transaction details to logs.
    """

    def charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simulate a successful charge and return a mock transaction ID.
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
        Simulate a successful refund.
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
