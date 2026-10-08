from __future__ import annotations

from django.db import DEFAULT_DB_ALIAS, models, transaction

from core.exceptions import InvalidTypeError, SeederException
from core.seeder.registry import seeder_registry
from core.utils.strings import camel_to_snake_case

empty = object()


class BaseSeeder:
    """
    Base seeder class to be inherited by each seeder functionality
    """

    _model: models.Model
    _fields: list[str]
    _relation_map: dict[str, type[BaseSeeder]]

    nonconcrete_relations: list[dict]

    def __init_subclass__(cls):
        """
        Build out the seeder registry for each subclass using BaseSeeder
        """
        meta = getattr(cls, "Meta", None)
        if meta:
            depends_on = getattr(meta, "depends_on", None)
            if isinstance(depends_on, (list, tuple)):
                if not all(
                    [
                        isinstance(k, type) and issubclass(k, models.Model)
                        for k in depends_on
                    ]
                ):
                    raise SeederException("Dependencies should be Model classes only")

        try:
            seeder_registry.register(cls, key=camel_to_snake_case(cls.__name__))
        except Exception as e:
            raise SeederException(cls.__name__, str(e)) from e

    @classmethod
    def get_seeder_from_registry(cls, model_name: str) -> type[BaseSeeder]:
        """
        Get seeder for given model_name from the registry
        """
        return seeder_registry.get(model_name)

    def __init__(self):
        """
        Initialize variable's for given seeder instance.
        """
        self._meta = getattr(self, "Meta", None)
        if not self._meta:
            raise SeederException(self.__class__.__name__, "Meta not defined")

        self._model = getattr(self._meta, "model", None)
        if not self._model:
            raise SeederException(self.__class__.__name__, "Model not defined")
        if not isinstance(models.Model):
            raise TypeError(type(self._model), models.Model)

        self._fields = getattr(self._meta, "fields", None)
        if not self._fields:
            raise SeederException(
                self.__class__.__name__, "Fields not defined for seeder"
            )
        if not isinstance(self._fields, (list, tuple)):
            raise InvalidTypeError(type(self._fields), tuple)

        self._relation_map = getattr(self._meta, "related_seeders", {})
        if self._relation_map and not isinstance(self._relation_map, dict):
            raise InvalidTypeError(type(self._relation_map), dict)

    @property
    def seedable_fields(self):
        """
        Get the srializable fields, on this seeder
        """
        if hasattr(self, "_fields") and self._fields is not None:
            return self._fields

        return []

    def validate(self, data: dict):
        """
        Pre Seeding Validation hook, this executes before any object intitation takes place.
        """
        if not isinstance(data, dict):
            raise InvalidTypeError(type=type(data), expected=dict)

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
            self.nonconcrete_relations.append(
                {"accessor_name": field.name, "instance": related_instance}
            )
        elif (
            field.one_to_many
            or (
                field.one_to_one and field.auto_created
            )  # I think this needs to be handeled differently
            or (field.many_to_many and field.auto_created)
        ):
            self.nonconcrete_relations.append(
                {
                    "accessor_name": field.get_accessor_name(),
                    "instance": related_instance,
                }
            )
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

        model_name = self.get_related_model_name(field)
        RegisteredSeeder = self.get_seeder_from_registry(model_name)
        if RegisteredSeeder:
            return RegisteredSeeder.seed(data)

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
                    if not field_value:
                        continue

                    self.set_field_value(field, val, instance)

                # Set all the fields that are not directly on model
                for nonconcrete_map in self.nonconcrete_relations:
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
