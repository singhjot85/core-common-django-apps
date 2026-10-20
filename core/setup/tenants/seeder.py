"""
Development mock seeders for Tenants and Users setup.
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model

from core.apps.tenants import get_tenant_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class DevTenantSeeder(BaseSeeder):
    """Dev seeder for mock tenants (public and private)."""

    class Meta(BaseMeta):
        model = get_tenant_model()
        fields = ["schema_name", "label", "is_active", "status"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/tenants/dev_tenant/tenants.json"
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevUserSeeder(BaseSeeder):
    """Dev seeder for mock users linked to tenants."""

    class Meta(BaseMeta):
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "is_staff", "is_superuser"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        data_source = FileDataSource(
            os.path.join(settings.CORE_BASE_DIR, "setup/tenants/dev_user/users.json")
        )
        object_create_method = get_user_model().objects.create_user
        depends_on = []
        is_fixture = False
        related_seeders = {}
