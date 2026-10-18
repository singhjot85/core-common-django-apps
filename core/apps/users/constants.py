from django.db import models
from django.utils.translation import gettext_lazy as _


class SocialProviderChoices(models.TextChoices):
    """Supported third-party OAuth providers."""

    GOOGLE = "google", _("Google")
    APPLE = "apple", _("Apple")


class OTPChannelChoices(models.TextChoices):
    """Delivery channels for OTP codes."""

    PHONE = "phone", _("Phone (SMS)")
    EMAIL = "email", _("Email")


class OTPPurposeChoices(models.TextChoices):
    """Intent for generating/verifying an OTP code."""

    LOGIN = "login", _("Login")
    SIGNUP = "signup", _("Signup")
    VERIFY = "verify", _("Verification")


class OTPDeliveryStatusChoices(models.TextChoices):
    """Status lifecycle of an OTP dispatch log."""

    PENDING = "pending", _("Pending")
    SENT = "sent", _("Sent")
    FAILED = "failed", _("Failed")
    VERIFIED = "verified", _("Verified")
    EXPIRED = "expired", _("Expired")
