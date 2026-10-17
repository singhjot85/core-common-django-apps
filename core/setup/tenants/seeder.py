from django.contrib.auth import get_user_model

from core.apps.tenants import get_tenant_model
from core.seeder.base import BaseMeta, BaseSeeder


class DevTenantSeeder(BaseSeeder):
    """Dev seeder for mock tenants (public and private)."""

    class Meta(BaseMeta):
        model = get_tenant_model()
        fields = ["schema_name", "label", "is_active"]
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevUserSeeder(BaseSeeder):
    """Dev seeder for mock users linked to tenants."""

    class Meta(BaseMeta):
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "is_staff", "is_superuser"]
        depends_on = []
        is_fixture = False
        related_seeders = {}
