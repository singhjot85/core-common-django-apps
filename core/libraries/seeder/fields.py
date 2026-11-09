import typing

from django.db import models

from core.libraries.seeder.exceptions import FieldException

if typing.TYPE_CHECKING:
    from core.libraries.seeder.seeder import BaseSeeder


class SeederField:
    """ """

    field_name: str
    model: models.Model
    data: typing.Any

    def __init__(self, field_name: str, model: type[models.Model], data: typing.Any):
        """ """
        self.field_name = field_name
        self.model = model
        self.data = data

        self.field.clean(self.data)

    @property
    def field(self) -> models.Field:
        """ """
        return self.model._meta.get_field(self.field_name)

    @property
    def is_required(self) -> bool:
        """ """
        if self.field.null or self.field.has_default():
            return False

        return not self.field.blank

    def get_value(self, seeder: "BaseSeeder") -> typing.Any:
        """ """
        raw_value = self.data

        if hasattr(seeder, f"get_{self.field_name}"):
            return getattr(seeder, f"get_{self.field_name}")(raw_value)

        return raw_value


class RelationField(SeederField):
    """ """

    is_relation: bool = True
    related_instance: models.Model
    related_seeder_map: dict[str, "BaseSeeder"]

    def __init__(self, related_seeder_map: dict, *args):
        """ """

        self.related_seeder_map = related_seeder_map

        super().__init__(*args)

    def get_value(self, seeder: "BaseSeeder") -> typing.Any:
        """ """
        raw_value = self.data

        if hasattr(seeder, f"get_{self.field_name}"):
            return getattr(seeder, f"get_{self.field_name}")(raw_value)

        return self.create_related_instance(None)

    def retrieve_related_instance(self) -> models.Model:
        """
        Retrieve an existing related model instance using the unique attribute.

        Payload Example:
        >>> {"$ref": {"attr": "first_name", "value": "Charlie"}}

        Returns:
            models.Model: The matched related model instance from the database.

        Raises:
            - ObjectDoesNotExist: If no record matches the lookup.
            - ManyObjectsExist: If multiple records matches the lookup.
        """
        self.data: dict
        self.field: models.ForeignObjectRel

        RelatedModel = (
            self.field.field.model  # Reverse 1-1 need this special access route for the realted model
            if self.field.one_to_one and self.field.auto_created
            else self.field.related_model
        )

        lookup_map = {}
        for attr, val in self.data.items():
            lookup_map[attr] = val

        return RelatedModel._default_manager.get(**lookup_map)

    def create_related_instance(self, seeding_instance: "models.Model"):
        """
        Create the realted instance from data, and field

        """
        if isinstance(self.data, dict) and self.data.keys()[0] == "$ref":
            self.related_instance = self.retrieve_related_instance()

        if self.field_name in self.related_seeder_map:
            CustomSeeder: type["BaseSeeder"] = self.related_seeder_map[self.field_name]
            return CustomSeeder().run(self.data)

    def link_relation(self, instance: "models.Model") -> None:
        """
        Attach the related instance to `instance` via the accessor.
        Override in subclasses if the accessor semantics differ.
        """
        raise NotImplementedError


class ForwardSingularRelation(RelationField):
    """ """

    @property
    def is_required(self):
        """ """
        field = self.related_instance._meta.get_field(self.field_name)

        if field.null or field.has_default():
            return False

        if self._constraint_requires_field(self.related_instance, self.field_name):
            return True

        return not field.blank

    def _constraint_requires_field(model: models.Model, field_name: str) -> bool:
        """
        Return True if any UniqueConstraint/Index includes field_name.

        Args:
            model: class or object of the model.
            field_name (str): Attribute name of the field.

        Returns:
            True if the field in model constraints.
        """
        for constraint in model._meta.constraints:
            if isinstance(constraint, (models.UniqueConstraint, models.Index)):
                if field_name in constraint.fields:
                    return True

        for index in model._meta.indexes:
            if field_name in index.fields:
                return True

        return False

    def link_relation(self, instance):
        """
        Link the related object to the instance.
        """
        setattr(instance, self.field_name, self.related_instance)
        instance.save(update_fields=[self.field_name])


class ReverseSingularRelation(RelationField):
    """
    Reverse ``OneToOne`` set FK on the *related* instance and save it.
    Only special handling that is different from all.
    """

    accessor_name: str  # field name on the other model.

    def __init__(self, related_seeder_map, *args):
        super().__init__(related_seeder_map, *args)

        self.accessor_name = self.field.field.name

    @property
    def is_required(self):
        """ """
        return False

    def create_related_instance(self, seeding_instance):
        """ """
        if not (isinstance(self.data, dict) and self.data.keys()[0] == "$ref"):
            if not seeding_instance:
                raise FieldException(
                    self.field_name,
                    self.model.__class__,
                    "Seeding Instance not provided",
                )

            self.data[self.accessor_name] = seeding_instance

        return super().create_related_instance(seeding_instance)

    def link_relation(self, instance):
        """
        No need to link reverse OneToOne relation, create_related_instance links current seeding_object
        on the other side model.
        """


class ManagerRelation(RelationField):
    """
    Forward ``ManyToMany``, reverse ``ForeignKey``and reverse ``ManyToMany``
    All these fetch a RelatedManager using the accessor and a ``.add()``
    """

    accessor_name: str  # field name (forward) or get_accessor_name() (reverse)

    def __init__(self, related_seeder_map, *args):
        super().__init__(related_seeder_map, *args)

        self.accessor_name = (
            self.field.get_accessor_name()
            if self.field.auto_created
            else self.field_name
        )

    @property
    def is_required(self):
        """ """
        return False

    def link_relation(self, instance):
        """ """
        RelatedManager = getattr(instance, self.accessor_name)
        RelatedManager.add(self.related_instance)
