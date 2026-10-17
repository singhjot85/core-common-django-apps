from core.apps.configurations import get_tenant_configuration_model
from core.seeder.base import BaseMeta, BaseSeeder


class TenantConfigurationSeeder(BaseSeeder):
    """Production seeder for tenant configuration records."""

    class Meta(BaseMeta):
        model = get_tenant_configuration_model()
        fields = ["tenant", "details"]
        depends_on = []
        is_fixture = True
        related_seeders = {}
