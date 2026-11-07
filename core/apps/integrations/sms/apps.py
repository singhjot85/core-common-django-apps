"""
Django AppConfig for the SMS integrations sub-app.
"""

from django.apps import AppConfig


class IntegrationsSmsConfig(AppConfig):
    """
    AppConfig for the SMS integrations sub-app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.integrations.sms"
    label = "integrations_sms"
    verbose_name = "Integrations Sms"
