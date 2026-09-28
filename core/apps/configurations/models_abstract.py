import typing

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, models
from django_tenants.utils import schema_context
from rest_framework.exceptions import ValidationError

from core.apps.configurations import (
    get_configuration_model,
    get_tenant_configuration_model,
)
from core.apps.configurations.constants import InterfaceTypeChoices
from core.apps.tenants import get_tenant_model
from core.utils.checks import is_multi_tenant
from core.utils.models import BaseModel, BaseVersioningModel


class ConfigurationManager(
    models.Manager.from_queryset(queryset_class=models.QuerySet)
):
    """
    Custom manager for configuration model
    """

    def get_latest(
        self, interface_type: str, name: str = None
    ) -> models.QuerySet["AbstractConfiguration"]:
        """
        Get latest configurations based on given parameters
        """
        Configuration = get_configuration_model()

        filters = {"interface_type": interface_type}
        if name:
            filters.update({"name": name})

        return (
            self.filter(**filters)
            .order_by("interface_type", *Configuration.DEFAULT_ORDERING)
            .distinct("interface_type")
        )

    def update_latest(
        self, interface_type: str, details: dict, name: str = None, create: bool = False
    ) -> typing.Optional["AbstractConfiguration"]:
        """
        Update latest config based on given filters
        """
        Configuration = get_configuration_model()

        latest_config = self.get_latest(interface_type, name).first()
        if latest_config:
            old_details = latest_config.details
            old_details.update(details)
            latest_config.details = old_details
            latest_config.save(update_fields=["details"])

        elif not latest_config and not create:
            return None

        elif not latest_config and create:

            latest_config = Configuration.objects.create(
                interface_type=interface_type, name=name, details=details
            )

        return latest_config


class AbstractConfiguration(BaseVersioningModel):
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

    objects: ConfigurationManager = ConfigurationManager()

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
    def get_current_active_config_version(cls, interface_type):
        """
        Get version of a configuration.
        """
        if is_multi_tenant():
            TenantConfiguration = get_tenant_configuration_model()

            tenant_config = TenantConfiguration.objects.get_latest()
            config_meta = tenant_config.details.get(interface_type)

            if not config_meta:
                raise ImproperlyConfigured(
                    f"Configuration for interface {interface_type} is not registered in TenantConfiguration."
                )

            return config_meta.get("version", "1.0.0")

        Configuration = get_configuration_model()

        return Configuration.get_latest_version(interface_type=interface_type)

    @classmethod
    def set_config(
        cls,
        interface_type: str,
        details: dict,
        name: str = None,
        set_cache: bool = True,
        create_config: bool = True,
    ) -> "AbstractConfiguration":
        """
        Create a new configuration object.
        """
        config_obj = cls.objects.update_latest(
            interface_type=interface_type,
            details=details,
            name=name,
            create=create_config,
        )

        cache_key = cls.get_cache_key(interface_type=interface_type)
        cache.delete(cache_key)
        if set_cache:
            cache.set(cache_key, details, timeout=settings.CACHE_LARGE_LARGE_TIMEOUT)

        return config_obj

    @classmethod
    def get_configuration(cls, interface_type: str, version: str = None) -> dict:
        """
        Get a configuration from database or cache.
        """
        if not version:
            version = cls.get_current_active_config_version(interface_type)

        cache_key = cls.get_cache_key(interface_type)
        config_details = cache.get(cache_key)

        if config_details is None:
            config = cls.objects.get_latest(interface_type=interface_type).first()
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

    class TenantConfigurationManager(models.Manager.from_queryset(models.QuerySet)):
        """
        Manager for tenant configuration
        """

        def get_latest(self) -> "AbstractTenantConfiguration":
            """
            Get latest Tenant Configuration
            """
            TenantConfiguration = get_tenant_configuration_model()

            return (
                self.filter(
                    tenant__schema_name=connection.schema_name,
                )
                .order_by("tenant", *TenantConfiguration.DEFAULT_ORDERING)
                .first()
            )

    class AbstractTenantConfiguration(BaseVersioningModel):
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

        objects: TenantConfigurationManager = TenantConfigurationManager()

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
                tenant_config = {}

                with schema_context(schema_name):

                    Configuration = get_configuration_model()
                    configs = Configuration.objects.get_latest().values_list(
                        ["version", "name", "interface_type"]
                    )

                    for config in configs:
                        tenant_config.update(
                            {
                                config.interface_type: {
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
                version=cls.get_latest_version(tenant=tenant),
            )
