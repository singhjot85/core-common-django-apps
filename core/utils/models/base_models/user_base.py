from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from core.utils.models.base_models.base import BaseModel


class BaseUserModel(BaseModel):
    """Base user model providing standard UUID, timestamps, soft-delete,
    and phone/verification fields for user implementations.

    Attributes:
        phone_number (CharField): Phone number of user, unique and optional.
        is_phone_verified (BooleanField): Flag for phone verification status.
        is_email_verified (BooleanField): Flag for email verification status.
    """

    phone_number = PhoneNumberField(
        null=True,
        blank=True,
        unique=True,
        verbose_name=_("Phone Number"),
    )
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is Phone Verified"),
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name=_("Is Email Verified"),
    )

    class Meta:
        abstract = True

    @property
    def full_name(self) -> str:
        """Return the combined first and last name, or username."""
        first = getattr(self, "first_name", "") or ""
        last = getattr(self, "last_name", "") or ""
        name = f"{first} {last}".strip()
        return name or getattr(self, "username", "") or str(self.pk)
