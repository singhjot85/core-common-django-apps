from django.contrib import admin

from core.apps.tenants import (
    get_domain_model,
    get_tenant_branding_model,
    get_tenant_contact_info_model,
    get_tenant_model,
)
from core.utils.admin import public_admin_site

Tenants = get_tenant_model()
Domain = get_domain_model()
TenantContactInfo = get_tenant_contact_info_model()
TenantBranding = get_tenant_branding_model()


class DomainInline(admin.TabularInline):
    """Inline admin for tenant domains."""

    model = Domain
    extra = 1
    fields = ("domain", "label", "is_primary", "is_removed")


class TenantContactInfoInline(admin.TabularInline):
    """Inline admin for tenant contact information."""

    model = TenantContactInfo
    extra = 1
    fields = ("order", "contact_type", "contact_info", "is_removed")


class TenantBrandingInline(admin.StackedInline):
    """Inline admin for tenant branding customization."""

    model = TenantBranding
    extra = 0
    fields = ("details", "is_removed")


@admin.register(Tenants, site=public_admin_site)
class TenantsAdmin(admin.ModelAdmin):
    """Admin configuration for Tenants and schema management."""

    list_display = (
        "label",
        "schema_name",
        "public_id",
        "status",
        "is_active",
        "created",
        "is_removed",
    )
    list_filter = ("status", "is_active", "is_removed", "created")
    search_fields = ("label", "schema_name", "public_id")
    readonly_fields = ("id", "public_id", "created", "modified")
    inlines = [DomainInline, TenantContactInfoInline, TenantBrandingInline]


@admin.register(Domain, site=public_admin_site)
class DomainAdmin(admin.ModelAdmin):
    """Admin configuration for Domain mappings."""

    list_display = ("domain", "tenant", "label", "is_primary", "is_removed")
    list_filter = ("is_primary", "is_removed")
    search_fields = ("domain", "label", "tenant__schema_name", "tenant__label")


@admin.register(TenantContactInfo, site=public_admin_site)
class TenantContactInfoAdmin(admin.ModelAdmin):
    """Admin configuration for TenantContactInfo."""

    list_display = (
        "tenant",
        "contact_type",
        "order",
        "created",
        "is_removed",
    )
    list_filter = ("contact_type", "is_removed", "created")
    search_fields = ("tenant__schema_name", "tenant__label")


@admin.register(TenantBranding, site=public_admin_site)
class TenantBrandingAdmin(admin.ModelAdmin):
    """Admin configuration for TenantBranding settings."""

    list_display = (
        "tenant",
        "created",
        "modified",
        "is_removed",
    )
    search_fields = ("tenant__schema_name", "tenant__label")
    readonly_fields = ("created", "modified")
