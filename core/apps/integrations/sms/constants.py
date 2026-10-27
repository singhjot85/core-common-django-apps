from django.db import models
from django.utils.translation import gettext_lazy as _


class SMSLogStatusChoices(models.TextChoices):
    """
    Delivery status choices for SMS logs.
    """

    QUEUED = "queued", _("Queued")
    IN_PROGRESS = "in_progress", _("In Progress")
    SUCCESS = "succeded", _("Succeded")
    FAILED = "failed", _("Failed")


class SMSTemplateInterfaceTypeChoices(models.TextChoices):
    """
    Template interface categories for SMS messages.
    """

    GENERAL = "general", _("General")
    OTP = "otp", _("OTP Verification")
