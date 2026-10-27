import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from .base import BasePaymentService

LOGGER = logging.getLogger(__name__)


class MockPaymentService(BasePaymentService):
    """
    Mock payment processing service active when integration.mock == True.
    """

    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
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
