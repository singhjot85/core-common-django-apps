"""
Django AppConfig for the payments integrations sub-app.
"""

from django.apps import AppConfig


class IntegrationsPaymentsConfig(AppConfig):
    """
    AppConfig for the payments integrations sub-app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.integrations.payments"
    label = "integrations_payments"
    verbose_name = "Integrations Payments"
