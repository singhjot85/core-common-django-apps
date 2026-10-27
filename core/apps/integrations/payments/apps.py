from django.apps import AppConfig


class IntegrationsPaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.integrations.payments"
    label = "integrations_payments"
    verbose_name = "Integrations Payments"
