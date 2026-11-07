"""
Admin site registrations for core integrations and credentials management.
"""

from django.contrib import admin

from core.apps.integrations import get_credentials_manager_model, get_integration_model
from core.utils.admin import private_admin_site

Integration = get_integration_model()
CredentialsManager = get_credentials_manager_model()


@admin.register(Integration, site=private_admin_site)
class IntegrationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Integration model on the private tenant site.
    """

    list_display = (
        "id",
        "label",
        "integration_key",
        "is_active",
        "mock",
        "has_webhooks",
    )
    list_filter = ("integration_key", "is_active", "mock", "has_webhooks")
    search_fields = ("label",)


@admin.register(CredentialsManager, site=private_admin_site)
class CredentialsManagerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the CredentialsManager model on the private tenant site.
    """

    list_display = ("id", "name", "expires_on", "created")
    list_filter = ("name",)
    search_fields = ("name",)
