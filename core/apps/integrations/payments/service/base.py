import abc
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db import connection

from core.apps.integrations.payments import app_settings
from core.apps.integrations.payments.constants import PaymentLogStatusChoices
from core.apps.integrations.payments.tasks import log_payment_dispatch
from core.utils.tasks import queue_task

LOGGER = logging.getLogger(__name__)


class BasePaymentService(abc.ABC):
    """
    Template and execution workflow for payment processing services.
    """

    def __init__(self, integration=None):
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
            schema_name = getattr(connection, "schema_name", "public")
            gateway_name = self.get_gateway_name()
            queue_task(
                log_payment_dispatch,
                schema_name=schema_name,
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
            schema_name = getattr(connection, "schema_name", "public")
            gateway_name = self.get_gateway_name()
            queue_task(
                log_payment_dispatch,
                schema_name=schema_name,
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
        return self.__class__.__name__

    @abc.abstractmethod
    def _charge(
        self, amount: Decimal, currency: str, source: str, **kwargs: Any
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def _refund(
        self, transaction_id: str, amount: Optional[Decimal] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        raise NotImplementedError
