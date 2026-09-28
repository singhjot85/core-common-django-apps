from core.apps.configurations import models_abstract


class Configuration(models_abstract.AbstractConfiguration):
    """
    Configuration model
    """

    class Meta(models_abstract.AbstractConfiguration.Meta):
        swappable = "CONFIGURATIONS_CONFIGURATION_MODEL"


class ConfigurationSchema(models_abstract.AbstractConfigurationSchema):
    """
    Configuration Schema Model
    """

    class Metas(models_abstract.AbstractConfigurationSchema.Meta):
        swappable = "CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL"
