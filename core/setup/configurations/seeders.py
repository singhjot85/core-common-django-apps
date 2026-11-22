"""
Development seeders for configurations app.
"""

from __future__ import annotations

from core.apps.configurations.fixtures.seeders import ConfigurationSeeder


class DevUsersTemplateLabelSeeder(ConfigurationSeeder):
    """
    Development seeder for users template labels configuration.

    Inherits data source and creation logic with is_fixture=False.
    """

    is_fixture: bool = False
