import typing

from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.apps.crm.constants import AddressTypeChoices, ContactTypeChoices
from core.apps.crm.managers import CustomerAttributeManager
from core.utils.models import AbstractAddress, BaseModel

if typing.TYPE_CHECKING:
    from core.apps.crm.models_abstract.customer import AbstractCustomer


class AbstractCustomerPhone(BaseModel):
    """
    Abstract model for Customer Phone Numbers.
    """

    customer: "AbstractCustomer" = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="phones",
    )
    phone = PhoneNumberField()
    phone_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PERSONAL,
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Phone"
        verbose_name_plural = "Customer Phones"
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_primary=True, is_removed=False),
                name="unique_available_primary_phone_per_customer",
            )
        ]

    def __str__(self):
        return f"{self.phone} ({self.customer})"


class AbstractCustomerEmail(BaseModel):
    """
    Abstract model for Customer Email Addresses.
    """

    customer: "AbstractCustomer" = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="emails",
    )
    email = models.EmailField(max_length=255)
    email_type = models.CharField(
        max_length=32,
        choices=ContactTypeChoices.choices,
        default=ContactTypeChoices.PERSONAL,
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Email"
        verbose_name_plural = "Customer Emails"
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_primary=True, is_removed=False),
                name="unique_available_primary_email_per_customer",
            )
        ]

    def __str__(self):
        return f"{self.email} ({self.customer})"


class AbstractCustomerAddress(BaseModel, AbstractAddress):
    """
    Abstract model for Customer Addresses.
    """

    customer: "AbstractCustomer" = models.ForeignKey(
        settings.CRM_CUSTOMER_MODEL,
        on_delete=models.PROTECT,
        related_name="addresses",
    )
    address_type = models.CharField(
        null=True,
        blank=True,
        choices=AddressTypeChoices.choices,
        default=AddressTypeChoices.PERMANENT.value,
    )
    is_primary = models.BooleanField(default=False)

    objects: CustomerAttributeManager = CustomerAttributeManager()

    class Meta:
        abstract = True
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_primary=True, is_removed=False),
                name="unique_available_primary_address_per_customer",
            )
        ]

    def __str__(self):
        return f"{self.full_address} ({self.customer})"
