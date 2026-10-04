import typing
from decimal import Decimal
from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.utils.models import BaseModel

if typing.TYPE_CHECKING:
    from .invoices import AbstractInvoice


class AbstractInvoiceItem(BaseModel):
    """
    Abstract model for inventory-maintained and cataloged items.
    """

    name = models.CharField(max_length=255, verbose_name=_("Item Name"))
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Price"),
    )
    discount_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Discount Options"),
    )
    HSN_code = models.CharField(
        max_length=64, null=True, blank=True, verbose_name=_("HSN Code")
    )
    current_stock = models.IntegerField(default=0, verbose_name=_("Current Stock"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        abstract = True
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")

    def __str__(self) -> str:
        return f"{self.name} ({self.price})"


class AbstractInvoiceItemEntry(BaseModel):
    """
    Abstract model snapshot of each line item inside an invoice.
    """

    invoice: "AbstractInvoice" = models.ForeignKey(
        settings.INVOICES_INVOICE_MODEL,
        on_delete=models.CASCADE,
        related_name="item_entries",
        verbose_name=_("Invoice"),
    )
    item: AbstractInvoiceItem = models.ForeignKey(
        settings.INVOICES_INVOICE_ITEM_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_entries",
        verbose_name=_("Catalog Item"),
        help_text=_("Optional reference to source catalog item."),
    )
    item_name = models.CharField(max_length=255, verbose_name=_("Item Name Snapshot"))
    item_description = models.TextField(
        null=True, blank=True, verbose_name=_("Item Description Snapshot")
    )
    HSN_code = models.CharField(
        max_length=64, null=True, blank=True, verbose_name=_("HSN Code Snapshot")
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name=_("Unit Price Snapshot"),
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name=_("Quantity"),
    )

    class Meta:
        abstract = True
        verbose_name = _("Invoice Item Entry")
        verbose_name_plural = _("Invoice Item Entries")

    def __str__(self) -> str:
        return f"{self.item_name} x {self.quantity} ({self.invoice})"

    def snapshot_item_data(self):
        """
        Snapshot/Copy needed data from InvoiceItem
        """
        if not self.item:
            return

        if not self.item_name and self.item:
            self.item_name = self.item.name

        if not self.item_description and self.item:
            self.item_description = self.item.description

        if not self.HSN_code and self.item:
            self.HSN_code = self.item.HSN_code

        if self.price is None and self.item:
            self.price = self.item.price

    def save(self, *args, **kwargs):
        """Auto-populate snapshot data from referenced item if not explicitly supplied."""

        self.snapshot_item_data()

        super().save(*args, **kwargs)

    @cached_property
    def total_price(self) -> Decimal:
        """Calculate line item base amount (unit price * quantity)."""
        unit_price = self.price if self.price is not None else Decimal("0.00")
        qty = self.quantity if self.quantity is not None else Decimal("0.00")
        return unit_price * qty

    @cached_property
    def total_fee_amount(self) -> Decimal:
        """Calculate total fees/taxes applied to this entry."""
        return sum((fee.fee_amount for fee in self.fees.all()), Decimal("0.00"))

    @cached_property
    def grand_total(self) -> Decimal:
        """Calculate grand total for this line item including fees/taxes."""
        return self.total_price + self.total_fee_amount


class AbstractInvoiceItemFee(BaseModel):
    """
    Abstract model snapshot of a fee or tax applied on an invoiced line item.
    """

    item_entry: "AbstractInvoiceItemEntry" = models.ForeignKey(
        settings.INVOICES_INVOICE_ITEM_ENTRY_MODEL,
        on_delete=models.CASCADE,
        related_name="fees",
        verbose_name=_("Invoice Item Entry"),
    )
    rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Rate (%)"),
        help_text=_("Rate percentage applied to the line entry amount."),
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Description / Fee Name"),
    )
    auto_applied = models.BooleanField(
        default=False,
        verbose_name=_("Auto Applied"),
        help_text=_("Whether this tax/fee was automatically computed and attached."),
    )

    class Meta:
        abstract = True
        verbose_name = _("Invoice Item Fee")
        verbose_name_plural = _("Invoice Item Fees")

    def __str__(self) -> str:
        return f"{self.description or 'Fee'} ({self.rate}%) - {self.item_entry}"

    @cached_property
    def fee_amount(self) -> Decimal:
        """Calculate concrete monetary amount for this fee/tax percentage."""
        base_amount = self.item_entry.total_price
        return (self.rate / Decimal("100.00")) * base_amount
