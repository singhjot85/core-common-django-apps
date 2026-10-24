"""
Fixture seeders for Configurations application.
"""

import os
from typing import Any

from django.conf import settings

from core.apps.configurations import get_configuration_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class ConfigurationSeeder(BaseSeeder):
    """Production seeder for global configuration entries."""

    class Meta(BaseMeta):
        model = get_configuration_model()
        fields = ["name", "interface_type", "details"]
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "configurations/fixtures/configuration",
            ),
            load_method=FileDataSource.LOAD_INDIVIDUAL,
        )
        is_fixture = True

    def create(self, data: dict[str, Any]):
        """
        Persist configuration with set_cache=False to prevent cache stampedes during seeding.
        """
        interface_type = data.get("interface_type", None)
        details = data.get("details", {})
        name = data.get("name", "Users Template Labels")

        return self._model.set_config(
            interface_type=interface_type,
            details=details,
            name=name,
            set_cache=False,
        )
