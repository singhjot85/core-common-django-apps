import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from core.apps.integrations.payments import app_settings

from .base import BasePaymentService

LOGGER = logging.getLogger(__name__)


class PaymentService(BasePaymentService):
    """
    Standard payment service delegating operations to configured backend.
    """

    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else backend_class
        return backend.charge(amount=amount, currency=currency, source=source, **kwargs)

    def _refund(
        self, transaction_id: str, amount: Optional[Decimal] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else backend_class
        return backend.refund(transaction_id=transaction_id, amount=amount, **kwargs)

    def get_gateway_name(self) -> str:
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__
        return str(backend_class)
