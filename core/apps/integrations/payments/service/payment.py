"""
Standard payment service delegating to the configured payment backend.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from core.apps.integrations.payments import app_settings

from .base import BasePaymentService

LOGGER = logging.getLogger(__name__)


class PaymentService(BasePaymentService):
    """
    Standard payment service delegating operations to configured backend.

    Instantiates the backend specified in ``app_settings.BACKEND`` and delegates
    charge and refund operations with amount and transaction parameters.
    """

    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute payment charge via the configured backend.

        Args:
            amount (Decimal): Transaction amount to charge.
            currency (str): ISO 3-letter currency code.
            source (str): Payment source or token identifier.
            **kwargs (Any): Additional parameters passed to backend.

        Side effects:
            - Performs charge operation against payment backend adapter.

        Returns:
            dict: Response payload containing at least 'success' and 'transaction_id'.
        """
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else backend_class
        return backend.charge(amount=amount, currency=currency, source=source, **kwargs)

    def _refund(
        self, transaction_id: str, amount: Optional[Decimal] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute payment refund via the configured backend.

        Args:
            transaction_id (str): Gateway transaction identifier.
            amount (Decimal, optional): Refund amount. None for full refund.
                Defaults to None.
            **kwargs (Any): Additional parameters passed to backend.

        Side effects:
            - Performs refund operation against payment backend adapter.

        Returns:
            dict: Response payload containing at least 'success' and 'refund_id'.
        """
        backend_class = app_settings.BACKEND
        backend = backend_class() if callable(backend_class) else backend_class
        return backend.refund(transaction_id=transaction_id, amount=amount, **kwargs)

    def get_gateway_name(self) -> str:
        """
        Return the configured payment backend class name or string identifier.

        Returns:
            str: Name of the backend class or string path.
        """
        backend_class = app_settings.BACKEND
        if hasattr(backend_class, "__name__"):
            return backend_class.__name__
        return str(backend_class)
