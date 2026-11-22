"""
Fixture seeders for Tenants application.
"""

from __future__ import annotations

import os

from django.conf import settings

from core.apps.configurations import get_tenant_configuration_model
from core.libraries.seeder import BaseSeeder, FileBasedLoader, GetorCreateObject

TenantConfiguration = get_tenant_configuration_model()


class TenantConfigurationSeeder(BaseSeeder):
    """Production seeder for tenant configuration records."""

    is_fixture: bool = True
    tenant_type: str = getattr(settings, "TENANT_TYPE_PUBLIC", "public")
    schema_name: str = "public"

    loader = FileBasedLoader(
        directory_name=os.path.join(
            settings.CORE_APP_DIR,
            "tenants/fixtures/tenant_configuration/tenant_config.json",
        ),
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = GetorCreateObject(
        model=TenantConfiguration,
        lookup_fields=["tenant"],
        default_fields=["details"],
    )
