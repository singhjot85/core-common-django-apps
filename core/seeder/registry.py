from core.utils.registry import ClassRegistry

# Global registry for all the seeders
seeder_registry = ClassRegistry()

# Fixture registry: Seeders for static values like status etc.
fixture_registry = ClassRegistry()
