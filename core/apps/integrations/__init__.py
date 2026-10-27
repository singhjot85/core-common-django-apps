import typing

from django.apps import apps as django_apps
from django.conf import settings

from core.apps.integrations.app_settings import IntegrationsSettings

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractCredentialsManager, AbstractIntegration


app_settings: IntegrationsSettings = IntegrationsSettings()


def get_integration_model():
    """Return the configured Integration model."""
    return typing.cast(
        type["AbstractIntegration"],
        django_apps.get_model(
            settings.INTEGRATIONS_INTEGRATION_MODEL, require_ready=False
        ),
    )


def get_credentials_manager_model():
    """Return the configured CredentialsManager model."""
    return typing.cast(
        type["AbstractCredentialsManager"],
        django_apps.get_model(
            settings.INTEGRATIONS_CREDENTIALS_MANAGER_MODEL, require_ready=False
        ),
    )


__all__ = [
    "app_settings",
    "get_integration_model",
    "get_credentials_manager_model",
]
