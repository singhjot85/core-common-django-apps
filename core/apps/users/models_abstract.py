"""
Abstract base models for authentication, identity linking, and OTP auditing.

Provides AbstractUser (inheriting Django auth and BaseModel soft-delete / timestamps),
AbstractSocialAccount for third-party SSO bindings, and AbstractOTPLog for delivery auditing.
"""

import logging
import typing

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

if typing.TYPE_CHECKING:
    from core.utils.models import BaseUserModel as AbstractUserModel

LOGGER = logging.getLogger(__name__)

# Dynamically resolve BaseUserModel from app_settings
BaseUserModel: type["AbstractUserModel"] = app_settings.BASE_USER_MODEL


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

    objects: UserManager = UserManager()

    class Meta(DjangoAbstractUser.Meta):
        abstract = True
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.get_full_name() or self.username or self.email or str(self.pk)

    @property
    def has_password(self) -> bool:
        """
        Check if user has an active, usable password set.

        Returns:
            bool: True if password is set and usable, False if unusable (e.g. OTP/SSO only).
        """
        return self.has_usable_password()

    @classmethod
    def create_system_user(cls) -> "AbstractUser":
        """
        Create or retrieve the system user without a usable password.

        Reserved for internal auditing, automated workers, and system actions.

        Side effects:
            - Inserts or updates system user record in database.
            - Sets an unusable password on the user.

        Returns:
            AbstractUser: The system user instance.
        """
        username = app_settings.SYSTEM_USER_USERNAME
        user = cls.objects.all_objects().filter(username=username).first()
        if not user:
            user = cls.objects.create(
                username=username,
                first_name="System",
                last_name="User",
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
        elif user.is_removed:
            user.is_removed = False
            user.save(update_fields=["is_removed"])

        if user.has_usable_password():
            user.set_unusable_password()
            user.save(update_fields=["password"])

        return user

    @classmethod
    def get_system_user(cls, create: bool = False) -> typing.Optional["AbstractUser"]:
        """
        Retrieve the internal system user used for auditing and system operations.

        Args:
            create (bool): If True and system user doesn't exist, create it. Defaults to False.

        Returns:
            AbstractUser | None: The system user instance, or None if not found and create is False.
        """
        username = app_settings.SYSTEM_USER_USERNAME
        try:
            user = cls.objects.filter(username=username).first()
            if not user and create:
                return cls.create_system_user()
            return user
        except Exception as e:
            LOGGER.warning(f"Failed to retrieve system user: {e}")
            return None

    @classmethod
    def system_user(cls) -> typing.Optional["AbstractUser"]:
        """
        Retrieve the cached or persisted system user instance.

        Returns:
            AbstractUser | None: The system user instance if found or created.
        """
        return cls.get_system_user()


class AbstractSocialAccount(BaseModel):
    """
    Abstract model linking third-party identity providers to a user.

    Relations:
        user (ForeignKey): Target user associated with the social credential.

    Attributes:
        provider (str): Social provider identifier (e.g. google, apple, meta).
        uid (str): Unique subject or account identifier assigned by the provider.
        extra_data (dict): JSON payload of claims and profile data from the provider.
    """

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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

    Attributes:
        recipient (str): Destination phone number or email address.
        channel (str): Delivery medium (sms, email, whatsapp).
        purpose (str): Functional purpose of the OTP (login, verification, password reset).
        status (str): Delivery lifecycle status (pending, sent, delivered, failed).
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
