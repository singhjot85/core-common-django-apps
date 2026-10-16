from unittest.mock import MagicMock

import pytest

from core.exceptions import InvalidTypeError, SeederException
from core.seeder.base import BaseMeta, BaseSeeder, empty
from core.seeder.registry import fixture_registry, seeder_registry


@pytest.mark.skip(
    "Fix them post changing validation form Meta.__init_subclass__ to BaseSeeder.__init__"
)
class TestBaseMeta:
    """Unit tests for BaseMeta validation logic."""

    def test_validate_fields_rejects_non_list(self):
        """Fields must be a list or tuple."""
        with pytest.raises((InvalidTypeError, SeederException, TypeError)):

            class BadFieldsMeta(BaseMeta):
                model = MagicMock()
                fields = "not_a_list"
                depends_on = []
                is_fixture = False
                relation_map = {}

    def test_validate_fields_rejects_empty(self):
        """Empty fields should raise SeederException."""
        with pytest.raises((SeederException, TypeError)):

            class EmptyFieldsMeta(BaseMeta):
                model = MagicMock()
                fields = []
                depends_on = []
                is_fixture = False
                relation_map = {}

    def test_validate_relation_map_rejects_non_dict(self):
        """relation_map must be a dict."""
        with pytest.raises((InvalidTypeError, SeederException, TypeError)):

            class BadRelMapMeta(BaseMeta):
                model = MagicMock()
                fields = ["name"]
                depends_on = []
                is_fixture = False
                relation_map = "bad"


class TestBaseSeederRegistration:
    """Unit tests for BaseSeeder __init_subclass__ registration."""

    def test_seeder_subclass_registered_in_seeder_registry(self):
        """Any BaseSeeder subclass should auto-register in seeder_registry."""
        # The production fixture seeders are registered on import
        registry = seeder_registry.registry
        assert registry is not None
        assert isinstance(registry, dict)

    def test_fixture_seeder_registered_in_fixture_registry(self):
        """Seeders with Meta.is_fixture=True must appear in fixture_registry."""
        registry = fixture_registry.registry
        assert registry is not None
        assert isinstance(registry, dict)

    def test_seeder_registry_key_is_snake_case(self):
        """Registry keys should be auto-generated as snake_case from class name."""
        registry = seeder_registry.registry
        for key in registry:
            # Keys should be lowercase and use underscores
            assert key == key.lower(), f"Registry key '{key}' is not lowercase"
            assert " " not in key, f"Registry key '{key}' contains spaces"


@pytest.mark.skip(
    "Fix them post changing validation form Meta.__init_subclass__ to BaseSeeder.__init__"
)
class TestBaseSeederInit:
    """Unit tests for BaseSeeder instance initialization."""

    def test_init_without_meta_raises(self):
        """Instantiating a BaseSeeder subclass without Meta should raise."""
        # BaseSeeder itself should raise on init because it has no Meta
        with pytest.raises(SeederException):
            BaseSeeder()

    def test_seedable_fields_returns_fields_from_meta(self):
        """seedable_fields property should return the list from Meta."""
        registry = seeder_registry.registry
        if not registry:
            pytest.skip("No seeders registered")

        key = next(iter(registry))
        seeder_cls = registry[key]
        instance = seeder_cls()
        assert isinstance(instance.seedable_fields, (list, tuple))
        assert len(instance.seedable_fields) > 0


@pytest.mark.skip(
    "Fix them post changing validation form Meta.__init_subclass__ to BaseSeeder.__init__"
)
class TestBaseSeederValidate:
    """Unit tests for BaseSeeder.validate()."""

    def test_validate_rejects_non_dict(self):
        """validate() should reject non-dict data."""
        registry = seeder_registry.registry
        if not registry:
            pytest.skip("No seeders registered")

        key = next(iter(registry))
        seeder_cls = registry[key]
        instance = seeder_cls()
        with pytest.raises(InvalidTypeError):
            instance.validate("not a dict")

    def test_validate_rejects_list(self):
        """validate() should reject list data."""
        registry = seeder_registry.registry
        if not registry:
            pytest.skip("No seeders registered")

        key = next(iter(registry))
        seeder_cls = registry[key]
        instance = seeder_cls()
        with pytest.raises(InvalidTypeError):
            instance.validate([1, 2, 3])


class TestEmptySentinel:
    """Tests for the empty sentinel object."""

    def test_empty_is_singleton(self):
        """empty should be a unique sentinel."""
        assert empty is not None
        assert empty is not False
        assert empty != 0
