from django.conf import settings
from django.contrib.auth.models import AbstractUser as DjangoAbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.apps.users import app_settings
from core.apps.users.constants import (
    OTPChannelChoices,
    OTPDeliveryStatusChoices,
    OTPPurposeChoices,
    SocialProviderChoices,
)
from core.apps.users.managers import UserManager
from core.utils.models import BaseLogModel, BaseModel

# Dynamically resolve BaseUserModel from app_settings
BaseUserModel = app_settings.BASE_USER_MODEL


class AbstractUser(DjangoAbstractUser, BaseUserModel):
    """
    Abstract user model inheriting Django's AbstractUser for standard auth
    and Core's BaseUserModel for UUID, timestamps, soft-delete, and phone attributes.
    """

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        blank=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(
        _("email address"),
        blank=True,
        null=True,
    )

    objects = UserManager()

    class Meta(DjangoAbstractUser.Meta):
        abstract = True
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.username or self.email or self.phone_number or str(self.pk)

    @property
    def has_password(self) -> bool:
        """Check if user has an active, usable password set."""
        return self.has_usable_password()


class AbstractSocialAccount(BaseModel):
    """
    Abstract model linking third-party identity providers to a user.
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(
        max_length=32,
        choices=SocialProviderChoices.choices,
        verbose_name=_("Provider"),
    )
    uid = models.CharField(
        max_length=255,
        verbose_name=_("Provider UID"),
    )
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Extra Data"),
    )

    class Meta:
        abstract = True
        unique_together = [("provider", "uid")]
        verbose_name = _("Social Account")
        verbose_name_plural = _("Social Accounts")

    def __str__(self):
        return f"{self.get_provider_display()} ({self.uid}) - {self.user}"


class AbstractOTPLog(BaseLogModel):
    """
    Audit log for one-time password (OTP) dispatch and verification events.
    """

    STATUS = OTPDeliveryStatusChoices.choices

    recipient = models.CharField(
        max_length=255,
        verbose_name=_("Recipient Identifier"),
    )
    channel = models.CharField(
        max_length=16,
        choices=OTPChannelChoices.choices,
        verbose_name=_("Channel"),
    )
    purpose = models.CharField(
        max_length=16,
        choices=OTPPurposeChoices.choices,
        default=OTPPurposeChoices.LOGIN,
        verbose_name=_("Purpose"),
    )

    class Meta:
        abstract = True
        verbose_name = _("OTP Log")
        verbose_name_plural = _("OTP Logs")

    def __str__(self):
        return f"OTP to {self.recipient} [{self.channel}] - {self.status}"
