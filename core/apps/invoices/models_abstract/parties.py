import typing
from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.invoices.constants import ContactTypeChoices, PartyTypeChoices
from core.utils.models import AbstractParty, BaseModel


class AbstractInvoicePartyCategory(BaseModel):
    """
    Abstract model for categorization of invoice parties (e.g. VIP, Regular, Defaulter).
    """

    category_name = models.CharField(
        max_length=128, unique=True, verbose_name=_("Category Name")
    )
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))

    class Meta:
        abstract = True
        verbose_name = _("Invoice Party Category")
        verbose_name_plural = _("Invoice Party Categories")

    def __str__(self) -> str:
        return self.category_name


class AbstractInvoiceParty(BaseModel, AbstractParty):
    """
    Abstract snapshot model for a customer, supplier, or distributor invoiced on a bill.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_parties",
        verbose_name=_("Linked CRM Customer"),
        help_text=_("Optional reference to the source customer profile in CRM."),
    )
    party_type = models.CharField(
        max_length=32,
        choices=PartyTypeChoices.choices,
        default=PartyTypeChoices.CUSTOMER,
        verbose_name=_("Party Type"),
    )
    party_category = models.ForeignKey(
        settings.INVOICES_INVOICE_PARTY_CATEGORY_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parties",
        verbose_name=_("Party Category"),
    )
    pending_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Pending Balance"),
    )

    class Meta:
        abstract = True
        verbose_name = _("Invoice Party")
        verbose_name_plural = _("Invoice Parties")

    def __str__(self) -> str:
        return self.full_name or str(self.pk)

    @cached_property
    def primary_email(self) -> typing.Optional["AbstractInvoicePartyEmail"]:
        """Return the primary snapshotted email for this party."""
        return self.emails.first()

    @cached_property
    def primary_phone(self) -> typing.Optional["AbstractInvoicePartyPhone"]:
        """Return the primary snapshotted phone for this party."""
        return self.phones.first()


class AbstractInvoicePartyEmail(BaseModel):
    """
    Abstract snapshot model of a party's email address at time of invoicing.
    """

    invoice_party = models.ForeignKey(
        settings.INVOICES_INVOICE_PARTY_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name=_("Invoice Party"),
    )
    email = models.EmailField(verbose_name=_("Email Address"))
    email_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
        verbose_name=_("Email Type"),
    )

    class Meta:
        abstract = True
        verbose_name = _("Invoice Party Email")
        verbose_name_plural = _("Invoice Party Emails")

    def __str__(self) -> str:
        return f"{self.email} ({self.invoice_party})"


class AbstractInvoicePartyPhone(BaseModel):
    """
    Abstract snapshot model of a party's phone number at time of invoicing.
    """

    invoice_party = models.ForeignKey(
        settings.INVOICES_INVOICE_PARTY_MODEL,
        on_delete=models.CASCADE,
        related_name="phones",
        verbose_name=_("Invoice Party"),
    )
    phone = models.CharField(max_length=32, verbose_name=_("Phone Number"))
    phone_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
        verbose_name=_("Phone Type"),
    )

    class Meta:
        abstract = True
        verbose_name = _("Invoice Party Phone")
        verbose_name_plural = _("Invoice Party Phones")

    def __str__(self) -> str:
        return f"{self.phone} ({self.invoice_party})"
