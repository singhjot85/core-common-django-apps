from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

from apps.tenants.constants import TenantContactInfoChoices
from utils.models import BaseModel


class Tenants(TenantMixin, BaseModel):
    """
    Tenant's and their schema's
    """

    auto_create_schema = False

    label = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    public_id = models.CharField(max_length=124, null=True, blank=True)

    def __str__(self):
        return "%s - %s", self.label, self.public_id

    def save(self, verbosity=1, *args, **kwargs):
        """
        Schema migration is a slow process, and even slower when migrations grow in number
        So using a seperate thread (async thread) to create schema's instead of blocking main thread.
        """
        # Save the model instance first
        super().save(verbosity, *args, **kwargs)

        # queue a task to create schema
        queue_task( # noqa: F821
            TaskNames.MIGRATE_SCHEMA, # noqa: F821
            schema_name=self.schema_name,
            is_active=self.is_active,
            public_id=self.public_id,
        )


class Domain(DomainMixin, BaseModel):
    """
    Backend Domains for tenants
    """

    label = models.CharField(max_length=124, null=True, blank=True)


class TenantContactInfo(BaseModel):
    """
    Tenant Contact Info: email, phone, address
    """

    order = models.IntegerField(null=False, blank=False, default=1)
    contact_type = models.CharField(
        null=False, blank=False, choices=TenantContactInfoChoices.choices
    )
    tenant = models.ForeignKey(
        Tenants,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="contact_info",
    )
    value = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, null=True, blank=True
    )


class TenantBranding(BaseModel):
    """
    Implement this model after UI requierements, until then keeping it as abstract
    """

    tenant = models.OneToOneField(
        Tenants, on_delete=models.PROTECT, null=False, blank=False
    )
    details = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, null=True, blank=True
    )
