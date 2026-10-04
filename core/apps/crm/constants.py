from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomerTypeChoices(models.TextChoices):
    """Customer entity type choices."""

    INDIVIDUAL = "individual", _("Individual")
    BUSINESS = "business", _("Business / Corporate")


class CustomerStatusChoices(models.TextChoices):
    """Customer onboarding and account status choices."""

    LEAD = "lead", _("Lead")
    PROSPECT = "prospect", _("Prospect")
    ONBOARDING = "onboarding", _("Onboarding")
    ACTIVE = "active", _("Active")
    INACTIVE = "inactive", _("Inactive")
    SUSPENDED = "suspended", _("Suspended")


class ContactTypeChoices(models.TextChoices):
    """Contact channel type choices."""

    PRIMARY = "primary", _("Primary")
    SECONDARY = "secondary", _("Secondary")
    WORK = "work", _("Work")
    PERSONAL = "personal", _("Personal")
    OTHER = "other", _("Other")


class AddressTypeChoices(models.TextChoices):
    """Physical and mailing address type choices."""

    PERMANENT = "permanent", _("Permanent")
    CURRENT = "current", _("Current / Residential")
    BILLING = "billing", _("Billing")
    SHIPPING = "shipping", _("Shipping")
    OFFICE = "office", _("Office / Business")
    OTHER = "other", _("Other")


class IdentityTypeChoices(models.TextChoices):
    """Government and regulatory identification document choices."""

    AADHAAR = "aadhaar", _("Aadhaar Card")
    PAN = "pan", _("PAN Card")
    DRIVING_LICENSE = "driving_license", _("Driving License")
    PASSPORT = "passport", _("Passport")
    VOTER_ID = "voter_id", _("Voter ID")
    GSTIN = "gstin", _("GSTIN")
    CIN = "cin", _("CIN")
    OTHER = "other", _("Other")


class PreferenceDataTypeChoices(models.TextChoices):
    """Data types supported for customer preference configuration."""

    BOOLEAN = "bool", _("Boolean")
    CHOICES = "choices", _("Single Choices")
    MULTI_SELECT = "multi_select", _("Multi-Select")
    TEXT = "text", _("Text")
    NUMBER = "number", _("Number")
