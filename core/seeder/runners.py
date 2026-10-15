import logging
import typing
from functools import cached_property

from django.db import DEFAULT_DB_ALIAS, connection, transaction
from rest_framework.exceptions import MethodNotAllowed

from core.exceptions import InvalidTypeError, SeederException
from core.seeder.registry import fixture_registry
from core.seeder.registry import seeder_registry as default_seeder_registry
from core.utils.checks import is_production
from core.utils.datatypes import InstanceDAGBuilder
from core.utils.registry import ClassRegistry
from core.utils.strings import camel_to_snake_case

LOGGER = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from core.seeder.base import BaseSeeder


class BaseRunner(InstanceDAGBuilder):
    """
    Base Runner class to run fixture's
    """

    seeder_registry: ClassRegistry

    def __init__(
        self, seed_data: dict, seeder_registry: ClassRegistry, *args, **kwargs
    ):
        self.seeder_registry = seeder_registry
        if not self.seeder_registry:
            raise SeederException("No registry defined for runner to work on.")

        self._seed_data = seed_data
        if not isinstance(seed_data, dict):
            raise InvalidTypeError(type(seed_data), dict)

        super().__init__(*args, **kwargs)

    @cached_property
    def seeders(self) -> list:
        """
        Get all the seeders as an unordered sequence
        """
        return self.seeder_registry.values

    @property
    def seed_data(self) -> dict:
        """
        Seed data for all the seeders.
        """
        return self._seed_data

    # ------------------------------
    # Overrides for DAG Builder Methods
    # ------------------------------

    def instance_label(self) -> str:
        """
        Override for DAGBuilder's get stringified notation of the instance.
        """
        return self.seeder_label()

    def get_instance_sequence(self) -> typing.Union[list, tuple]:
        """
        Get sequence of instance that need to Sorted using DAG
        """
        return self.seeders

    def is_initial_attribute(self, seeder: type[BaseSeeder]) -> bool:
        """
        Get the attribute representing inital instance.

        Example:
        >>> instance.initial
        """
        return seeder.is_inital_seeder()

    def get_dependencies(self, seeder: type[BaseSeeder]) -> list:
        """
        Get the attribute representing dependencies for the instance.

        Example:
        >>> instance.depends_on
        """
        return seeder.get_dependencies()

    # ------------------------------
    #   Base Seeder Methods
    # ------------------------------

    def seeder_label(self, Seeder: type["BaseSeeder"]) -> str:
        """
        Get label for seeder

        Args:
            kls (BaseSeeder): Seeder Class
        """
        return camel_to_snake_case(Seeder.__name__)

    def run(self):
        """
        Run all the seeders
        """
        LOGGER.info("Seeder Execution Started...")
        seeders: list[type["BaseSeeder"]] = self.topo_sorted_instances()

        with transaction.atomic(using=DEFAULT_DB_ALIAS):
            for Seeder in seeders:
                label = self.seeder_label(Seeder)
                try:
                    Seeder().seed(data=self.seed_data.get(label))
                    LOGGER.info(
                        msg=f"[{connection.schema_name}] Succefully Executed Seeder >>> {label}"
                    )
                except Exception as e:
                    LOGGER.error(
                        msg=f"[{connection.schema_name}] Failed Executing Seeder >>> {label}",
                        exc_info=e,
                    )
                    raise e

        LOGGER.info("Seeder Execution Finished...")


class SeedData(BaseRunner):
    """
    Run all the fixture's that are available
    """

    def __init__(self, seed_data, *args, **kwargs):
        if is_production():
            raise MethodNotAllowed("Seeding data not allowed in current env.")

        seeder_registry = default_seeder_registry
        super().__init__(seed_data, seeder_registry, *args, **kwargs)


class SeedFixtures(BaseRunner):
    """
    Seed fixtures in production enviurnment
    """

    def __init__(self, seed_data, *args, **kwargs):
        seeder_registry = fixture_registry
        super().__init__(seed_data, seeder_registry, *args, **kwargs)
