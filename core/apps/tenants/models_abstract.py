import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from model_utils.models import StatusModel

from core.apps.tenants import get_tenant_model
from core.apps.tenants.constants import TenantContactInfoChoices, TenantStatus
from core.apps.tenants.tasks import provision_tenant_schema
from core.utils.models import BaseModel
from core.utils.tasks import queue_task


class AbstractTenants(TenantMixin, BaseModel, StatusModel):
    """
    Abstract model for Tenant's and their schema's.
    This model is intended to be inherited by other models and should not be used directly.
    """

    auto_create_schema = False

    STATUS = TenantStatus.choices
    label = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    public_id = models.CharField(max_length=124, null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return f"{self.label} - {self.public_id}"

    def generate_public_id(self, retry: int = 0):
        """
        Generate public id for current tenant.
        """
        Tenant = get_tenant_model()

        if retry >= 5:
            raise Exception(f"Error Creating unique {self.__class__.__name__}")

        public_id = f"Tenant-{self.label}-{uuid.uuid4().hex}"

        tenants = Tenant.objects.filter(public_id=public_id)
        if tenants.count() <= 0:
            self.public_id = public_id
            return self.public_id

        retry += 1
        return self.generate_public_id(retry)

    def save(self, verbosity=1, *args, **kwargs):
        """
        Schema migration is a slow process, and even slower when migrations grow in number.
        Use an async background task to create schemas instead of blocking the main thread.
        """
        is_new = self._state.adding or self.pk is None
        if not self.public_id:
            self.generate_public_id()

        # Save the model instance first
        super().save(verbosity, *args, **kwargs)

        # Only queue schema provisioning on initial creation
        if is_new and self.status != TenantStatus.READY:
            queue_task(
                provision_tenant_schema,
                on_commit=True,
                idempotency_key=str(self.pk),
                task_kwargs={"tenant_id": str(self.pk)},
            )


class AbstractDomain(DomainMixin, BaseModel):
    """
    Abstract model for Backend Domains for tenants.
    This model is intended to be inherited by other models and should not be used directly.
    """

    label = models.CharField(max_length=124, null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = "Domain"
        verbose_name_plural = "Domains"


class AbstractTenantContactInfo(BaseModel):
    """
    Abstract model for Tenant Contact Information.
    This model is intended to be inherited by other models and should not be used directly.
    """

    order = models.IntegerField(null=False, blank=False, default=1)
    tenant = models.ForeignKey(
        settings.TENANTS_TENANT_MODEL,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="contact_info",
    )
    contact_type = models.CharField(
        null=False, blank=False, choices=TenantContactInfoChoices.choices
    )
    contact_info = models.JSONField(
        encoder=DjangoJSONEncoder,
        default=dict,
        blank=True,
        null=True,
        help_text="Contact information for the tenant in JSON format.",
    )

    class Meta:
        abstract = True
        verbose_name = "Tenant Contact Info"
        verbose_name_plural = "Tenant Contact Infos"


class AbstractTenantBranding(BaseModel):
    """
    Abstract model for Tenant Branding.
    This model is intended to be inherited by other models and should not be used directly.
    """

    tenant = models.OneToOneField(
        settings.TENANTS_TENANT_MODEL,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="branding",
    )
    details = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, null=True, blank=True
    )

    class Meta:
        abstract = True
        verbose_name = "Tenant Branding"
        verbose_name_plural = "Tenant Brandings"
