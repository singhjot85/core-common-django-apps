import logging
import typing
from functools import cached_property

from django.db import transaction

from core.libraries.seeder.exceptions import SeederException
from core.utils.database import core_schema_context

if typing.TYPE_CHECKING:
    from core.libraries.seeder.loaders.base import AbstractDataSource
    from core.libraries.seeder.methods.base import BaseObjectMethods

LOGGER = logging.getLogger(__name__)


class BaseSeeder:
    """ """

    if typing.TYPE_CHECKING:
        loader = AbstractDataSource
        method: BaseObjectMethods
        label: str

    @property
    def schema_name(self):
        """ """

    @cached_property
    def seeder_label(self):
        """ """
        return self.label or self.__class__.__name__

    def run(self, data: dict | list = None):
        """
        Args:
            data (dict, optional): Data to be seeded.
        """
        if not data:
            data = self.loader.get_data()

        with core_schema_context(self.schema_name):
            LOGGER.info(f"[{self.seeder_label}] Seeding in schema: {self.schema_name}")
            try:
                for item in data:
                    try:
                        with transaction.atomic():
                            self.method.seed(item, self)

                    except Exception as e:
                        LOGGER.error(
                            f"[{self.seeder_label}] Error seeding object", exc_info=e
                        )

            except Exception as e:
                LOGGER.error(
                    f"[{self.seeder_label}] Error Seeding in schema: {self.schema_name}",
                    exc_info=e,
                )
                raise SeederException(self.seeder_label) from e
