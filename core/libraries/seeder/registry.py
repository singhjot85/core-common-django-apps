"""
Registries for database seeders.

Maintains class registries for all registered seeders (global development seeders)
and static production fixtures (fixture_registry).
"""

from core.utils.registry import ClassRegistry

# Global registry for all development and production seeders
seeder_registry = ClassRegistry()

# Fixture registry: Seeders for static values (e.g. system configs, preference types)
fixture_registry = ClassRegistry()
