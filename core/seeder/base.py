"""
Base abstractions and lifecycle hooks for database seeders.

Defines BaseSeeder and BaseMeta contracts, registry registration hooks,
field conversion logic, relation mapping, and transactional database persistence.
"""

from __future__ import annotations

import typing
from functools import cached_property

from django.db import DEFAULT_DB_ALIAS, connection, models, transaction

from core.exceptions import InvalidTypeError, SeederException
from core.seeder.registry import fixture_registry, seeder_registry
from core.utils.checks import is_model
from core.utils.strings import camel_to_snake_case

if typing.TYPE_CHECKING:
    from core.seeder.datasource import AbstractDataSource

empty = object()


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

    depends_on: typing.Optional[list]
    is_fixture: typing.Optional[bool]
    execution_order: typing.Optional[
        int
    ]  # Order in which the seeder needs to be executed, lower number means higher priority
    related_seeders: typing.Optional[dict[str, BaseSeeder]]

    @classmethod
    def validate_meta(cls, seeder_name):
        """
        Validate any attribute here.
        """
        cls._validate_model(seeder_name)
        cls._validate_fields(seeder_name)
        cls._validate_depends_on(seeder_name)
        cls._validate_relation_map()

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
    def _validate_relation_map(cls):
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

    # Only for type convention, do not override
    _model: models.Model
    _fields: list[str]
    _relation_map: dict[str, type[BaseSeeder]]
    _nonconcrete_relations: list[dict]

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

    def __init__(self, find_seeder: bool = False):
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
        self._relation_map = getattr(self._meta, "related_seeders", {})

        self.pick_from_global_registry = find_seeder
        self._nonconcrete_relations = []

        self._data_source: typing.Optional[AbstractDataSource] = getattr(
            self._meta, "data_source", None
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
        if isinstance(self.seed_data, dict):
            schema_name = self.seed_data.get("_schema_name", None)
            if schema_name:
                return schema_name
        elif isinstance(self.seed_data, list) and self.seed_data:
            if isinstance(self.seed_data[0], dict):
                schema_name = self.seed_data[0].get("_schema_name") or self.seed_data[
                    0
                ].get("tenant_schema")
                if schema_name:
                    return schema_name

        return getattr(connection, "schema_name", "public")

    @classmethod
    def get_dependencies(cls) -> list:
        """
        Get all the dependencies for given seeder.
        """
        meta = getattr(cls, "Meta", None)
        if meta and (depends_on := getattr(meta, "depends_on", False)):
            return depends_on

        return []

    @classmethod
    def get_seeder_from_registry(cls, model_name: str) -> type[BaseSeeder]:
        """
        Get seeder for given model_name from the registry
        """
        return seeder_registry.get(model_name)

    def validate(self, data: dict):
        """
        Pre Seeding Validation hook, this executes before any object intitation takes place.
        """
        if not isinstance(data, dict):
            raise InvalidTypeError(type=type(data), expected=dict)
        return data

    def to_internal_value(self, field_name: str, field_val, model_instance):
        """
        Convert the json field to python internal value
        """
        if field_name not in self.seedable_fields:
            return empty

        field: models.Field = self._model._meta.get_field(field_name)

        if field.concrete and not field.is_relation:
            return field.clean(field_val, model_instance)

        related_instance = self.seed_related_instance(field, field_val)
        if field.many_to_many and not field.auto_created:
            self._nonconcrete_relations.append(
                {"accessor_name": field.name, "instance": related_instance}
            )
            return empty
        elif (
            field.one_to_many
            or (
                field.one_to_one and field.auto_created
            )  # I think this needs to be handeled differently
            or (field.many_to_many and field.auto_created)
        ):
            self._nonconcrete_relations.append(
                {
                    "accessor_name": field.get_accessor_name(),
                    "instance": related_instance,
                }
            )
            return empty
        else:
            return model_instance

        return None

    def get_related_model_name(self, field: models.ForeignObjectRel):
        """
        Get model name for given related field.
        """
        return field.model

    def seed_related_instance(self, field: models.Field, data) -> models.Model:
        """
        Seed a related instance and get its instance
        """
        if not field.is_relation:
            return None

        field_name = field.name
        if field_name in self._relation_map:
            CustomSeeder = self._relation_map[field_name]
            return CustomSeeder().seed(data)

        if self.pick_from_global_registry:
            model_name = self.get_related_model_name(field)
            RegisteredSeeder = self.get_seeder_from_registry(model_name)
            if RegisteredSeeder:
                return RegisteredSeeder.seed(data)

        return None

    def set_field_value(self, field_name, field_value, model_instance):
        """
        Set field attribute to the model instance.
        """
        method_name = f"set_field_{field_name}"
        if hasattr(self, method_name) and callable(getattr(self, method_name)):
            return getattr(self, method_name)(model_instance, field_value)

        return setattr(model_instance, field_name, field_value)

    def seed(self, data: dict) -> models.Model:
        """
        Seed the data
        """
        instance = None
        try:
            validated_data: dict = self.validate(data)

            with transaction.atomic(using=DEFAULT_DB_ALIAS):
                instance = self._model()
                for field, val in validated_data.items():
                    field_value = self.to_internal_value(field, val, instance)
                    if field_value is empty:
                        continue

                    self.set_field_value(field, val, instance)

                # Set all the fields that are not directly on model
                for nonconcrete_map in self._nonconcrete_relations:
                    accessor_name = nonconcrete_map["accessor_name"]
                    obj = nonconcrete_map["instance"]
                    Manager = getattr(instance, accessor_name)
                    Manager.add(obj)

                # Make sure everythin persist in db
                instance.save()
        except Exception as e:
            raise SeederException(
                seeder_name=self.__class__.__name__, message=str(e)
            ) from e

        return instance
