"""
Global registries for BaseSeeder subclasses.

Maintains class registries for all registered seeders (global development seeders)
and static production fixtures (`fixture_registry`).
"""

from core.utils.registry import ClassRegistry

# Global registry for all the seeders
seeder_registry = ClassRegistry()

# Fixture registry: Seeders for static values like status etc.
fixture_registry = ClassRegistry()
