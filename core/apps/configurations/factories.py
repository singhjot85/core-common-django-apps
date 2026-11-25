"""
Model factories for the configurations application.
"""

import factory

from core.apps.configurations import (
    get_configuration_model,
    get_configuration_schema_model,
)
from core.apps.configurations.constants import (
    DefaultConfigurationInterfaceTypeChoices,
)

Configuration = get_configuration_model()
ConfigurationSchema = get_configuration_schema_model()


class ConfigurationSchemaFactory(factory.django.DjangoModelFactory):
    """Factory for generating ConfigurationSchema instances."""

    class Meta:
        model = ConfigurationSchema

    interface_type = DefaultConfigurationInterfaceTypeChoices.UI_CONFIGURATION.value
    schema = factory.LazyFunction(lambda: {"type": "object", "properties": {}})


class ConfigurationFactory(factory.django.DjangoModelFactory):
    """Factory for generating Configuration instances."""

    class Meta:
        model = Configuration

    name = factory.Sequence(lambda n: f"config_{n}")
    interface_type = DefaultConfigurationInterfaceTypeChoices.UI_CONFIGURATION.value
    details = factory.LazyFunction(dict)
    version = "1.0.0"
