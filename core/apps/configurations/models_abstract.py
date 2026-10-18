from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models
from django_tenants.utils import schema_context
from rest_framework.exceptions import ValidationError

from core.apps.configurations.constants import InterfaceTypeChoices
from core.apps.tenants import get_tenant_model
from core.utils.checks import is_multi_tenant
from core.utils.models import BaseModel, BaseSemanaticVersionModel


class AbstractConfiguration(BaseSemanaticVersionModel):
    """
    Configurations model to store database configuration values
    """

    name = models.CharField(max_length=124, null=True, blank=True)
    interface_type = models.CharField(
        null=False, blank=False, choices=InterfaceTypeChoices.choices
    )

    details = models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)
    schema = models.ForeignKey(
        settings.CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL,
        on_delete=models.PROTECT,
        related_name="configurations",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"

    def __str__(self):
        return f"{self.name} - {self.version}"

    @classmethod
    def get_cache_key(cls, interface_type: str):
        """
        Get Cache key for current config
        """
        return f"{connection.schema_name}:configurations:{interface_type}"

    @classmethod
    def set_config(
        cls,
        interface_type: str,
        details: dict,
        name: str = None,
        set_cache: bool = True,
    ) -> "AbstractConfiguration":
        """
        Create a new configuration object.
        """
        config_obj, _ = cls.objects.versioned_update_or_create(
            interface_type=interface_type,
            defaults={
                "details": details,
                "name": name,
            },
        )

        cache_key = cls.get_cache_key(interface_type=interface_type)
        cache.delete(cache_key)
        if set_cache:
            cache.set(cache_key, details, timeout=settings.CACHE_LARGE_LARGE_TIMEOUT)

        return config_obj

    @classmethod
    def get_configuration(cls, interface_type: str) -> dict:
        """
        Get a configuration from database or cache.
        """
        cache_key = cls.get_cache_key(interface_type)
        config_details = cache.get(cache_key)

        if config_details is None:
            config = cls.objects.latest_qs(interface_type=interface_type).first()
            if not config:
                ImproperlyConfigured(
                    f"Cannot find any configuration for: {interface_type}"
                )

            config_details = config.details
            cache.set(
                cache_key, config_details, timeout=settings.CACHE_LARGE_LARGE_TIMEOUT
            )

        return config_details


class AbstractConfigurationSchema(BaseModel):
    """
    Configuration schema model to store configuration schema values
    """

    interface_type = models.CharField(
        null=False, blank=False, choices=InterfaceTypeChoices.choices
    )
    schema = models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True
        verbose_name = "Configuration Schema"
        verbose_name_plural = "Configuration Schemas"


if is_multi_tenant():
    """
    Crete a TenantConfiguration for a multi-schema projects to keep
    tenant-wise config version tracking
    """

    class AbstractTenantConfiguration(BaseSemanaticVersionModel):
        """
        Abstract Class for a tenant configuration.
        """

        tenant = models.ForeignKey(
            settings.TENANTS_TENANT_MODEL,
            on_delete=models.CASCADE,
            null=True,
            blank=True,
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
            from core.apps.configurations.constants import InterfaceTypeChoices

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
                    if sub_key not in val.keys() or not val.get(sub_key):
                        raise ValidationError(
                            f"{sub_key} is required to form a valid configuration for interface: {key}"
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
                from core.apps.configurations import get_configuration_model

                Configuration = get_configuration_model()

                tenant_config = {}
                with schema_context(schema_name):
                    configs = (
                        Configuration.objects.latest_qs(ordering=("interface_type"))
                        .distinct("interface_type")
                        .values_list(["version", "name", "interface_type"])
                    )

                    for config in configs:
                        tenant_config.update(
                            {
                                str(config.interface_type): {
                                    "name": config.get("name"),
                                    "interface_type": config.get("interface_type"),
                                    "version": config.get("version"),
                                }
                            }
                        )

                return tenant_config

            return cls.objects.create(
                tenant=tenant,
                details=create_config(),
                version=cls.objects.latest_version(tenant=tenant),
            )
