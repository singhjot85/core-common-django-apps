"""
Fixture seeders for Configurations application.
"""

import os

from django.conf import settings

from core.apps.configurations import (
    get_configuration_model,
    get_configuration_schema_model,
    get_tenant_configuration_model,
)
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class ConfigurationSeeder(BaseSeeder):
    """Production seeder for global configuration entries."""

    class Meta(BaseMeta):
        model = get_configuration_model()
        fields = ["name", "interface_type", "details"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "configurations/fixtures/configuration/configurations.json",
            )
        )
        depends_on = []
        is_fixture = True
        related_seeders = {}


class ConfigurationSchemaSeeder(BaseSeeder):
    """Production seeder for configuration schema definitions."""

    class Meta(BaseMeta):
        model = get_configuration_schema_model()
        fields = ["interface_type", "schema"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "configurations/fixtures/configuration_schema/schemas.json",
            )
        )
        depends_on = []
        is_fixture = True
        related_seeders = {}


class TenantConfigurationSeeder(BaseSeeder):
    """Optional production seeder for tenant-specific configuration."""

    REGISTRY_KEY = "configurations_tenant_configuration_seeder"

    class Meta(BaseMeta):
        model = get_tenant_configuration_model()
        fields = ["tenant", "details"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "configurations/fixtures/tenant_configuration/tenant_configs.json",
            )
        )
        depends_on = []
        is_fixture = True
        related_seeders = {}
