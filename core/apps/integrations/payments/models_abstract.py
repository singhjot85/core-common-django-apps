from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.integrations.payments.constants import PaymentLogStatusChoices
from core.utils.models import BaseLogModel


class AbstractPaymentLog(BaseLogModel):
    """
    Log of payment operations (charges, refunds, authorizations).
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
        return f"{self.gateway} {self.amount} {self.currency} [{self.get_status_display()}] ({self.transaction_id})"
