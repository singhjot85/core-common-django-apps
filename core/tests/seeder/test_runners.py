"""
Unit tests for core.seeder.runners (SeederRunner, SeedDevelopmentData, SeedFixtures).
"""

from unittest.mock import patch

import pytest
from rest_framework.exceptions import MethodNotAllowed

from core.apps.configurations import get_configuration_model
from core.apps.crm import get_customer_model
from core.apps.invoices import get_invoice_party_model
from core.apps.users import get_user_model
from core.exceptions import SeederException
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.registry import fixture_registry, seeder_registry
from core.seeder.runners import SeedDevelopmentData, SeederRunner, SeedFixtures
from core.utils.registry import ClassRegistry

Configuration = get_configuration_model()
Customer = get_customer_model()
User = get_user_model()
InvoiceParty = get_invoice_party_model()


class MockUserSeeder(BaseSeeder):
    class Meta(BaseMeta):
        model = User
        fields = ["username", "email"]
        execution_order = 1
        is_fixture = False
        depends_on = []


class MockCustomerSeeder(BaseSeeder):
    class Meta(BaseMeta):
        model = Customer
        fields = ["first_name", "last_name"]
        execution_order = 2
        is_fixture = False
        depends_on = [User]


class MockInvoicePartySeeder(BaseSeeder):
    class Meta(BaseMeta):
        model = InvoiceParty
        fields = ["first_name", "last_name", "party_type"]
        execution_order = 3
        is_fixture = False
        depends_on = [Customer]


class MockItemSeeder(BaseSeeder):
    class Meta(BaseMeta):
        model = Configuration
        fields = ["name"]
        is_fixture = False
        depends_on = []


class TestSeederRunnerDependenciesAndOrdering:
    """Tests for SeederRunner dependency extraction and topological ordering."""

    def test_seeder_runner_requires_registry(self):
        with pytest.raises(SeederException, match="No registry defined"):
            SeederRunner(seeder_registry=None)

    def test_get_dependencies_resolves_model_prerequisites(self):
        registry = ClassRegistry()
        registry.register(MockUserSeeder, key="user")
        registry.register(MockCustomerSeeder, key="customer")
        registry.register(MockInvoicePartySeeder, key="party")
        registry.register(MockItemSeeder, key="item")

        runner = SeederRunner(seeder_registry=registry)

        # MockUserSeeder has no model dependencies
        assert runner.get_dependencies(MockUserSeeder) == []

        # MockCustomerSeeder depends on User -> [MockUserSeeder]
        customer_deps = runner.get_dependencies(MockCustomerSeeder)
        assert customer_deps == [MockUserSeeder]

        # MockInvoicePartySeeder depends on Customer -> [MockCustomerSeeder]
        party_deps = runner.get_dependencies(MockInvoicePartySeeder)
        assert party_deps == [MockCustomerSeeder]

        # MockItemSeeder has no model dependencies
        assert runner.get_dependencies(MockItemSeeder) == []

    def test_topo_sorted_instances_resolves_prerequisite_chain(self):
        registry = ClassRegistry()
        # Register in deliberately reverse dependency order: Party -> Customer -> User
        registry.register(MockInvoicePartySeeder, key="party")
        registry.register(MockItemSeeder, key="item")
        registry.register(MockCustomerSeeder, key="customer")
        registry.register(MockUserSeeder, key="user")

        runner = SeederRunner(seeder_registry=registry)
        sorted_seeders = runner.topo_sorted_instances()

        # User must run before Customer
        user_idx = sorted_seeders.index(MockUserSeeder)
        customer_idx = sorted_seeders.index(MockCustomerSeeder)
        party_idx = sorted_seeders.index(MockInvoicePartySeeder)

        assert (
            user_idx < customer_idx
        ), f"User ({user_idx}) must precede Customer ({customer_idx})"
        assert (
            customer_idx < party_idx
        ), f"Customer ({customer_idx}) must precede InvoiceParty ({party_idx})"

    def test_min_execution_order_computation(self):
        registry = ClassRegistry()
        registry.register(MockInvoicePartySeeder, key="party")  # order 3
        registry.register(MockCustomerSeeder, key="customer")  # order 2
        registry.register(MockUserSeeder, key="user")  # order 1
        registry.register(MockItemSeeder, key="item")  # order None

        runner = SeederRunner(seeder_registry=registry)
        assert runner._min_execution_order == 1

    def test_is_initial_attribute_logic(self):
        registry = ClassRegistry()
        registry.register(MockInvoicePartySeeder, key="party")  # order 3
        registry.register(MockCustomerSeeder, key="customer")  # order 2
        registry.register(MockUserSeeder, key="user")  # order 1
        registry.register(MockItemSeeder, key="item")  # order None

        runner = SeederRunner(seeder_registry=registry)

        # Only the minimum execution order (1) should qualify as initial
        assert runner.is_initial_attribute(MockUserSeeder) is True
        assert runner.is_initial_attribute(MockCustomerSeeder) is False
        assert runner.is_initial_attribute(MockInvoicePartySeeder) is False
        assert runner.is_initial_attribute(MockItemSeeder) is False

    def test_is_initial_attribute_when_no_execution_order_defined(self):
        registry = ClassRegistry()
        registry.register(MockItemSeeder, key="item")

        runner = SeederRunner(seeder_registry=registry)
        assert runner._min_execution_order is None
        assert runner.is_initial_attribute(MockItemSeeder) is True


@pytest.mark.django_db
class TestSeederRunnerExecutionPipeline:
    """Tests for SeederRunner execution pipeline, transactions, and error handling."""

    def test_run_executes_seeders_in_atomic_transaction(self, monkeypatch):
        registry = ClassRegistry()

        execution_log = []

        class TestSeederA(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = "public"
                schema_name = "public"
                is_fixture = False
                depends_on = []
                execution_order = 1

            def seed(self, data):
                execution_log.append("SeederA")
                return "InstanceA"

        class TestSeederB(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = "public"
                schema_name = "public"
                is_fixture = False
                depends_on = []
                execution_order = 2

            def seed(self, data):
                execution_log.append("SeederB")
                return "InstanceB"

        registry.register(TestSeederA, key="seeder_a")
        registry.register(TestSeederB, key="seeder_b")

        runner = SeederRunner(seeder_registry=registry)

        with (
            patch.object(TestSeederA, "seed_data", [{"name": "A"}]),
            patch.object(TestSeederB, "seed_data", [{"name": "B"}]),
        ):
            instances = runner.run()

        assert "InstanceA" in instances
        assert "InstanceB" in instances
        assert execution_log == ["SeederA", "SeederB"]

    def test_run_rolls_back_and_reraises_on_seeder_exception(self):
        registry = ClassRegistry()

        class FailingSeeder(BaseSeeder):
            class Meta(BaseMeta):
                model = Configuration
                fields = ["name"]
                tenant_type = "public"
                schema_name = "public"
                is_fixture = False
                depends_on = []

            def seed(self, data):
                raise ValueError("Seeding failed critically")

        registry.register(FailingSeeder, key="failing_seeder")
        runner = SeederRunner(seeder_registry=registry)

        with patch.object(FailingSeeder, "seed_data", [{"name": "Fail"}]):
            with pytest.raises(ValueError, match="Seeding failed critically"):
                runner.run()


class TestSeedDevelopmentDataAndFixturesRunners:
    """Tests for environment guards and registry bindings in specialized runners."""

    def test_seed_development_data_disallows_production(self, settings):
        settings.DEBUG = False
        settings.DJANGO_ENV = "production"

        with pytest.raises(MethodNotAllowed, match="not allowed in current env"):
            SeedDevelopmentData()

    def test_seed_development_data_defaults_to_global_seeder_registry(self, settings):
        settings.DEBUG = True
        settings.DJANGO_ENV = "dev"

        runner = SeedDevelopmentData()
        assert runner.seeder_registry is seeder_registry

    def test_seed_fixtures_defaults_to_fixture_registry(self):
        runner = SeedFixtures()
        assert runner.seeder_registry is fixture_registry
