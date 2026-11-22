"""
Base seeder abstraction for database seeders.
"""

from __future__ import annotations

import logging
import typing

from django.conf import settings
from django.db import models, transaction

from core.libraries.seeder.exceptions import SeederException
from core.libraries.seeder.registry import fixture_registry, seeder_registry
from core.utils.strings import camel_to_snake_case

if typing.TYPE_CHECKING:
    from core.libraries.seeder.loaders.base import AbstractDataSource
    from core.libraries.seeder.methods.base import BaseObjectMethods

LOGGER = logging.getLogger(__name__)


class BaseSeeder:
    """
    Base class for declarative, component-driven database seeders.

    Configured via class attributes:
        - loader: Data source strategy (FileBasedLoader, FactoryBasedLoader, etc.).
        - method: Object persistence strategy (GetorCreateObject, CreateObject, etc.).
        - label: Explicit identifier; defaults to snake_cased class name.
        - is_fixture: If True, registered into fixture_registry for production fixtures.
        - is_root: If True, executed as a standalone DAG node by SeederRunner.
        - tenant_type: Tenant category (e.g. settings.TENANT_TYPE_ORGANIZATION).
        - schema_name: Explicit target schema (e.g. 'public'); None resolves dynamically.
        - depends_on: Prerequisite seeder classes required prior to this seeder's execution.
        - execution_order: Integer priority for breaking dependency ties in runner DAG.
    """

    loader: AbstractDataSource | None = None
    method: BaseObjectMethods | None = None
    label: str | None = None

    is_fixture: bool = False
    is_root: bool = True
    tenant_type: str = getattr(settings, "TENANT_TYPE_ORGANIZATION", "organization")
    schema_name: str | None = None
    schemas: list[str] | None = None

    depends_on: list[type[BaseSeeder]] = []
    execution_order: int | None = None

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Register seeder subclasses into class registries.

        Automatically registers each subclass into ``seeder_registry`` under its snake_case label,
        and into ``fixture_registry`` if ``is_fixture = True``.
        """
        super().__init_subclass__(**kwargs)

        registry_key = cls.label or camel_to_snake_case(cls.__name__)
        seeder_registry.register(cls, key=registry_key)

        if cls.is_fixture:
            fixture_registry.register(cls, key=registry_key)

    @property
    def seeder_label(self) -> str:
        """
        Return the explicit label or the snake_case class name.

        Returns:
            str: Unique registry identifier string.
        """
        return self.label or camel_to_snake_case(self.__class__.__name__)

    def seed_data(
        self,
        data: dict | list[dict],
        parent: models.Model | None = None,
    ) -> models.Model | list[models.Model]:
        """
        Seed one or more child records within the caller's active schema context.

        Invoked by parent seeders through ``related_seeder_map``. Automatically inspects
        foreign key relationships on the child model and injects the parent model instance
        if not explicitly provided in the payload.

        Args:
            data (dict | list[dict]): Single record dictionary or list of record dictionaries.
            parent (models.Model, optional): Parent model instance to bind child foreign keys to.

        Returns:
            models.Model | list[models.Model]: Seeded model instance(s).

        Raises:
            SeederException: If no persistence method is configured on this seeder.
        """
        if self.method is None:
            raise SeederException(
                self.seeder_label, "No persistence method configured."
            )

        # Inject parent reference into child record(s) if not already explicitly present
        if parent is not None:
            parent_field_name = None
            for field in getattr(self.method.model._meta, "fields", []):
                if field.is_relation and isinstance(parent, field.related_model):
                    parent_field_name = field.name
                    break

            if parent_field_name is not None:
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and parent_field_name not in item:
                            item[parent_field_name] = parent
                elif isinstance(data, dict) and parent_field_name not in data:
                    data[parent_field_name] = parent

        if isinstance(data, list):
            instances: list[models.Model] = []
            for item in data:
                instances.append(self.method.seed(item, self))
            return instances

        return self.method.seed(data, self)

    def run(self, data: dict | list[dict] | None = None) -> list[models.Model]:
        """
        Execute seeding for all records within the current schema context.

        Loads records from ``self.loader`` if ``data`` is not passed directly.
        Processes each record inside its own atomic database transaction.

        Side effects:
            - Performs database operations (create/get_or_create/update_or_create).
            - Dispatches child seeders defined in ``related_seeder_map``.

        Args:
            data (dict | list[dict], optional): Explicit data to seed instead of loading from loader.

        Returns:
            list[models.Model]: Successfully persisted model instances.

        Raises:
            SeederException: If no method/loader is configured or if a record persistence fails.
        """
        if self.method is None:
            raise SeederException(
                self.seeder_label, "No persistence method configured."
            )

        if data is None:
            if self.loader is None:
                raise SeederException(
                    self.seeder_label, "No loader configured for seeder."
                )
            data = self.loader.get_data()

        records = [data] if isinstance(data, dict) else data
        instances: list[models.Model] = []

        LOGGER.info("[%s] Seeding %d record(s)...", self.seeder_label, len(records))
        for item in records:
            try:
                with transaction.atomic():
                    instance = self.method.seed(item, self)
                    if instance is not None:
                        instances.append(instance)
            except Exception as exc:
                LOGGER.error(
                    "[%s] Error seeding record: %s",
                    self.seeder_label,
                    exc,
                    exc_info=exc,
                )
                raise SeederException(self.seeder_label, str(exc)) from exc

        return instances
