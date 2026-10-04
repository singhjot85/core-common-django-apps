from django.db import models
from django.utils.translation import gettext_lazy as _


class PartyTypeChoices(models.TextChoices):
    """Classification for an invoiced party / entity."""

    CUSTOMER = "customer", _("Customer")
    DISTRIBUTOR = "distributor", _("Distributor")
    SUPPLIER = "supplier", _("Supplier")
    VENDOR = "vendor", _("Vendor")
    OTHER = "other", _("Other")


class ContactTypeChoices(models.TextChoices):
    """Contact channel classification (email / phone)."""

    PRIMARY = "primary", _("Primary")
    SECONDARY = "secondary", _("Secondary")
    BILLING = "billing", _("Billing")
    SUPPORT = "support", _("Support")
    WORK = "work", _("Work")
    PERSONAL = "personal", _("Personal")
    OTHER = "other", _("Other")


class OrganizationAssetTypeChoices(models.TextChoices):
    """Billing organization asset classification."""

    LOGO = "logo", _("Logo")
    SIGNATURE = "signature", _("Signature")
    STAMP = "stamp", _("Stamp")
    HEADER = "header", _("Header")
    FOOTER = "footer", _("Footer")
    OTHER = "other", _("Other")
