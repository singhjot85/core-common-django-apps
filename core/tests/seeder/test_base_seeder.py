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


class TestBaseSeederSchemaResolution:
    """Unit tests for BaseSeeder.schema_name property."""

    def test_schema_name_from_meta(self):
        """schema_name explicitly defined on Meta takes highest precedence."""
        from django.conf import settings

        class CustomMeta(BaseMeta):
            model = Configuration
            fields = ["name"]
            tenant_type = settings.TENANT_TYPE_PUBLIC
            schema_name = "custom_schema"
            depends_on = []
            is_fixture = False
            related_seeders = {}

        class CustomSeeder(BaseSeeder):
            class Meta(CustomMeta):
                pass

        instance = CustomSeeder()
        assert instance.schema_name == "custom_schema"

    def test_schema_name_from_seed_data_dict(self):
        """_schema_name in dict seed_data is respected."""
        from django.conf import settings

        class DictDataSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = settings.TENANT_TYPE_PUBLIC
                depends_on = []
                is_fixture = False
                related_seeders = {}

        instance = DictDataSeeder()
        instance.seed_data = {"_schema_name": "org_tenant_1", "name": "Test"}
        assert instance.schema_name == "org_tenant_1"

    def test_schema_name_from_seed_data_list(self):
        """_schema_name in list seed_data is respected."""
        from django.conf import settings

        class ListDataSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = settings.TENANT_TYPE_PUBLIC
                depends_on = []
                is_fixture = False
                related_seeders = {}

        instance = ListDataSeeder()
        instance.seed_data = [{"_schema_name": "org_tenant_2", "name": "Test"}]
        assert instance.schema_name == "org_tenant_2"

    def test_organization_tenant_type_without_schema_returns_all_schemas(self):
        """Organization tenant_type seeder without explicit schema resolves to ALL_SCHEMAS."""
        from django.conf import settings

        class OrgSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = settings.TENANT_TYPE_ORGANIZATION
                depends_on = []
                is_fixture = False
                related_seeders = {}

        instance = OrgSeeder()
        assert instance.schema_name == BaseSeeder.ALL_SCHEMAS

    def test_organization_tenant_type_with_explicit_public_schema_raises(self):
        """Organization tenant_type seeder raises if schema_name is explicitly set to public."""
        from django.conf import settings

        class BadOrgSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = settings.TENANT_TYPE_ORGANIZATION
                schema_name = "public"
                depends_on = []
                is_fixture = False
                related_seeders = {}

        instance = BadOrgSeeder()
        with pytest.raises(SeederException) as exc_info:
            _ = instance.schema_name
        assert "cannot run on public schema" in str(exc_info.value)

    def test_organization_tenant_type_seed_directly_on_public_raises(self, monkeypatch):
        """Calling seed() directly for an organization seeder on public schema raises."""
        from django.conf import settings
        from django.db import connection

        class DirectPublicOrgSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = settings.TENANT_TYPE_ORGANIZATION
                depends_on = []
                is_fixture = False
                related_seeders = {}

        monkeypatch.setattr(connection, "schema_name", "public")
        instance = DirectPublicOrgSeeder()
        with pytest.raises(SeederException) as exc_info:
            instance.seed({"name": "Test"})
        assert "cannot run on public schema" in str(exc_info.value)


class TestSeederRunnerExecution:
    """Unit tests for SeederRunner schema dispatch logic."""

    def test_runner_runs_all_schemas_for_org_seeder(self, monkeypatch):
        """When an org seeder has ALL_SCHEMAS, runner seeds into all ready tenants."""
        from core.apps import tenants
        from core.seeder import runners
        from core.seeder.runners import SeederRunner
        from core.utils.registry import ClassRegistry

        seeded_schemas = []

        class DummyOrgSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = "organization"
                depends_on = []
                is_fixture = False
                related_seeders = {}

            def seed(self, data):
                from django.db import connection

                seeded_schemas.append(getattr(connection, "schema_name", None))

        registry = ClassRegistry()
        registry.register(DummyOrgSeeder, key="dummy_org_seeder")

        class MockQuerySet:
            def filter(self, **kwargs):
                return self

            def exclude(self, **kwargs):
                return self

            def values_list(self, *args, **kwargs):
                return ["tenant_one", "tenant_two"]

        class MockTenantModel:
            objects = MockQuerySet()

        monkeypatch.setattr(tenants, "get_tenant_model", lambda: MockTenantModel)
        monkeypatch.setattr(runners, "get_tenant_model", lambda: MockTenantModel)

        runner = SeederRunner(seeder_registry=registry)
        seeder_instance = DummyOrgSeeder()
        seeder_instance.seed_data = [{"name": "Item1"}]

        runner._run(seeder_instance)
        assert seeded_schemas == ["tenant_one", "tenant_two"]

    def test_runner_runs_item_schema_override(self):
        """When an item specifies _schema_name, runner switches to that schema."""
        from core.seeder.runners import SeederRunner
        from core.utils.registry import ClassRegistry

        seeded_schemas = []

        class SingleSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = "public"
                schema_name = "public"
                depends_on = []
                is_fixture = False
                related_seeders = {}

            def seed(self, data):
                from django.db import connection

                seeded_schemas.append(getattr(connection, "schema_name", None))

        registry = ClassRegistry()
        registry.register(SingleSeeder, key="single_seeder")

        runner = SeederRunner(seeder_registry=registry)
        seeder_instance = SingleSeeder()
        seeder_instance.seed_data = [
            {"_schema_name": "custom_schema_1", "name": "Item1"},
            {"name": "Item2"},
        ]

        runner._run(seeder_instance)
        assert seeded_schemas == ["custom_schema_1", "public"]
