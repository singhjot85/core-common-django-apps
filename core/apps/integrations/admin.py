from django.contrib import admin

from core.apps.integrations import get_credentials_manager_model, get_integration_model
from core.utils.admin import private_admin_site

Integration = get_integration_model()
CredentialsManager = get_credentials_manager_model()


@admin.register(Integration, site=private_admin_site)
class IntegrationAdmin(admin.ModelAdmin):
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
    list_display = ("id", "name", "expires_on", "created")
    list_filter = ("name",)
    search_fields = ("name",)
