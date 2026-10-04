from django.contrib import admin

from core.apps.configurations import (
    get_configuration_model,
    get_configuration_schema_model,
    get_tenant_configuration_model,
)
from core.utils.admin import public_admin_site
from core.utils.checks import is_multi_tenant

Configuration = get_configuration_model()
ConfigurationSchema = get_configuration_schema_model()


@admin.register(Configuration, site=public_admin_site)
class ConfigurationAdmin(admin.ModelAdmin):
    """Admin configuration for Database Configurations."""

    list_display = (
        "name",
        "interface_type",
        "version",
        "schema",
        "created",
        "modified",
    )
    list_filter = ("interface_type", "created")
    search_fields = ("name", "interface_type")
    readonly_fields = ("id", "version", "created", "modified")


@admin.register(ConfigurationSchema, site=public_admin_site)
class ConfigurationSchemaAdmin(admin.ModelAdmin):
    """Admin configuration for Configuration Schemas."""

    list_display = ("interface_type", "created", "modified", "is_removed")
    list_filter = ("interface_type", "is_removed")
    search_fields = ("interface_type",)
    readonly_fields = ("id", "created", "modified")


if is_multi_tenant():
    TenantConfiguration = get_tenant_configuration_model()

    @admin.register(TenantConfiguration, site=public_admin_site)
    class TenantConfigurationAdmin(admin.ModelAdmin):
        """Admin configuration for TenantConfiguration version tracking."""

        list_display = ("tenant", "version", "created", "modified")
        search_fields = ("tenant__schema_name", "tenant__label")
        readonly_fields = ("id", "version", "created", "modified")
