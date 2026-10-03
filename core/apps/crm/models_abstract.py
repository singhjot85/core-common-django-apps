import typing

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.apps.crm.constants import (
    ContactTypeChoices,
    CustomerStatusChoices,
    CustomerTypeChoices,
    IdentityTypeChoices,
    PreferenceDataTypeChoices,
)
from core.apps.crm.managers import CustomerAttributeManager
from core.utils.models import AbstractAddress, AbstractParty, BaseModel


class AbstractCustomer(BaseModel, AbstractParty):
    """
    Abstract Customer model for onboarding and managing customers.
    """

    customer_type = models.CharField(
        max_length=32,
        choices=CustomerTypeChoices.choices,
        default=CustomerTypeChoices.INDIVIDUAL,
    )
    status = models.CharField(
        max_length=32,
        choices=CustomerStatusChoices.choices,
        default=CustomerStatusChoices.LEAD,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, null=True, blank=True)
    details = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.full_name or str(self.pk)

    @property
    def primary_phone(self) -> typing.Optional["AbstractCustomerPhone"]:
        """Return the primary phone instance for the customer."""
        return self.phones.filter(is_primary=True).first()

    @property
    def primary_email(self) -> typing.Optional["AbstractCustomerEmail"]:
        """Return the primary email instance for the customer."""
        return self.emails.filter(is_primary=True).first()

    @property
    def primary_address(self) -> typing.Optional["AbstractCustomerAddress"]:
        """Return the primary address instance for the customer."""
        return self.addresses.filter(is_primary=True).first()


class AbstractCustomerPhone(BaseModel):
    """
    Abstract model for Customer Phone Numbers.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name="phones",
    )
    phone = models.CharField(max_length=32)
    phone_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Phone"
        verbose_name_plural = "Customer Phones"

    def __str__(self):
        return f"{self.phone} ({self.customer})"

    def save(self, *args, **kwargs):
        """Save phone and ensure a single primary phone per customer."""
        if self.is_primary and self.customer_id:
            self.__class__.objects.filter(customer_id=self.customer_id).exclude(
                pk=self.pk
            ).filter(is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractCustomerEmail(BaseModel):
    """
    Abstract model for Customer Email Addresses.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name="emails",
    )
    email = models.EmailField(max_length=255)
    email_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PRIMARY,
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Email"
        verbose_name_plural = "Customer Emails"

    def __str__(self):
        return f"{self.email} ({self.customer})"

    def save(self, *args, **kwargs):
        """Save email and ensure a single primary email per customer."""
        if self.is_primary and self.customer_id:
            self.__class__.objects.filter(customer_id=self.customer_id).exclude(
                pk=self.pk
            ).filter(is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractCustomerAddress(BaseModel, AbstractAddress):
    """
    Abstract model for Customer Addresses.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    is_primary = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"

    def __str__(self):
        return f"{self.full_address} ({self.customer})"

    def save(self, *args, **kwargs):
        """Save address and ensure a single primary address per customer."""
        if self.is_primary and self.customer_id:
            self.__class__.objects.filter(customer_id=self.customer_id).exclude(
                pk=self.pk
            ).filter(is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class AbstractCustomerIdentification(BaseModel):
    """
    Abstract model for Customer KYC and Identification records.
    Supports Generic Foreign Key (GFK) to attach identity verification details or document instances.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name="identifications",
    )
    identity_type = models.CharField(
        max_length=32,
        choices=IdentityTypeChoices.choices,
        default=IdentityTypeChoices.AADHAAR,
    )
    identity_number = models.CharField(max_length=128)

    # Generic Foreign Key (GFK) to link to any identity/document model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.CharField(max_length=255, null=True, blank=True)
    customer_identity = GenericForeignKey("content_type", "object_id")

    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Customer Identification"
        verbose_name_plural = "Customer Identifications"

    def __str__(self):
        return f"{self.get_identity_type_display()}: {self.identity_number} ({self.customer})"


class AbstractCustomerPreferenceType(BaseModel):
    """
    Abstract model defining customer preference types and schemas.
    """

    code = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    data_type = models.CharField(
        max_length=32,
        choices=PreferenceDataTypeChoices.choices,
        default=PreferenceDataTypeChoices.BOOLEAN,
    )
    default_value = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)
    values = models.JSONField(
        default=list,
        blank=True,
        encoder=DjangoJSONEncoder,
        help_text="Allowed choices/options for choice-based preference types.",
    )

    class Meta:
        abstract = True
        verbose_name = "Customer Preference Type"
        verbose_name_plural = "Customer Preference Types"

    def __str__(self):
        return f"{self.label} ({self.code})"

    def clean(self):
        """Validate default_value against data_type."""
        if (
            self.data_type == PreferenceDataTypeChoices.BOOLEAN
            and self.default_value is not None
        ):
            if not isinstance(self.default_value, bool):
                raise ValidationError(
                    "default_value must be a boolean for bool data_type."
                )
        elif (
            self.data_type == PreferenceDataTypeChoices.CHOICES
            and self.default_value is not None
        ):
            if self.values and self.default_value not in self.values:
                raise ValidationError(
                    "default_value must be one of the allowed values."
                )
        elif (
            self.data_type == PreferenceDataTypeChoices.MULTI_SELECT
            and self.default_value is not None
        ):
            if not isinstance(self.default_value, list):
                raise ValidationError(
                    "default_value must be a list for multi-select data_type."
                )
            if self.values and not all(v in self.values for v in self.default_value):
                raise ValidationError(
                    "All default_value items must be in allowed values."
                )


class AbstractCustomerPreference(BaseModel):
    """
    Abstract model storing customer preferences.
    """

    customer = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    preference_type = models.ForeignKey(
        settings.CRM_CUSTOMER_PREFERENCE_TYPE_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_preferences",
    )
    value = models.JSONField(null=True, blank=True, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Customer Preference"
        verbose_name_plural = "Customer Preferences"
        unique_together = [("customer", "preference_type")]

    def __str__(self):
        return f"{self.customer} - {self.preference_type}: {self.value}"

    def clean(self):
        """Validate value against preference_type data_type and allowed values."""
        if not self.preference_type_id:
            return
        pref_type = self.preference_type
        if (
            pref_type.data_type == PreferenceDataTypeChoices.BOOLEAN
            and self.value is not None
        ):
            if not isinstance(self.value, bool):
                raise ValidationError("value must be a boolean.")
        elif (
            pref_type.data_type == PreferenceDataTypeChoices.CHOICES
            and self.value is not None
        ):
            if pref_type.values and self.value not in pref_type.values:
                raise ValidationError(f"value must be one of: {pref_type.values}")
        elif (
            pref_type.data_type == PreferenceDataTypeChoices.MULTI_SELECT
            and self.value is not None
        ):
            if not isinstance(self.value, list):
                raise ValidationError("value must be a list for multi-select.")
            if pref_type.values and not all(v in pref_type.values for v in self.value):
                raise ValidationError(
                    f"All selected items must be in: {pref_type.values}"
                )
