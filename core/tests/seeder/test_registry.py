import pytest

from core.seeder.registry import fixture_registry, seeder_registry
from core.utils.registry import ClassRegistry


class TestSeederRegistry:
    """Tests for the seeder_registry singleton."""

    def test_seeder_registry_is_class_registry(self):
        assert isinstance(seeder_registry, ClassRegistry)

    def test_fixture_registry_is_class_registry(self):
        assert isinstance(fixture_registry, ClassRegistry)

    def test_seeder_registry_not_empty(self):
        """At least production fixture seeders should be registered."""
        assert seeder_registry.registry is not None
        assert len(seeder_registry.registry) > 0

    def test_fixture_registry_contains_production_seeders(self):
        """fixture_registry should contain only is_fixture=True seeders."""
        registry = fixture_registry.registry
        expected_keys = {
            "customer_preference_type_seeder",
            "configuration_seeder",
            "configuration_schema_seeder",
        }
        registered_keys = set(registry.keys())
        assert expected_keys.issubset(registered_keys), (
            f"Missing production seeders. "
            f"Expected: {expected_keys}, Got: {registered_keys}"
        )

    def test_dev_seeders_not_in_fixture_registry(self):
        """Dev-prefixed seeders must NOT appear in fixture_registry."""
        registry = fixture_registry.registry
        dev_keys = [k for k in registry if k.startswith("dev_")]
        assert (
            len(dev_keys) == 0
        ), f"Dev seeders should not be in fixture_registry: {dev_keys}"

    def test_dev_seeders_in_seeder_registry(self):
        """Dev-prefixed seeders must appear in seeder_registry."""
        registry = seeder_registry.registry
        dev_keys = [k for k in registry if k.startswith("dev_")]
        assert len(dev_keys) > 0, "No dev seeders found in seeder_registry"

    def test_all_dev_seeders_registered(self):
        """All expected dev seeders should be in the global registry."""
        registry = seeder_registry.registry
        expected_dev_keys = {
            "dev_user_seeder",
            "dev_customer_seeder",
            "dev_customer_phone_seeder",
            "dev_customer_email_seeder",
            "dev_customer_address_seeder",
            "dev_billing_organization_seeder",
            "dev_organization_email_seeder",
            "dev_organization_phone_seeder",
            "dev_invoice_party_seeder",
            "dev_invoice_party_email_seeder",
            "dev_invoice_party_phone_seeder",
            "dev_invoice_item_seeder",
        }
        registered_keys = set(registry.keys())
        missing = expected_dev_keys - registered_keys
        assert not missing, f"Missing dev seeders in registry: {missing}"

    def test_seeder_registry_get_returns_class(self):
        """registry.get() should return the seeder class, not an instance."""
        registry = seeder_registry.registry
        if not registry:
            pytest.skip("No seeders registered")

        key = next(iter(registry))
        cls = seeder_registry.get(key)
        assert cls is not None
        assert isinstance(cls, type)

    def test_seeder_registry_get_unknown_returns_none(self):
        """registry.get() for a non-existent key should return None."""
        result = seeder_registry.get("nonexistent_seeder_key_xyz")
        assert result is None
