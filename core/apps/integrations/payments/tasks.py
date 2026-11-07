"""
Asynchronous Celery tasks for persisting payment operation logs.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from celery import shared_task

from core.apps.integrations.payments import get_payment_log_model

LOGGER = logging.getLogger(__name__)


@shared_task(
    bind=True, name="core.apps.integrations.payments.tasks.log_payment_dispatch"
)
def log_payment_dispatch(
    self,
    transaction_id: str,
    amount: str,
    currency: str,
    status: str,
    gateway: str = "",
    source: str = "",
    message: str = "",
    traceback: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Persist a PaymentLog record asynchronously within the current tenant schema.

    Args:
        transaction_id (str): Transaction identifier from the gateway.
        amount (str): String representation of the Decimal transaction amount.
        currency (str): Three-letter ISO currency code.
        status (str): Status choice string from ``PaymentLogStatusChoices``.
        gateway (str, optional): Name of the payment gateway adapter. Defaults to "".
        source (str, optional): Source account or payment token. Defaults to "".
        message (str, optional): Status summary or failure message. Defaults to "".
        traceback (str, optional): Exception stack trace if operation failed. Defaults to "".
        details (dict, optional): Raw gateway response dictionary. Defaults to None.

    Side effects:
        - Creates a new ``PaymentLog`` record in the database.

    Returns:
        str: String representation of the newly created PaymentLog UUID primary key.
    """
    PaymentLog = get_payment_log_model()
    log = PaymentLog.objects.create(
        transaction_id=transaction_id,
        amount=Decimal(amount),
        currency=currency,
        status=status,
        gateway=gateway,
        source=source,
        message=message[:255] if message else "",
        traceback=traceback,
        details=details or {},
    )
    return str(log.id)
