from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentLogStatusChoices(models.TextChoices):
    """
    Operation status choices for payment logs.
    """

    QUEUED = "queued", _("Queued")
    IN_PROGRESS = "in_progress", _("In Progress")
    SUCCESS = "succeded", _("Succeded")
    FAILED = "failed", _("Failed")


class PaymentGatewayChoices(models.TextChoices):
    """
    Standard payment gateway provider options.
    """

    STRIPE = "stripe", _("Stripe")
    PAYPAL = "paypal", _("PayPal")
    MOCK = "mock", _("Mock Gateway")
    CUSTOM = "custom", _("Custom Gateway")
