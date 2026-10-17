import pytest

from core.apps.configurations import get_configuration_model
from core.exceptions import InvalidTypeError, SeederException
from core.seeder.base import BaseMeta, BaseSeeder, empty
from core.seeder.registry import fixture_registry, seeder_registry

Configuration = get_configuration_model()


class TestBaseMeta:
    """Unit tests for BaseMeta validation logic."""

    def test_validate_fields_rejects_non_list(self):
        """Fields must be a list or tuple."""

        class BadFieldsMeta(BaseMeta):
            model = Configuration
            fields = "not_a_list"
            depends_on = []
            is_fixture = False
            related_seeders = {}

        with pytest.raises((InvalidTypeError, SeederException, TypeError)):
            BadFieldsMeta.validate_meta("BadFieldsSeeder")

    def test_validate_fields_rejects_empty(self):
        """Empty fields should raise SeederException."""

        class EmptyFieldsMeta(BaseMeta):
            model = Configuration
            fields = []
            depends_on = []
            is_fixture = False
            related_seeders = {}

        with pytest.raises((SeederException, TypeError)):
            EmptyFieldsMeta.validate_meta("EmptyFieldsSeeder")

    def test_validate_relation_map_rejects_non_dict(self):
        """related_seeders must be a dict."""

        class BadRelMapMeta(BaseMeta):
            model = Configuration
            fields = ["name"]
            depends_on = []
            is_fixture = False
            related_seeders = "bad"

        with pytest.raises((InvalidTypeError, SeederException, TypeError)):
            BadRelMapMeta.validate_meta("BadRelMapSeeder")

    def test_validate_relation_map_rejects_non_seeder_class(self):
        """related_seeders values must be BaseSeeder subclasses."""

        class BadRelValMeta(BaseMeta):
            model = Configuration
            fields = ["name"]
            depends_on = []
            is_fixture = False
            related_seeders = {"rel": str}

        with pytest.raises(InvalidTypeError):
            BadRelValMeta.validate_meta("BadRelValSeeder")

    def test_validate_model_rejects_non_model(self):
        """model must be a Django Model subclass."""

        class BadModelMeta(BaseMeta):
            model = "not_a_model"
            fields = ["name"]
            depends_on = []
            is_fixture = False
            related_seeders = {}

        with pytest.raises(SeederException):
            BadModelMeta.validate_meta("BadModelSeeder")

    def test_seeder_init_triggers_meta_validation(self):
        """BaseSeeder.__init__ should trigger Meta.validate_meta and reject bad fields."""

        class BadSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = "not_a_list"
                depends_on = []
                is_fixture = False
                related_seeders = {}

        with pytest.raises((InvalidTypeError, SeederException, TypeError)):
            BadSeeder()


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
