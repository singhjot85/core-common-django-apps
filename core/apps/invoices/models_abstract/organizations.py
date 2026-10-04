import typing
from functools import cached_property

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.invoices.constants import (
    ContactTypeChoices,
    OrganizationAssetTypeChoices,
)
from core.utils.models import BaseModel


class AbstractBillingOrganization(BaseModel):
    """
    Abstract Billing Organization model representing the entity issuing the invoice/bill.
    """

    organization_name = models.CharField(
        max_length=255, verbose_name=_("Organization Name")
    )
    billing_suffix = models.CharField(
        max_length=32,
        default="",
        blank=True,
        verbose_name=_("Billing Suffix"),
        help_text=_(
            "Optional suffix appended to invoice sequence numbers (e.g. /2026-27 or -INV)."
        ),
    )
    billing_start_sequence = models.PositiveBigIntegerField(
        default=1,
        verbose_name=_("Billing Start Sequence"),
        help_text=_("Initial sequence number for generated invoices."),
    )
    billing_current_sequence = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_("Billing Current Sequence"),
        help_text=_("Current sequence counter tracker for generated invoices."),
    )

    class Meta:
        abstract = True
        verbose_name = _("Billing Organization")
        verbose_name_plural = _("Billing Organizations")

    def __str__(self) -> str:
        return self.organization_name

    @cached_property
    def primary_email(self) -> typing.Optional["AbstractOrganizationEmail"]:
        """Return the primary email instance for the billing organization."""
        return self.emails.filter(is_primary=True).first() or self.emails.first()

    @cached_property
    def primary_phone(self) -> typing.Optional["AbstractOrganizationPhone"]:
        """Return the primary phone instance for the billing organization."""
        return self.phones.filter(is_primary=True).first() or self.phones.first()

    @cached_property
    def financials(self) -> typing.Optional["AbstractOrganizationFinancials"]:
        """Return the financial data record for the billing organization."""
        return getattr(self, "financial_data", None)

    @cached_property
    def logo(self) -> typing.Optional["AbstractOrganizationAssets"]:
        """Return the primary logo asset for the billing organization."""
        return (
            self.assets.filter(asset_type=OrganizationAssetTypeChoices.LOGO).first()
            or self.assets.first()
        )

    def generate_next_invoice_number(self) -> str:
        """
        Generate and persist the next formatted invoice number for this organization.
        """
        next_seq = max(self.billing_start_sequence, self.billing_current_sequence + 1)
        self.billing_current_sequence = next_seq
        self.save(update_fields=["billing_current_sequence", "modified"])
        suffix = self.billing_suffix or ""
        return f"{next_seq}{suffix}"


class AbstractOrganizationEmail(BaseModel):
    """
    Abstract model for email addresses belonging to a Billing Organization.
    """

    organization: AbstractBillingOrganization = models.ForeignKey(
        settings.INVOICES_BILLING_ORGANIZATION_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
        verbose_name=_("Billing Organization"),
    )
    email = models.EmailField(verbose_name=_("Email Address"))
    type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
        verbose_name=_("Email Type"),
    )
    is_primary = models.BooleanField(default=False, verbose_name=_("Is Primary"))

    class Meta:
        abstract = True
        verbose_name = _("Organization Email")
        verbose_name_plural = _("Organization Emails")

    def __str__(self) -> str:
        return f"{self.email} ({self.organization})"

    def save(self, *args, **kwargs):
        """Ensure only one primary email per billing organization."""
        if self.is_primary and self.organization_id:
            self.__class__.objects.filter(organization_id=self.organization_id).exclude(
                pk=self.pk
            ).filter(is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractOrganizationPhone(BaseModel):
    """
    Abstract model for phone numbers belonging to a Billing Organization.
    """

    organization: AbstractBillingOrganization = models.ForeignKey(
        settings.INVOICES_BILLING_ORGANIZATION_MODEL,
        on_delete=models.CASCADE,
        related_name="phones",
        verbose_name=_("Billing Organization"),
    )
    phone = models.CharField(max_length=32, verbose_name=_("Phone Number"))
    type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
        verbose_name=_("Phone Type"),
    )
    is_primary = models.BooleanField(default=False, verbose_name=_("Is Primary"))

    class Meta:
        abstract = True
        verbose_name = _("Organization Phone")
        verbose_name_plural = _("Organization Phones")

    def __str__(self) -> str:
        return f"{self.phone} ({self.organization})"

    def save(self, *args, **kwargs):
        """Ensure only one primary phone per billing organization."""
        if self.is_primary and self.organization_id:
            self.__class__.objects.filter(organization_id=self.organization_id).exclude(
                pk=self.pk
            ).filter(is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractOrganizationFinancials(BaseModel):
    """
    Abstract model for financial, statutory, and tax identification details of a Billing Organization.
    """

    organization: AbstractBillingOrganization = models.OneToOneField(
        settings.INVOICES_BILLING_ORGANIZATION_MODEL,
        on_delete=models.CASCADE,
        related_name="financial_data",
        verbose_name=_("Billing Organization"),
    )
    aadhar = models.CharField(
        max_length=32, null=True, blank=True, verbose_name=_("Aadhaar")
    )
    GSTIN = models.CharField(
        max_length=32, null=True, blank=True, verbose_name=_("GSTIN")
    )
    PAN = models.CharField(max_length=32, null=True, blank=True, verbose_name=_("PAN"))

    class Meta:
        abstract = True
        verbose_name = _("Organization Financials")
        verbose_name_plural = _("Organization Financials")

    def __str__(self) -> str:
        return f"Financials ({self.organization})"


class AbstractOrganizationAssets(BaseModel):
    """
    Abstract model for logos, signatures, stamps, and assets of a Billing Organization.
    """

    billing_org: AbstractBillingOrganization = models.ForeignKey(
        settings.INVOICES_BILLING_ORGANIZATION_MODEL,
        on_delete=models.CASCADE,
        related_name="assets",
        verbose_name=_("Billing Organization"),
    )
    asset = models.FileField(
        upload_to="invoices/organization_assets/",
        verbose_name=_("Asset File"),
    )
    name = models.CharField(max_length=128, verbose_name=_("Asset Name"))
    asset_type = models.CharField(
        max_length=32,
        choices=OrganizationAssetTypeChoices.choices,
        default=OrganizationAssetTypeChoices.LOGO,
        verbose_name=_("Asset Type"),
    )
    description = models.TextField(null=True, blank=True, verbose_name=_("Description"))

    class Meta:
        abstract = True
        verbose_name = _("Organization Asset")
        verbose_name_plural = _("Organization Assets")

    def __str__(self) -> str:
        return f"{self.name} ({self.billing_org})"
