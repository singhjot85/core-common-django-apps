from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.crm"
    label = "crm"
    verbose_name = "Customer Relationship Management"
