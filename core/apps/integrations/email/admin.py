from django.contrib import admin

from core.apps.integrations.email import (
    get_email_log_model,
    get_email_template_model,
)
from core.utils.admin import private_admin_site

EmailLog = get_email_log_model()
EmailTemplate = get_email_template_model()


@admin.register(EmailLog, site=private_admin_site)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "subject", "status", "backend_used", "created")
    list_filter = ("status", "backend_used")
    search_fields = ("recipient", "subject")


@admin.register(EmailTemplate, site=private_admin_site)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "interface_type", "subject", "version", "is_active")
    list_filter = ("interface_type", "is_active")
    search_fields = ("interface_type", "subject")
