import typing
import uuid

from django.db import models, transaction

if typing.TYPE_CHECKING:
    from django.db.models import Model


class CustomerAttributeManager(
    models.Manager.from_queryset(queryset_class=models.QuerySet)
):
    """
    Manager for customer-related attributes such as Phone, Email, and Address.
    Provides utility methods to get and set the primary record per customer.
    """

    def get_primary(
        self, customer: typing.Union["Model", uuid.UUID, str]
    ) -> typing.Optional[models.Model]:
        """
        Get the primary record for the specified customer.
        """
        return self.filter(customer=customer, is_primary=True).first()

    def set_primary(
        self,
        instance_or_pk: typing.Union[models.Model, uuid.UUID, str],
        customer: typing.Optional[typing.Union["Model", uuid.UUID, str]] = None,
    ) -> models.Model:
        """
        Set the specified instance as the primary record for its customer,
        and unset is_primary for all other records of that customer.
        """
        if isinstance(instance_or_pk, models.Model):
            instance = instance_or_pk
            resolved_customer = customer or instance.customer
        else:
            instance = self.get(pk=instance_or_pk)
            resolved_customer = customer or instance.customer

        with transaction.atomic():
            self.filter(customer=resolved_customer).exclude(pk=instance.pk).filter(
                is_primary=True
            ).update(is_primary=False)
            if not instance.is_primary:
                instance.is_primary = True
                instance.save(update_fields=["is_primary"])

        return instance
