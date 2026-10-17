"""
Fixture seeders for Tenants application.
"""

import os

from django.conf import settings

from core.apps.configurations import get_tenant_configuration_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class TenantConfigurationSeeder(BaseSeeder):
    """Production seeder for tenant configuration records."""

    class Meta(BaseMeta):
        model = get_tenant_configuration_model()
        fields = ["tenant", "details"]
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "tenants/fixtures/tenant_configuration/tenant_config.json",
            )
        )
        depends_on = []
        is_fixture = True
        related_seeders = {}
