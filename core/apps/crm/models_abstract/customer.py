import typing

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.apps.crm.constants import (
    CustomerStatusChoices,
    CustomerTypeChoices,
)
from core.apps.crm.managers import CustomerManager
from core.utils.models import AbstractParty, BaseModel

if typing.TYPE_CHECKING:
    from core.apps.crm.models_abstract.customer_attributes import (
        AbstractCustomerAddress,
        AbstractCustomerEmail,
        AbstractCustomerPhone,
    )


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
        default=CustomerStatusChoices.ONBOARDING,
    )
    is_active = models.BooleanField(null=False, blank=False, default=True)
    date_of_birth = models.DateField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )

    objects: CustomerManager = CustomerManager()

    if typing.TYPE_CHECKING:
        phones = models.Manager["AbstractCustomerPhone"]
        emails = models.Manager["AbstractCustomerEmail"]
        addresses = models.Manager["AbstractCustomerAddress"]

    class Meta:
        abstract = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.full_name or str(self.pk)

    @property
    def primary_phone(self) -> typing.Optional["AbstractCustomerPhone"]:
        """
        Return the primary phone instance for the customer.

        Returns:
            AbstractCustomerPhone | None: The active primary phone record if set, else None.
        """
        return self.phones.filter(is_primary=True, is_removed=False).first()

    @property
    def primary_email(self) -> typing.Optional["AbstractCustomerEmail"]:
        """
        Return the primary email instance for the customer.

        Returns:
            AbstractCustomerEmail | None: The active primary email record if set, else None.
        """
        return self.emails.filter(is_primary=True, is_removed=False).first()

    @property
    def primary_address(self) -> typing.Optional["AbstractCustomerAddress"]:
        """
        Return the primary address instance for the customer.

        Returns:
            AbstractCustomerAddress | None: The active primary address record if set, else None.
        """
        return self.addresses.filter(is_primary=True, is_removed=False).first()
