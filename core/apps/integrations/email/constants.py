from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailLogStatusChoices(models.TextChoices):
    """
    Delivery status choices for email logs.
    """

    QUEUED = "queued", _("Queued")
    IN_PROGRESS = "in_progress", _("In Progress")
    SUCCESS = "succeded", _("Succeded")
    FAILED = "failed", _("Failed")


class EmailTemplateInterfaceTypeChoices(models.TextChoices):
    """
    Template interface categories for email templates.
    """

    GENERAL = "general", _("General")
    AUTH = "auth", _("Authentication")
    NOTIFICATION = "notification", _("Notification")
    INVOICE = "invoice", _("Invoice")
