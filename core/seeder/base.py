"""
Base abstractions and lifecycle hooks for database seeders.

Defines BaseSeeder and BaseMeta contracts, registry registration hooks,
field conversion logic, relation mapping, and transactional database persistence.
"""

from __future__ import annotations

import typing
from functools import cached_property

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, models, transaction

from core.exceptions import InvalidTypeError, SeederException
from core.seeder.constants import (
    ForwardSingularRelation,
    ManagerRelation,
    ReverseSingularRelation,
)
from core.seeder.registry import fixture_registry, seeder_registry
from core.utils.checks import is_model, is_multi_tenant
from core.utils.database import get_public_schema_name
from core.utils.strings import camel_to_snake_case

if typing.TYPE_CHECKING:
    from core.seeder.constants import BaseModelRelation
    from core.seeder.datasource import AbstractDataSource


class BaseMeta:
    """
    Base Meta configuration class for BaseSeeder subclasses.

    Attributes:
        model (models.Model): Django model class to seed.
        fields (list[str]): List of model field names to populate.
        data_source (AbstractDataSource, optional): Data source (FileDataSource, etc.).
        depends_on (list, optional): Prerequisite model classes or dependencies.
        is_fixture (bool, optional): If True, registered in fixture_registry for production.
        execution_order (int, optional): Priority order for initial execution (lower = earlier).
        related_seeders (dict, optional): Map of relation field names to nested BaseSeeder classes.
    """

    model: models.Model
    fields: list
    data_source: AbstractDataSource
    object_create_method: typing.Callable

    is_fixture: bool = False
    schema_name: typing.Optional[str] = None
    tenant_type: str = settings.TENANT_TYPE_ORGANIZATION

    depends_on: typing.Optional[list]
    execution_order: typing.Optional[int]
    related_seeders: typing.Optional[dict[str, BaseSeeder]]

    @classmethod
    def validate_meta(cls, seeder_name):
        """
        Validate any attribute here.
        """
        cls._validate_model(seeder_name)
        cls._validate_fields(seeder_name)
        cls._validate_depends_on(seeder_name)
        cls._validate_related_seeder_map()

    @classmethod
    def _validate_depends_on(cls, seeder_name):
        """
        Validate depends_on
        """
        depends_on = getattr(cls, "depends_on", None)
        if not depends_on:
            return

        if not isinstance(depends_on, (list, tuple)):
            raise InvalidTypeError(type=type(depends_on), expected=list)

        for val in depends_on:
            if not is_model(val):
                raise SeederException(seeder_name, f"Invalid depends_on value: {val}")

    @classmethod
    def _validate_model(cls, seeder_name):
        """
        Validate model
        """
        model = getattr(cls, "model", None)
        if not model:
            raise SeederException(seeder_name, "Model not defined")

        if not is_model(model):
            raise SeederException(seeder_name, f"Invalid model: {model}")

    @classmethod
    def _validate_fields(cls, seeder_name):
        """
        Validate Fields
        """
        fields = getattr(cls, "fields", None)
        if fields is None:
            raise SeederException(seeder_name, "Fields not defined for seeder")

        if not isinstance(fields, (list, tuple)):
            raise InvalidTypeError(type=type(fields), expected=list)

        if len(fields) == 0:
            raise SeederException(seeder_name, "Fields not defined for seeder")

    @classmethod
    def _validate_related_seeder_map(cls):
        """
        Validate related_seeders
        """
        related_seeders = getattr(cls, "related_seeders", None)
        if not related_seeders:
            return

        if not isinstance(related_seeders, dict):
            raise InvalidTypeError(type=type(related_seeders), expected=dict)

        for val in related_seeders.values():
            if not (isinstance(val, type) and issubclass(val, BaseSeeder)):
                raise InvalidTypeError(type=type(val), expected=BaseSeeder)


class BaseSeeder:
    """
    Base seeder class to be inherited by each seeder functionality
    """

    # Can be overriden on base classes
    REGISTRY_KEY: str

    ALL_SCHEMAS = "all_tenant_schemas"

    # Only for type convention, do not override
    _model: models.Model
    _fields: list[str]
    _related_seeder_map: dict[str, type[BaseSeeder]]

    def __init_subclass__(cls, **kwargs):
        """
        Build out the seeder registry for each subclass using BaseSeeder
        """
        super().__init_subclass__(**kwargs)

        try:
            registry_key = getattr(cls, "REGISTRY_KEY", False) or camel_to_snake_case(
                cls.__name__
            )
            # Register all seeders to a global registry
            seeder_registry.register(cls, key=registry_key)

            # Register fixture seeders to a seperate registry
            if (meta := getattr(cls, "Meta", None)) and meta.is_fixture:
                fixture_registry.register(cls, key=registry_key)

        except Exception as e:
            raise SeederException(cls.__name__, str(e)) from e

    def __init__(self, **kwargs):
        """
        Initialize variable's for given seeder instance.

        Args:
            find_seeder (bool): find seeder from global registry if not given.
        """
        self._meta: BaseMeta = getattr(self, "Meta", None)
        if not self._meta:
            raise SeederException(self.__class__.__name__, "Meta not defined")

        self._meta.validate_meta(self.__class__.__name__)

        self._model = getattr(self._meta, "model", None)
        self._fields = getattr(self._meta, "fields", None)

        self.execution_order = getattr(self._meta, "execution_order", None)
        self._related_seeder_map = getattr(self._meta, "related_seeders", {})
        self._data_source: typing.Optional[AbstractDataSource] = getattr(
            self._meta, "data_source", None
        )

        self._related_data: list["BaseModelRelation"] = []
        self.context = kwargs
        self.creation_method = getattr(
            self._meta,
            "object_create_method",
            self._model._default_manager.get_or_create,
        )

    @property
    def seedable_fields(self):
        """
        Get the srializable fields, on this seeder
        """
        if hasattr(self, "_fields") and self._fields is not None:
            return self._fields

        return []

    def _get_data_source(self) -> typing.Optional[AbstractDataSource]:
        """
        Retrieve data source from Meta or infer fallback FileDataSource if configured.
        """
        if self._data_source:
            return self._data_source

        file_path = getattr(self._meta, "file_path", None)
        if file_path:
            from core.seeder.datasource import FileDataSource

            return FileDataSource(file_path)

        return None

    @cached_property
    def seed_data(self) -> typing.Union[dict, list]:
        """
        Load the seed_data for this seeder.
        """
        ds = self._get_data_source()
        if not ds:
            raise SeederException(
                seeder_name=self.__class__.__name__,
                message="Data source not defined for seeder",
            )
        return ds.get_data()

    @property
    def schema_name(self) -> str:
        """
        Schema in which the seeder is supposed to run.
        """
        if schema_name := getattr(self._meta, "schema_name", None):
            if (
                is_multi_tenant()
                and self._meta.tenant_type == settings.TENANT_TYPE_ORGANIZATION
                and schema_name == get_public_schema_name()
            ):
                raise SeederException(
                    seeder_name=self.__class__.__name__,
                    message="Seeder for organization tenant type cannot run on public schema",
                )
            return schema_name

        if (
            is_multi_tenant()
            and self._meta.tenant_type == settings.TENANT_TYPE_ORGANIZATION
        ):
            return self.ALL_SCHEMAS

        return get_public_schema_name()

    @classmethod
    def get_dependencies(cls) -> list:
        """
        Get all the dependencies for given seeder.
        """
        meta = getattr(cls, "Meta", None)
        if meta and (depends_on := getattr(meta, "depends_on", False)):
            return depends_on

        return []

    def to_internal_values(self, data: dict):
        """
        Convert the json field to python internal value

        Expected data format:
        ```json
        {
            "attr": "val",

            # This will do a related_model.objects.get(attribute=val)
            "related_field__attribute": "val",

            # This related create a realted_object and then link it to current model.
            # NOTE: Fot this notation you need to first define a realted seeder on this seeder.
            "related_field": {
                "attr1": "val1",
                "attr2": "val2",
                "attr3": "val3",
            }
        }
        ```
        """
        self._validated_data = {}
        for field_name, field_val in data.items():
            field_name: str
            field_val: typing.Any

            if field_name not in self.seedable_fields:
                continue

            related_unique_attr = None
            if "__" in field_name:
                field_name, related_unique_attr = field_name.split("__")

            field: models.Field = self._model._meta.get_field(field_name)

            if field.concrete and not field.is_relation:
                self._validated_data.update({field_name: field.clean(field_val, None)})
                continue

            related_data = self.get_related_instance(
                field_name, field_val, related_unique_attr
            )
            if related_data:
                self._related_data.append(related_data)

        return self._validated_data

    def get_related_instance(
        self, field_name: str, field_val: typing.Any, related_unique_attr: str
    ):
        """ """
        field: models.ForeignObjectRel = self._model._meta.get_field(field_name)

        def seed_related_instance() -> models.Model:
            """
            Seed a related instance and get its instance
            """
            if field.name in self._related_seeder_map:
                CustomSeeder = self._related_seeder_map[field.name]
                return CustomSeeder().seed(field_val)
            return None

        def retrieve_related_instance() -> models.Model:
            """ """
            RelatedModel = (
                field.field.model  # Reverse 1-1 need this special access route for the realted model
                if field.one_to_one and field.auto_created
                else field.related_model
            )
            return RelatedModel._default_manager.get(related_unique_attr=field_val)

        related_instance = None
        if related_unique_attr is not None:
            related_instance = retrieve_related_instance()
        elif isinstance(field_val, dict):
            related_instance = seed_related_instance()

        if related_instance:
            # Handle both ForeignKey and OneToOne
            if field.many_to_one or (field.one_to_one and not field.auto_created):
                return ForwardSingularRelation(related_instance, field_name)

            # Handle reverse OneToOne
            elif field.one_to_one and field.auto_created:
                return ReverseSingularRelation(related_instance, field_name)

            # Handle ManyToMany, reverse ForeignKey and reverse ManyToMany
            elif field.many_to_many or field.one_to_many:
                return ManagerRelation(related_instance, field_name)

    def _filter_seedable_fields(self, data: dict):
        """ """
        seedable_data = {}
        # Filter out fields that are not declared seedable
        for key, val in data.items():
            if key not in self.seedable_fields:
                seedable_data.update({key: val})

        return data

    def validate(self, data: dict):
        """
        Hook to implement validations
        """
        return data

    def seed(self, data: dict) -> models.Model:
        """
        Seed the data
        """
        try:
            filtered_data = self._filter_seedable_fields(data)
            validated_data = self.validate(filtered_data)

            with transaction.atomic(using=DEFAULT_DB_ALIAS):
                internal_values = self.to_internal_values(validated_data)
                return self.create(internal_values)

        except Exception as e:
            raise SeederException(
                seeder_name=self.__class__.__name__, message=str(e)
            ) from e

    def create(self, data: dict) -> models.Model:
        """ """
        instance = self.creation_method(**data)

        # All the FK, 1-1, 1-M, M-1, M-M linkage happend after the object is created
        for related_data in self._related_data:
            related_data.link_relation(instance)

        return instance
