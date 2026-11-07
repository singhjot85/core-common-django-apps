"""
Abstract base models for payment transaction and operation logs.
"""

from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.integrations.payments.constants import PaymentLogStatusChoices
from core.utils.models import BaseLogModel


class AbstractPaymentLog(BaseLogModel):
    """
    Log of payment operations (charges, refunds, authorizations).

    Tracks gateway responses, transaction IDs, amounts, currencies, and status
    for billing and compliance audit trails. Inherits audit timestamps and status
    management from ``BaseLogModel``.

    Attributes:
        transaction_id (str): Unique transaction identifier returned by gateway.
        amount (Decimal): Transaction amount with two decimal places.
        currency (str): Three-letter ISO currency code (e.g. 'USD').
        gateway (str): Identifier name of the payment gateway used.
        source (str): Identifier of the payment source, customer, or token.
        details (dict): Raw JSON response payload returned by the gateway.
    """

    STATUS = PaymentLogStatusChoices.choices

    transaction_id = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Transaction ID"),
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Amount"),
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        verbose_name=_("Currency"),
    )
    gateway = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name=_("Gateway"),
    )
    source = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Payment Source / Customer ID"),
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Response Details"),
    )

    class Meta(BaseLogModel.Meta):
        abstract = True
        verbose_name = _("Payment Log")
        verbose_name_plural = _("Payment Logs")

    def __str__(self) -> str:
        """
        Return gateway, amount, currency, and status summary.

        Returns:
            str: Formatted string representing transaction summary.
        """
        return f"{self.gateway} {self.amount} {self.currency} [{self.get_status_display()}] ({self.transaction_id})"
