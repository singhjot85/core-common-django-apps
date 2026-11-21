"""
Unit tests for core.libraries.seeder.runner components.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.db import models
from rest_framework.exceptions import MethodNotAllowed

from core.libraries.seeder.exceptions import SeederException
from core.libraries.seeder.methods.defaults import CreateObject
from core.libraries.seeder.registry import ClassRegistry
from core.libraries.seeder.runner import (
    SeedDevelopmentData,
    SeederRunner,
)
from core.libraries.seeder.seeder import BaseSeeder


# ---------------------------------------------------------------------------
# Dummy Models & Seeders
# ---------------------------------------------------------------------------
class DummyUserModel(models.Model):
    username = models.CharField(max_length=50)

    class Meta:
        app_label = "test_libraries_runner"

    def __str__(self) -> str:
        return self.username


class DummyCustomerModel(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = "test_libraries_runner"

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Test Runner Initialization and DAG Ordering
# ---------------------------------------------------------------------------
class TestSeederRunnerDAG:
    """Validate DAG dependency resolution and ordering."""

    def test_runner_requires_registry(self):
        with pytest.raises(SeederException) as exc_info:
            SeederRunner(seeder_registry=None)
        assert "No registry defined" in str(exc_info.value)

    def test_seeders_filters_non_root(self):
        registry = ClassRegistry()

        class RootSeeder(BaseSeeder):
            label = "root_seeder"
            is_root = True

        class ChildSeeder(BaseSeeder):
            label = "child_seeder"
            is_root = False

        registry.register(RootSeeder, key="root_seeder")
        registry.register(ChildSeeder, key="child_seeder")

        runner = SeederRunner(seeder_registry=registry)
        assert RootSeeder in runner.seeders
        assert ChildSeeder not in runner.seeders

    def test_dag_topological_sort_by_seeder_class(self):
        registry = ClassRegistry()

        class UserSeeder(BaseSeeder):
            label = "user_seeder"
            execution_order = 1

        class CustomerSeeder(BaseSeeder):
            label = "customer_seeder"
            depends_on = [UserSeeder]
            execution_order = 2

        registry.register(CustomerSeeder, key="customer_seeder")
        registry.register(UserSeeder, key="user_seeder")

        runner = SeederRunner(seeder_registry=registry)
        sorted_seeders = runner.topo_sorted_instances()

        # UserSeeder must come before CustomerSeeder
        assert sorted_seeders.index(UserSeeder) < sorted_seeders.index(CustomerSeeder)

    def test_dag_topological_sort_by_model_dependency(self):
        registry = ClassRegistry()

        class ModelDepUserSeeder(BaseSeeder):
            label = "model_dep_user_seeder"
            method = CreateObject(model=DummyUserModel, fields=["username"])
            execution_order = 1

        class ModelDepCustomerSeeder(BaseSeeder):
            label = "model_dep_customer_seeder"
            method = CreateObject(model=DummyCustomerModel, fields=["name"])
            depends_on = [DummyUserModel]
            execution_order = 2

        registry.register(ModelDepCustomerSeeder, key="model_dep_customer_seeder")
        registry.register(ModelDepUserSeeder, key="model_dep_user_seeder")

        runner = SeederRunner(seeder_registry=registry)
        sorted_seeders = runner.topo_sorted_instances()

        assert sorted_seeders.index(ModelDepUserSeeder) < sorted_seeders.index(
            ModelDepCustomerSeeder
        )


# ---------------------------------------------------------------------------
# Test Runner Execution & Tenant Isolation
# ---------------------------------------------------------------------------
class TestSeederRunnerExecution:
    """Validate runner schema execution and environment protection."""

    @patch("core.libraries.seeder.runner.is_production", return_value=True)
    def test_seed_development_data_blocked_in_production(self, mock_prod):
        with pytest.raises(MethodNotAllowed):
            SeedDevelopmentData()

    @patch("core.libraries.seeder.runner.transaction.atomic")
    @patch("core.libraries.seeder.runner.core_schema_context")
    def test_runner_executes_seeder_per_tenant(self, mock_schema_context, mock_atomic):
        registry = ClassRegistry()

        mock_method = MagicMock()
        mock_loader = MagicMock()
        mock_loader.get_data.return_value = [{"name": "Acme"}]

        class TenantCustomerSeeder(BaseSeeder):
            label = "tenant_customer"
            loader = mock_loader
            method = mock_method
            schema_name = None  # tenant-scoped

        registry.register(TenantCustomerSeeder, key="tenant_customer")
        runner = SeederRunner(seeder_registry=registry)

        with patch.object(
            runner, "get_tenant_schemas", return_value=["tenant_a", "tenant_b"]
        ):
            runner.run()

        # Should execute in both tenant_a and tenant_b schemas
        context_calls = [c.args[0] for c in mock_schema_context.call_args_list]
        assert "tenant_a" in context_calls
        assert "tenant_b" in context_calls

    @patch("core.libraries.seeder.runner.transaction.atomic")
    @patch("core.libraries.seeder.runner.core_schema_context")
    def test_runner_executes_pinned_schema_once(self, mock_schema_context, mock_atomic):
        registry = ClassRegistry()

        mock_method = MagicMock()
        mock_loader = MagicMock()
        mock_loader.get_data.return_value = [{"name": "Config"}]

        class PinnedPublicSeeder(BaseSeeder):
            label = "pinned_public"
            loader = mock_loader
            method = mock_method
            schema_name = "public"

        registry.register(PinnedPublicSeeder, key="pinned_public")
        runner = SeederRunner(seeder_registry=registry)

        with patch.object(
            runner, "get_tenant_schemas", return_value=["tenant_a", "tenant_b"]
        ):
            runner.run()

        # Pinned schema 'public' must execute only in 'public', never in tenant schemas
        context_calls = [c.args[0] for c in mock_schema_context.call_args_list]
        assert context_calls == ["public"]
