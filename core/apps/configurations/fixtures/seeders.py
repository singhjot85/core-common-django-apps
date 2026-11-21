"""
Fixture seeders for Configurations application.
"""

from __future__ import annotations

import json
import os
import typing

from django.conf import settings

from core.apps.configurations import get_configuration_model
from core.libraries.seeder import BaseObjectMethods, BaseSeeder, FileBasedLoader

Configuration = get_configuration_model()


class SetConfigMethod(BaseObjectMethods):
    """Custom persistence method executing Configuration.set_config()."""

    def perform_seed(self, prepared_fields, seeder):
        create_kwargs, _ = self.split_fields(prepared_fields, seeder)
        return self.model.set_config(
            interface_type=create_kwargs.get("interface_type"),
            details=create_kwargs.get("details", {}),
            name=create_kwargs.get("name", "Users Template Labels"),
            set_cache=False,
        )


class ConfigurationSeeder(BaseSeeder):
    """Production seeder for configuration entries."""

    is_fixture: bool = True
    tenant_type: str = getattr(settings, "TENANT_TYPE_ORGANIZATION", "organization")

    loader = FileBasedLoader(
        directory_name=os.path.join(
            settings.CORE_APP_DIR,
            "configurations/fixtures/configuration",
        ),
        load_method=FileBasedLoader.LOAD_INDIVIDUAL,
    )
    method = SetConfigMethod(
        model=Configuration,
        fields=["name", "interface_type", "details"],
    )

    def set_details(self, raw_value: typing.Any) -> typing.Any:
        """
        Field transform hook: allows template/details to be defined as an external file path.

        If raw_value is a relative path to a JSON or text/HTML template file, reads and returns
        the parsed content, keeping template bodies neatly formatted in separate files.
        """
        if isinstance(raw_value, str):
            candidate_paths = [
                os.path.join(settings.CORE_APP_DIR, raw_value),
                os.path.join(settings.CORE_BASE_DIR, raw_value),
            ]
            for path in candidate_paths:
                if os.path.isfile(path):
                    with open(path, encoding="utf-8") as f:
                        if path.endswith(".json"):
                            return json.load(f)
                        return f.read()

        return raw_value
