"""
Django AppConfig for the core integrations framework.
"""

from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    """
    AppConfig for the core integrations framework.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.integrations"
    label = "integrations"
    verbose_name = "Integrations"
