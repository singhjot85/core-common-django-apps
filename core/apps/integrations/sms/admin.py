from django.contrib import admin

from core.apps.integrations.sms import get_sms_log_model, get_sms_template_model
from core.utils.admin import private_admin_site

SMSLog = get_sms_log_model()
SMSTemplate = get_sms_template_model()


@admin.register(SMSLog, site=private_admin_site)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "status", "backend", "created")
    list_filter = ("status", "backend")
    search_fields = ("recipient",)


@admin.register(SMSTemplate, site=private_admin_site)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "interface_type", "version", "is_active")
    list_filter = ("interface_type", "is_active")
    search_fields = ("interface_type",)
