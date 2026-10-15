from core.apps.configurations import (
    get_configuration_model,
    get_configuration_schema_model,
    get_tenant_configuration_model,
)
from core.seeder.base import BaseMeta, BaseSeeder


class ConfigurationSeeder(BaseSeeder):
    """Production seeder for global configuration entries."""

    class Meta(BaseMeta):
        model = get_configuration_model()
        fields = ["name", "interface_type", "details"]
        depends_on = []
        is_fixture = True
        relation_map = {}


class ConfigurationSchemaSeeder(BaseSeeder):
    """Production seeder for configuration schema definitions."""

    class Meta(BaseMeta):
        model = get_configuration_schema_model()
        fields = ["interface_type", "schema"]
        depends_on = []
        is_fixture = True
        relation_map = {}


class TenantConfigurationSeeder(BaseSeeder):
    """Optional production seeder for tenant-specific configuration."""

    REGISTRY_KEY = "configurations_tenant_configuration_seeder"

    class Meta(BaseMeta):
        model = get_tenant_configuration_model()
        fields = ["tenant", "details"]
        depends_on = []
        is_fixture = True
        relation_map = {}
