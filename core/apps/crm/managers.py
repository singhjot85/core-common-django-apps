"""
Custom managers and querysets for CRM domain entities.

Provides:
- CustomerQuerySet: Queryset methods for customer creation and lifecycle management.
- CustomerManager: Domain manager for customer records.
- CustomerAttributeManager: Attribute manager for single-primary constraints (phones, emails, addresses).
"""

import typing
import uuid

from django.db import models, transaction

from core.apps.crm.constants import CustomerStatusChoices, CustomerTypeChoices

if typing.TYPE_CHECKING:
    from core.apps.crm.models_abstract import AbstractCustomer
    from core.apps.users.models_abstract import AbstractUser


class CustomerQuerySet(models.QuerySet):
    """
    QuerySet providing domain-specific queries and lifecycle actions for customers.
    """

    def get_or_create_for_user(
        self,
        user: "AbstractUser",
        status: str = CustomerStatusChoices.ONBOARDING,
        **extra_kwargs: typing.Any,
    ) -> tuple["AbstractCustomer", bool]:
        """
        Retrieve or create a customer profile linked to the specified user.

        If a customer does not exist for the user, creates one with default individual
        type, active state, and onboarding status. If the user has an email or phone number,
        primary email and phone records are automatically created and associated with the
        customer in the same database transaction.

        Side effects:
            - Inserts a new customer record within an atomic database transaction.
            - Inserts linked primary email/phone records if user has contact details.

        Args:
            user (AbstractUser): User instance for which the customer is to be created.
            status (str, optional): Status of the customer getting created. Defaults to
                ``CustomerStatusChoices.ONBOARDING``.
            **extra_kwargs: Extra keyword arguments for contact verification:
                - ``email_verified`` (bool, optional): Verification status for the created email.
                - ``phone_verified`` (bool, optional): Verification status for the created phone.

        Returns:
            tuple[AbstractCustomer, bool]: A tuple of (customer, created), where customer is the
            linked profile instance and created indicates whether a new record was inserted.
        """
        defaults = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "customer_type": CustomerTypeChoices.INDIVIDUAL.value,
            "status": status,
            "is_active": True,
        }

        with transaction.atomic():
            customer, created = self.get_or_create(user=user, defaults=defaults)

            if email := getattr(user, "email", None):
                verified = extra_kwargs.get("email_verified", False)
                customer.emails.get_or_create(
                    email=email,
                    defaults={"is_primary": True, "is_verified": verified},
                )

            if phone := getattr(user, "phone_number", None):
                verified = extra_kwargs.get("phone_verified", False)
                customer.phones.get_or_create(
                    phone=phone,
                    defaults={"is_primary": True, "is_verified": verified},
                )

        return customer, created


class CustomerManager(models.Manager.from_queryset(queryset_class=CustomerQuerySet)):
    """
    Manager for Customer models, exposing domain-specific queries and factory methods.
    """


class CustomerAttributeManager(
    models.Manager.from_queryset(queryset_class=models.QuerySet)
):
    """
    Manager for customer-related attributes such as Phone, Email, and Address.

    Enforces single-primary record semantics per customer across attribute types.
    """

    def get_primary(
        self, customer: typing.Union["models.Model", uuid.UUID, str]
    ) -> typing.Optional[models.Model]:
        """
        Return the single primary record for the specified customer.

        Args:
            customer (models.Model | uuid.UUID | str): Customer instance or customer primary key.

        Returns:
            models.Model | None: The active primary attribute record, or None if no primary is set.
        """
        return self.filter(customer=customer, is_primary=True).first()

    def set_primary(
        self,
        attribute: typing.Union[models.Model, uuid.UUID, str],
        customer: typing.Optional[typing.Union["models.Model", uuid.UUID, str]] = None,
    ) -> models.Model:
        """
        Set the specified record as primary and unset primary on all siblings.

        Executes an atomic database transaction that resets ``is_primary=False`` on
        all other active attribute records belonging to the customer, and then updates
        the target record to ``is_primary=True``.

        Side effects:
            - Updates sibling attribute rows in the database to ``is_primary=False``.
            - Updates the target row to ``is_primary=True``.

        Args:
            attribute (models.Model | uuid.UUID | str): Attribute instance or primary key.
            customer (models.Model | uuid.UUID | str, optional): Customer instance or ID.
                Inferred from ``attribute.customer`` if omitted.

        Returns:
            models.Model: The updated attribute instance with ``is_primary=True``.
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
