import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from django_tenants.utils import schema_context
from model_utils.models import StatusModel
from rest_framework.exceptions import ValidationError

from core.apps.configurations import get_configuration_model
from core.apps.tenants import get_tenant_model
from core.apps.tenants.constants import TenantContactInfoChoices, TenantStatus
from core.apps.tenants.tasks import provision_tenant_schema
from core.utils.models import BaseModel, BaseVersioningModel
from core.utils.tasks import queue_task


class AbstractTenants(TenantMixin, BaseModel, StatusModel):
    """
    Abstract model for Tenant's and their schema's.
    This model is intended to be inherited by other models and should not be used directly.
    """

    auto_create_schema = False

    status = TenantStatus.choices
    label = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    public_id = models.CharField(max_length=124, null=True, blank=True)

    class Meta:
        abstract = True
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

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


class AbstractTenantConfiguration(BaseVersioningModel):
    """
    Abstract Class for a tenant configuration.
    """

    tenant = models.ForeignKey(
        settings.TENANTS_TENANT_MODEL,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="tenant_configs",
    )
    details = models.JSONField(
        null=False, blank=False, default=dict, encoder=DjangoJSONEncoder
    )

    def clean(self):
        """
        Validations for JSON saved in details.
        TODO: Implement JSONSchema Validators and avoid this pattern going forward.
        """
        from apps.configurations.constants import InterfaceTypeChoices

        if not self.details:
            raise ValidationError("Tenant Configuration cannot be empty.")

        if not isinstance(self.details, dict):
            raise ValidationError("Tenant Configuration should be a valid dict.")

        for key, val in self.details.items():
            if not isinstance(key, str) or key not in InterfaceTypeChoices.values:
                raise ValidationError(
                    "Tenant Configuration should be a valid configuration interface_type"
                )

            if not isinstance(val, dict):
                raise ValidationError(
                    f"Invalid Tenant Configuration for interface: {key}"
                )

            for sub_key in ["name", "interface_type", "version"]:
                if sub_key not in val.keys():
                    raise ValidationError(
                        f"{sub_key} is required to form a valid conguration for interface: {key}"
                    )

    @classmethod
    def sync_tenant_configuration(
        cls, schema_name: str
    ) -> "AbstractTenantConfiguration":
        """
        Create a tenant configuration object that is synced from configuration database.
        """
        Tenant = get_tenant_model()

        tenant = Tenant.objects.get(schema_name=schema_name)

        def create_config() -> dict:
            tenant_config = {}

            with schema_context(schema_name):

                Configuration = get_configuration_model()
                configs = Configuration.objects.get_latest().values_list(
                    ["version", "name"]
                )

                for config in configs:
                    tenant_config.update(
                        {
                            config.interface_type: {
                                "name": config.name,
                                "interface_type": config.interface_type,
                                "version": config.version,
                            }
                        }
                    )

            return tenant_config

        return cls.objects.create(
            tenant=tenant,
            details=create_config(),
            version=cls.get_latest_version(tenant=tenant),
        )
