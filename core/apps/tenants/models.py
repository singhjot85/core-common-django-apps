import uuid

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from model_utils.models import StatusModel

from core.apps.tenants.constants import TenantContactInfoChoices, TenantStatus
from core.apps.tenants.tasks import provision_tenant_schema
from core.utils.models import BaseModel
from core.utils.tasks import queue_task


class Tenants(TenantMixin, BaseModel, StatusModel):
    """
    Tenant's and their schema's
    """

    auto_create_schema = False

    status = TenantStatus.choices
    label = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    public_id = models.CharField(max_length=124, null=True, blank=True)

    def __str__(self):
        return "%s - %s", self.label, self.public_id

    def generate_public_id(self, retry: int = 0):
        """
        Generate public id for current tenant.
        """
        if retry >= 5:
            raise Exception(f"Error Creating unique {self.__name__}")

        public_id = f"Tenant-{self.label}-{uuid.uuid4().hex}"

        try:
            self.objects.get(public_id)
        except self.DoesNotExist:
            self.public_id = public_id
            return self.public_id

        retry += 1
        self.generate_public_id(retry)

    def save(self, verbosity=1, *args, **kwargs):
        """
        Schema migration is a slow process, and even slower when migrations grow in number
        So using a seperate thread (async thread) to create schema's instead of blocking main thread.
        """
        self.generate_public_id()

        # Save the model instance first
        super().save(verbosity, *args, **kwargs)

        # queue a task to create schema
        queue_task(
            provision_tenant_schema,
            on_commit=True,
            idempotency_key=str(self.pk),
            task_kwargs={"tenant_id": str(self.pk)},
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
