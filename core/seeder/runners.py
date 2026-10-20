"""
Topological execution runners for database seeders.

Provides DAG-based dependency resolution and execution pipelines for database seeders
across multi-tenant schemas.
"""

from __future__ import annotations

import logging
import typing
from functools import cached_property

from django.db import DEFAULT_DB_ALIAS, transaction
from rest_framework.exceptions import MethodNotAllowed

from core.apps.tenants import get_tenant_model
from core.apps.tenants.constants import TenantStatus
from core.exceptions import SeederException
from core.seeder.registry import fixture_registry
from core.seeder.registry import seeder_registry as default_seeder_registry
from core.utils.checks import is_multi_tenant, is_production
from core.utils.database import core_schema_context, get_public_schema_name
from core.utils.datatypes import InstanceDAGBuilder
from core.utils.registry import ClassRegistry
from core.utils.strings import camel_to_snake_case

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from django.db import models

    from core.seeder.base import BaseSeeder


class SeederRunner(InstanceDAGBuilder):
    """
    Topological execution runner for BaseSeeder subclasses.

    Resolves inter-seeder dependencies into a directed acyclic graph (DAG),
    sorts seeders in execution priority order, and executes them within schema context
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
            raise SeederException("No registry defined for runner to work on.")

        super().__init__(*args, **kwargs)

    @cached_property
    def seeders(self) -> list[type["BaseSeeder"]]:
        """
        Get all registered seeders from the registry as an unordered sequence.

        Returns:
            list[type[BaseSeeder]]: List of seeder classes.
        """
        return self.seeder_registry.values

    # ------------------------------
    # Overrides for DAG Builder Methods
    # ------------------------------

    def instance_label(self, Seeder: type["BaseSeeder"]) -> str:
        """
        Override for DAGBuilder to get stringified notation of the seeder.

        Args:
            Seeder (type[BaseSeeder]): Seeder class.

        Returns:
            str: Snake-cased seeder label.
        """
        return self.seeder_label(Seeder)

    def get_instance_sequence(self) -> typing.Union[list, tuple]:
        """
        Get sequence of seeder classes to be sorted by the DAG builder.

        Returns:
            list[type[BaseSeeder]]: Unsorted seeder classes.
        """
        return self.seeders

    @cached_property
    def _min_execution_order(self) -> typing.Optional[int]:
        """
        Get the minimum execution_order among all registered seeders.

        Returns:
            int | None: Smallest execution order integer, or None if none set.
        """
        orders = []
        for Seeder in self.seeders:
            if (order := Seeder.execution_order()) is not None:
                orders.append(order)

        return min(orders) if orders else None

    def is_initial_attribute(self, seeder: type["BaseSeeder"]) -> bool:
        """
        Check if a seeder qualifies as an initial / root node in DAG resolution.

        Args:
            seeder (type[BaseSeeder]): Seeder class to test.

        Returns:
            bool: True if seeder is an initial node.
        """
        # If entire series don't have any seeder, make any radom as initial
        if self._min_execution_order is None:
            return True

        # If current seeder has no execution order don't make it first
        if order := seeder.execution_order() is None:
            return False

        return order <= self._min_execution_order

    def get_dependencies(self, seeder: type["BaseSeeder"]) -> list:
        """
        Get all prerequisite dependencies for a given seeder class.

        Args:
            seeder (type[BaseSeeder]): Seeder class.

        Returns:
            list: List of model classes or seeder classes that this seeder depends upon.
        """
        dep_models: list[type["models.Model"]] = seeder.get_model_dependencies()
        if not dep_models:
            return []

        dependent_seeders = []
        # TODO: Time Coplexity for this comaprison can be imporved by pre-builing a dict/map
        for seeder in self.seeders:
            seeder: type["BaseSeeder"]
            SeederModel = seeder.get_seeder_model()
            for Model in dep_models:
                if (
                    Model._meta.app_label == SeederModel._meta.app_label
                    and Model._meta.model_name == SeederModel._meta.model_name
                    and Model._meta.db_table == SeederModel._meta.db_table
                ):
                    dependent_seeders

        return dependent_seeders

    # ------------------------------
    #   Base Seeder Methods
    # ------------------------------

    def seeder_label(self, Seeder: type["BaseSeeder"]) -> str:
        """
        Compute standard snake_case label from a seeder class name.

        Args:
            Seeder (type[BaseSeeder]): Seeder Class.

        Returns:
            str: snake_case identifier.
        """
        return camel_to_snake_case(Seeder.__name__)

    def _run(self, seeder: "BaseSeeder"):
        """
        Execute seeding for an instantiated BaseSeeder.

        Args:
            seeder (BaseSeeder): Initialized seeder instance.
        """
        seed_data = (
            seeder.seed_data
            if isinstance(seeder.seed_data, list)
            else [seeder.seed_data]
        )

        instances = []
        for data in seed_data:
            # If schema for an object is defined, only run for that schema
            if item_schema := data.pop("_schema_name", False):
                with core_schema_context(item_schema):
                    instance = seeder.seed(data=data)
                    if instance:
                        instances.append(str(instance))

                continue

            # If needs to run for all schemas, iterate through all tenants and run in their schema context
            if is_multi_tenant() and seeder.schema_name == seeder.ALL_SCHEMAS:
                TenantModel = get_tenant_model()
                for tenant_schema in (
                    TenantModel.objects.filter(
                        is_active=True, status=TenantStatus.READY.value
                    )
                    .exclude(schema_name=get_public_schema_name())
                    .values_list("schema_name", flat=True)
                ):
                    with core_schema_context(tenant_schema):
                        instance = seeder.seed(data=data)
                        if instance:
                            instances.append(str(instance))

                continue

            # For single-schema seeders, run in the seeder's target schema context
            with core_schema_context(seeder.schema_name):
                if instance:
                    instances.append(str(instance))

                continue

        return instances

    def run(self):
        """
        Execute all registered seeders in topologically sorted dependency order.

        Wraps execution in a transaction and switches schema context per seeder.
        """
        LOGGER.info("Seeder Execution Started...")
        seeders: list[type["BaseSeeder"]] = self.topo_sorted_instances()

        all_instances = []
        with transaction.atomic(using=DEFAULT_DB_ALIAS):
            for Seeder in seeders:
                label = self.seeder_label(Seeder)
                try:
                    seeder = Seeder()
                    instances = self._run(seeder)
                    if instances:
                        all_instances.extend(instances)

                    LOGGER.info(
                        msg=f"[{seeder.schema_name}] Successfully Executed Seeder >>> {label}"
                    )
                except Exception as e:
                    LOGGER.error(
                        msg=f"Failed Executing Seeder >>> {label}",
                        exc_info=e,
                    )
                    raise e

        LOGGER.info("Seeder Execution Finished...")
        return all_instances


class SeedDevelopmentData(SeederRunner):
    """
    Runner for development seeders and global fixtures.

    Disallows execution in production environments for safety.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize SeedData with the default global seeder registry.
        """
        if is_production():
            raise MethodNotAllowed("Seeding data not allowed in current env.")

        seeder_registry = kwargs.pop("seeder_registry", default_seeder_registry)
        super().__init__(seeder_registry=seeder_registry, *args, **kwargs)


class SeedFixtures(SeederRunner):
    """
    Runner for production fixture seeders.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize SeedFixtures with the static fixture registry.
        """
        seeder_registry = kwargs.pop("seeder_registry", fixture_registry)
        super().__init__(seeder_registry=seeder_registry, *args, **kwargs)
