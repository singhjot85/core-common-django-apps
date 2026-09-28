from core.apps.configurations import models_abstract
from core.utils.checks import is_multi_tenant


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

    class Meta(models_abstract.AbstractConfigurationSchema.Meta):
        swappable = "CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL"


if is_multi_tenant():
    """
    Create Tenant Configuration only for muti-tenant apps
    """

    class TenantConfiguration(models_abstract.AbstractTenantConfiguration):
        """
        Tenant configuration model
        """

        class Meta(models_abstract.AbstractTenantConfiguration.Meta):
            swappable = "CONFIGURATIONS_TENANT_CONFIGURATION_MODEL"
