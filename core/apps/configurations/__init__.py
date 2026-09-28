import typing

from django.apps import apps as django_apps
from django.conf import settings

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractConfiguration, AbstractConfigurationSchema


def get_configuration_model():
    """
    Get configuration model
    """
    return typing.cast(
        type["AbstractConfiguration"],
        django_apps.get_model(
            settings.CONFIGURATIONS_CONFIGURATION_MODEL, require_ready=False
        ),
    )


def get_configuration_schema_model():
    """
    Get configuration schema model
    """
    return typing.cast(
        type["AbstractConfigurationSchema"],
        django_apps.get_model(
            settings.CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL, require_ready=False
        ),
    )
