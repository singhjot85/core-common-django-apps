"""
Fixture seeders for Configurations application (compatibility alias for seeders.py).
"""

from core.apps.configurations.fixtures.seeders import (
    ConfigurationSchemaSeeder,
    ConfigurationSeeder,
    TenantConfigurationSeeder,
    UsersTemplateLabelFixtureSeeder,
)

__all__ = [
    "ConfigurationSchemaSeeder",
    "ConfigurationSeeder",
    "TenantConfigurationSeeder",
    "UsersTemplateLabelFixtureSeeder",
]
