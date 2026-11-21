"""
Topological execution runners for database seeders.

Provides DAG-based dependency resolution and execution pipelines for database seeders
across multi-tenant schemas.
"""

from __future__ import annotations

import logging
import typing
from functools import cached_property

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, transaction
from django_tenants.utils import get_tenant_model
from rest_framework.exceptions import MethodNotAllowed

from core.exceptions import CycleError
from core.libraries.seeder.exceptions import SeederException
from core.libraries.seeder.registry import (
    fixture_registry,
    seeder_registry as default_seeder_registry,
)
from core.libraries.seeder.seeder import BaseSeeder
from core.utils.checks import is_model, is_multi_tenant, is_production
from core.utils.database import core_schema_context, get_public_schema_name
from core.utils.datatypes.implementations import InstanceDAGBuilder
from core.utils.strings import camel_to_snake_case

if typing.TYPE_CHECKING:
    from django.db import models

    from core.utils.registry import ClassRegistry

LOGGER = logging.getLogger(__name__)


class SeederRunner(InstanceDAGBuilder):
    """
    Topological execution runner for BaseSeeder subclasses.

    Resolves inter-seeder dependencies into a directed acyclic graph (DAG),
    sorts seeders in execution priority order, and executes them within schema contexts
    and atomic database transactions.
    """

    seeder_registry: ClassRegistry

    def __init__(self, seeder_registry: ClassRegistry, *args, **kwargs):
        """
        Initialize the seeder runner with a target ClassRegistry.

        Args:
            seeder_registry (ClassRegistry): Registry containing registered BaseSeeder classes.
        """
        self.seeder_registry = seeder_registry
        if not self.seeder_registry:
            raise SeederException(
                "runner", "No registry defined for runner to work on."
            )

        super().__init__(*args, **kwargs)

    @cached_property
    def seeders(self) -> list[type[BaseSeeder]]:
        """
        Get all registered root seeders from the registry as an unordered sequence.

        Filters out nested/child seeders marked with `is_root = False`.
        """
        return [s for s in self.seeder_registry.values if getattr(s, "is_root", True)]

    # -----------------------------------------------------------------------
    # Overrides for InstanceDAGBuilder Methods
    # -----------------------------------------------------------------------

    def instance_label(self, Seeder: type[BaseSeeder]) -> str:
        """Return the stringified snake_cased label of the seeder class."""
        return self.seeder_label(Seeder)

    def seeder_label(self, Seeder: type[BaseSeeder]) -> str:
        """Compute label from seeder attribute or snake_cased class name."""
        explicit_label = getattr(Seeder, "label", None)
        return explicit_label or camel_to_snake_case(Seeder.__name__)

    def get_instance_sequence(self) -> list[type[BaseSeeder]]:
        """Return unsorted root seeder classes for the DAG builder."""
        return self.seeders

    @cached_property
    def _min_execution_order(self) -> int | None:
        """Compute the smallest explicit execution_order among all registered seeders."""
        orders = []
        for Seeder in self.seeders:
            order = getattr(Seeder, "execution_order", None)
            if order is not None:
                orders.append(order)
        return min(orders) if orders else None

    def is_initial_attribute(self, seeder: type[BaseSeeder]) -> bool:
        """Check if seeder qualifies as a root execution node in DAG resolution."""
        if self._min_execution_order is None:
            return True

        order = getattr(seeder, "execution_order", None)
        if order is None:
            return False

        return order <= self._min_execution_order

    def get_dependencies(self, seeder: type[BaseSeeder]) -> list[type[BaseSeeder]]:
        """
        Retrieve prerequisite seeders that must run prior to this seeder.

        Resolves dependencies declared as either BaseSeeder classes or Django Models.
        """
        deps = getattr(seeder, "depends_on", []) or []
        dependent_seeders: list[type[BaseSeeder]] = []

        for dep in deps:
            if isinstance(dep, type) and issubclass(dep, BaseSeeder):
                if dep in self.seeders:
                    dependent_seeders.append(dep)
            elif is_model(dep):
                for candidate in self.seeders:
                    candidate_method = getattr(candidate, "method", None)
                    candidate_model = getattr(candidate_method, "model", None)
                    if candidate_model and (
                        candidate_model._meta.app_label == dep._meta.app_label
                        and candidate_model._meta.model_name == dep._meta.model_name
                    ):
                        dependent_seeders.append(candidate)

        return dependent_seeders

    # -----------------------------------------------------------------------
    # Schema Resolution and Execution Pipeline
    # -----------------------------------------------------------------------

    def get_tenant_schemas(self) -> list[str]:
        """
        Retrieve all active tenant schema names in multi-tenant environments.
        """
        if not is_multi_tenant():
            return [get_public_schema_name()]

        TenantModel = get_tenant_model()
        public_schema = get_public_schema_name()
        qs = TenantModel.objects.exclude(schema_name=public_schema).filter(
            is_active=True
        )

        if hasattr(qs, "provisioned"):
            qs = qs.provisioned()

        return list(qs.values_list("schema_name", flat=True))

    def _execute_seeder_in_schema(
        self, seeder_cls: type[BaseSeeder], schema_name: str
    ) -> list[models.Model]:
        """
        Instantiate and execute a fresh BaseSeeder instance inside the specified schema context.

        Guaranteeing complete tenant isolation by provisioning a new seeder per schema.
        """
        with core_schema_context(schema_name):
            seeder = seeder_cls()
            LOGGER.info(
                "[%s] Executing in schema '%s'...", seeder.seeder_label, schema_name
            )
            return seeder.run()

    def run(self) -> list[models.Model]:
        """
        Execute all registered root seeders in topologically sorted dependency order.

        Instantiates a fresh seeder per schema context to guarantee full tenant isolation.

        Side effects:
            - Executes database operations across isolated schema contexts within an atomic transaction.

        Returns:
            list[models.Model]: All model instances created across all executed seeders and schemas.

        Raises:
            SeederException: If a dependency cycle is detected or seeder execution fails.
        """
        LOGGER.info("Seeder Runner execution started...")
        try:
            sorted_seeders: list[type[BaseSeeder]] = self.topo_sorted_instances()
        except CycleError as exc:
            LOGGER.error("Cyclic dependency detected among seeders: %s", exc)
            raise SeederException(
                "runner", f"Cyclic dependency detected among seeders: {exc}"
            ) from exc

        all_instances: list[models.Model] = []

        with transaction.atomic(using=DEFAULT_DB_ALIAS):
            for SeederCls in sorted_seeders:
                label = self.seeder_label(SeederCls)
                try:
                    # 1. Explicit schemas list
                    explicit_schemas = getattr(SeederCls, "schemas", None)
                    if explicit_schemas:
                        target_schemas = (
                            [explicit_schemas]
                            if isinstance(explicit_schemas, str)
                            else list(explicit_schemas)
                        )
                        for sch in target_schemas:
                            if sch == getattr(
                                settings, "TENANT_TYPE_ORGANIZATION", "organization"
                            ):
                                for t_sch in self.get_tenant_schemas():
                                    all_instances.extend(
                                        self._execute_seeder_in_schema(SeederCls, t_sch)
                                    )
                            elif sch == getattr(
                                settings, "TENANT_TYPE_PUBLIC", "public"
                            ):
                                all_instances.extend(
                                    self._execute_seeder_in_schema(
                                        SeederCls, get_public_schema_name()
                                    )
                                )
                            else:
                                all_instances.extend(
                                    self._execute_seeder_in_schema(SeederCls, sch)
                                )
                        LOGGER.info("Successfully executed seeder >>> %s", label)
                        continue

                    # 2. Pinned explicit schema (e.g. 'public')
                    explicit_schema = getattr(SeederCls, "schema_name", None)
                    if explicit_schema:
                        instances = self._execute_seeder_in_schema(
                            SeederCls, explicit_schema
                        )
                        all_instances.extend(instances)
                        LOGGER.info("Successfully executed seeder >>> %s", label)
                        continue

                    # 3. Public tenant type or non-multitenant environment
                    tenant_type = getattr(SeederCls, "tenant_type", None)
                    is_public_tenant = tenant_type == getattr(
                        settings, "TENANT_TYPE_PUBLIC", "public"
                    )
                    if not is_multi_tenant() or is_public_tenant:
                        instances = self._execute_seeder_in_schema(
                            SeederCls, get_public_schema_name()
                        )
                        all_instances.extend(instances)
                        LOGGER.info("Successfully executed seeder >>> %s", label)
                        continue

                    # 4. Tenant schemas (fresh seeder instance per tenant)
                    tenant_schemas = self.get_tenant_schemas()
                    for schema_name in tenant_schemas:
                        instances = self._execute_seeder_in_schema(
                            SeederCls, schema_name
                        )
                        all_instances.extend(instances)

                    LOGGER.info("Successfully executed seeder >>> %s", label)
                except Exception as exc:
                    LOGGER.error(
                        "Failed executing seeder >>> %s: %s",
                        label,
                        exc,
                        exc_info=exc,
                    )
                    raise

        LOGGER.info("Seeder Runner execution completed.")
        return all_instances


class SeedDevelopmentData(SeederRunner):
    """
    Runner for development seeders and global fixtures.

    Disallows execution in production environments for safety.
    """

    def __init__(self, *args, **kwargs):
        if is_production():
            raise MethodNotAllowed(
                "Seeding development data is disallowed in production environments."
            )

        seeder_registry = kwargs.pop("seeder_registry", default_seeder_registry)
        super().__init__(*args, seeder_registry=seeder_registry, **kwargs)


class SeedFixtures(SeederRunner):
    """
    Runner for production fixture seeders.
    """

    def __init__(self, *args, **kwargs):
        seeder_registry = kwargs.pop("seeder_registry", fixture_registry)
        super().__init__(*args, seeder_registry=seeder_registry, **kwargs)
