from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class TenantTypeChoices(TextChoices):
    """ """

    ORGANIZATION = "organization", _("Organization")


class TenantStatus(TextChoices):
    """
    Tenant Status Choices
    """

    PROVISIONING = "provisioning", "Provisioning"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class TenantContactInfoChoices(TextChoices):
    """
    Tenant Contact Information Choices
    """

    EMAIL = "email", _("Email")
    ADDRESS = "address", _("Address")
    PHONE = "phone", _("phone")
