"""
Abstract base service and execution workflow for payment processing.
"""

import abc
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from core.apps.integrations.payments import app_settings
from core.apps.integrations.payments.constants import PaymentLogStatusChoices
from core.apps.integrations.payments.tasks import log_payment_dispatch
from core.utils.tasks import queue_task

LOGGER = logging.getLogger(__name__)


class BasePaymentService(abc.ABC):
    """
    Execution workflow for payment processing services.

    Orchestrates authorization, capture, refunds, error handling, and asynchronous
    audit log dispatch via Celery.
    """

    def __init__(self, integration=None):
        """
        Initialize the payment service with an optional Integration model instance.

        Args:
            integration (AbstractIntegration, optional): Active integration configuration.
                Defaults to None.
        """
        self.integration = integration

    def charge(
        self,
        amount: Decimal,
        currency: Optional[str] = None,
        source: str = "default",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute payment charge and queue audit logging.

        Args:
            amount (Decimal): Transaction amount to charge.
            currency (str, optional): ISO 3-letter currency code. Defaults to app_settings.DEFAULT_CURRENCY.
            source (str, optional): Payment source or token identifier. Defaults to "default".
            **kwargs (Any): Additional parameters passed to backend.

        Side effects:
            - Asynchronously queues ``log_payment_dispatch`` Celery task to persist a PaymentLog.
            - Performs payment authorization/capture via backend adapter.

        Returns:
            dict: Result payload containing at least 'success' and 'transaction_id'.
        """
        currency = currency or app_settings.DEFAULT_CURRENCY
        status = PaymentLogStatusChoices.FAILED
        tx_id = ""
        traceback_str = ""
        error_msg = ""
        result = {}

        try:
            result = self._charge(
                amount=amount, currency=currency, source=source, **kwargs
            )
            tx_id = result.get("transaction_id", "")
            if result.get("success", False):
                status = PaymentLogStatusChoices.SUCCESS
            return result
        except Exception as exc:
            LOGGER.exception("Payment charge failed: %s", exc)
            error_msg = str(exc)
            traceback_str = str(exc)
            return {"success": False, "error": error_msg}
        finally:
            gateway_name = self.get_gateway_name()
            queue_task(
                log_payment_dispatch,
                transaction_id=tx_id,
                amount=str(amount),
                currency=currency,
                status=status,
                gateway=gateway_name,
                source=source,
                message=error_msg
                or (
                    "Charged" if status == PaymentLogStatusChoices.SUCCESS else "Failed"
                ),
                traceback=traceback_str,
                details=result,
            )

    def refund(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute refund and queue audit logging.

        Args:
            transaction_id (str): Original gateway transaction identifier.
            amount (Decimal, optional): Refund amount. None for full refund.
                Defaults to None.
            **kwargs (Any): Additional parameters passed to backend.

        Side effects:
            - Asynchronously queues ``log_payment_dispatch`` Celery task to persist a PaymentLog.
            - Performs refund via backend adapter.

        Returns:
            dict: Result payload containing at least 'success' and 'refund_id'.
        """
        status = PaymentLogStatusChoices.FAILED
        traceback_str = ""
        error_msg = ""
        result = {}

        try:
            result = self._refund(
                transaction_id=transaction_id, amount=amount, **kwargs
            )
            if result.get("success", False):
                status = PaymentLogStatusChoices.SUCCESS
            return result
        except Exception as exc:
            LOGGER.exception("Payment refund failed: %s", exc)
            error_msg = str(exc)
            traceback_str = str(exc)
            return {"success": False, "error": error_msg}
        finally:
            gateway_name = self.get_gateway_name()
            queue_task(
                log_payment_dispatch,
                transaction_id=transaction_id,
                amount=str(amount or Decimal("0.00")),
                currency=app_settings.DEFAULT_CURRENCY,
                status=status,
                gateway=gateway_name,
                source=f"refund_{transaction_id}",
                message=error_msg
                or (
                    "Refunded"
                    if status == PaymentLogStatusChoices.SUCCESS
                    else "Failed"
                ),
                traceback=traceback_str,
                details=result,
            )

    def get_gateway_name(self) -> str:
        """
        Return the identifier name of the underlying payment gateway.

        Returns:
            str: Class name or configured gateway identifier string.
        """
        return self.__class__.__name__

    @abc.abstractmethod
    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute concrete gateway charge operation.

        Args:
            amount (Decimal): Transaction amount.
            currency (str): ISO 3-letter currency code.
            source (str): Payment source or token identifier.
            **kwargs (Any): Gateway-specific options.

        Returns:
            dict: Gateway response payload with 'success' and 'transaction_id'.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _refund(
        self, transaction_id: str, amount: Optional[Decimal] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute concrete gateway refund operation.

        Args:
            transaction_id (str): Original gateway transaction identifier.
            amount (Decimal, optional): Refund amount. Defaults to None.
            **kwargs (Any): Gateway-specific options.

        Returns:
            dict: Gateway response payload with 'success' and 'refund_id'.
        """
        raise NotImplementedError
