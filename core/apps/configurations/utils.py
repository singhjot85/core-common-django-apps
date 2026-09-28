from . import get_configuration_model, get_configuration_schema_model

Configuration = get_configuration_model()
ConfigurationSchema = get_configuration_schema_model()


def get_config_version(interface_type):
    """
    Get version of a configuration.
    """


def get_configuration(interface_type: str, version: str = None):
    """
    Get a configuration from database or cache.
    """
