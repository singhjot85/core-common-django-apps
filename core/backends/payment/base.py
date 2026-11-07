"""
Abstract base definitions for payment delivery adapters.
"""

import abc
from decimal import Decimal
from typing import Any, Dict


class BasePaymentBackend(abc.ABC):
    """
    Abstract interface for payment gateway delivery adapters.

    Subclasses must implement ``charge`` and ``refund`` methods to integrate
    with specific payment gateways (e.g. Stripe, Razorpay).
    """

    @abc.abstractmethod
    def charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute payment authorization and capture against the gateway.

        Args:
            amount (Decimal): Transaction amount.
            currency (str): ISO 3-letter currency code (e.g. 'USD').
            source (str): Payment method identifier, token, or customer ID.
            **kwargs (Any): Gateway-specific optional parameters.

        Returns:
            dict: Response dictionary containing at least 'success' and 'transaction_id'.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def refund(
        self, transaction_id: str, amount: Decimal = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute full or partial refund against the gateway.

        Args:
            transaction_id (str): Original gateway transaction identifier.
            amount (Decimal, optional): Refund amount. None for full refund.
                Defaults to None.
            **kwargs (Any): Gateway-specific optional parameters.

        Returns:
            dict: Response dictionary containing at least 'success' and 'refund_id'.
        """
        raise NotImplementedError
