from django.db import models
from django.utils.translation import gettext_lazy as _


class IntegrationKeyChoices(models.TextChoices):
    """
    Service category keys managed by the integrations framework.
    """

    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    PAYMENT = "payment", _("Payment")
    MAPS = "maps", _("Maps")
    WEBHOOK = "webhook", _("Webhook")
    OTHER = "other", _("Other")


class CredentialsNameChoices(models.TextChoices):
    """
    Standard provider names for credentials management.
    """

    TWILIO = "twilio", _("Twilio")
    SENDGRID = "sendgrid", _("SendGrid")
    AWS_SES = "aws_ses", _("AWS SES")
    AWS_SNS = "aws_sns", _("AWS SNS")
    RAZORPAY = "razorpay", _("Razorpay")
    STRIPE = "stripe", _("Stripe")
    GOOGLE_MAPS = "google_maps", _("Google Maps")
    CUSTOM = "custom", _("Custom / Generic")
