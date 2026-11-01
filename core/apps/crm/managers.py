import typing
import uuid

from django.db import models, transaction

from core.apps.crm import get_customer_email_model, get_customer_phone_model
from core.apps.crm.constants import CustomerStatusChoices, CustomerTypeChoices

if typing.TYPE_CHECKING:
    from core.apps.crm.models_abstract import AbstractCustomer
    from core.apps.users.models_abstract import AbstractUser


class CustomerQuerySet(models.QuerySet):
    """
    Queryset for CustomerManager
    """

    def get_or_create_for_user(
        self,
        user: "AbstractUser",
        status: str = CustomerStatusChoices.ONBOARDING,
        **extra_kwargs,
    ) -> "AbstractCustomer":
        """
        Create a customer for given user.

        Args:
            user (AbstractUser): User instance for which the customer is to be created.
            status (str): Status of the customer getting created
            **extra_kwargs: Extra kwargs for creation
                - email_verified (bool): Is the user email verified
                - phone_verified (bool): Is the user phone_number verified

        Returns:
            customer (AbstractCustomer): Customer instance created for given user.
        """
        defaults = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "customer_type": CustomerTypeChoices.INDIVIDUAL.value,
            "status": status,
            "is_active": True,
        }

        CustomerEmail = get_customer_email_model()
        CustomerPhone = get_customer_phone_model()

        with transaction.atomic():
            customer, created = self.get_or_create(user=user, defaults=defaults)

            if email := getattr(user, "email", None):
                verified = extra_kwargs.get("email_verified", False)
                CustomerEmail.objects.get_or_create(
                    customer=customer,
                    email=email,
                    defaults={"is_primary": True, "is_verified": verified},
                )

            if phone := getattr(user, "phone_number", None):
                verified = extra_kwargs.get("phone_verified", False)
                CustomerPhone.objects.get_or_create(
                    customer=customer,
                    phone=phone,
                    defaults={"is_primary": True, "is_verified": verified},
                )

        return customer, created


class CustomerManager(models.Manager.get_queryset(queryset_class=CustomerQuerySet)):
    """
    Manager for Customer model, create domain specific features.
    """


class CustomerAttributeManager(
    models.Manager.from_queryset(queryset_class=models.QuerySet)
):
    """
    Manager for customer-related attributes such as Phone, Email, and Address.
    Provides utility methods to get and set the primary record per customer.
    """

    def get_primary(
        self, customer: typing.Union["models.Model", uuid.UUID, str]
    ) -> typing.Optional[models.Model]:
        """
        Get the primary record for the specified customer.
        """
        return self.filter(customer=customer, is_primary=True).first()

    def set_primary(
        self,
        attribute: typing.Union[models.Model, uuid.UUID, str],
        customer: typing.Optional[typing.Union["models.Model", uuid.UUID, str]] = None,
    ) -> models.Model:
        """
        Set the specified instance as the primary record for its customer,
        and unset is_primary for all other records of that customer.
        """

        instance = (
            attribute if isinstance(attribute, models.Model) else self.get(pk=attribute)
        )
        resolved_customer = customer or instance.customer

        with transaction.atomic():
            self.filter(customer=resolved_customer).exclude(pk=instance.pk).filter(
                is_primary=True
            ).update(is_primary=False)
            if not instance.is_primary:
                instance.is_primary = True
                instance.save(update_fields=["is_primary"])

        return instance
