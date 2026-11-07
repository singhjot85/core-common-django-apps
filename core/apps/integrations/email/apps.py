"""
Django AppConfig for the email integrations sub-app.
"""

from django.apps import AppConfig


class IntegrationsEmailConfig(AppConfig):
    """
    AppConfig for the email integrations sub-app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.integrations.email"
    label = "integrations_email"
    verbose_name = "Integrations Email"
