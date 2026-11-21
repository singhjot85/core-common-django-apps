"""
Field and relationship descriptors for database seeders.
"""

from __future__ import annotations

import typing

from django.db import models

from core.libraries.seeder.exceptions import FieldException

if typing.TYPE_CHECKING:
    from core.libraries.seeder.seeder import BaseSeeder


class SeederField:
    """Represents a standard model field within a seeder payload."""

    field_name: str
    model: type[models.Model]
    data: typing.Any

    def __init__(
        self, field_name: str, model: type[models.Model], data: typing.Any
    ) -> None:
        self.field_name = field_name
        self.model = model
        self.data = data

    @property
    def field(self) -> models.Field:
        """Resolve model field metadata from the Django model."""
        return self.model._meta.get_field(self.field_name)

    @property
    def is_required(self) -> bool:
        """
        Determine if the field is mandatory for model persistence.

        Returns False if the field allows NULL or specifies a default value.
        """
        if self.field.null or self.field.has_default():
            return False
        return not self.field.blank

    def get_value(self, seeder: BaseSeeder) -> typing.Any:
        """
        Retrieve transformed field value, delegating to seeder hook if defined.

        Checks for custom transform method `set_<field_name>(raw_value)` or `get_<field_name>(raw_value)` on the seeder.
        """
        raw_value = self.data
        if hasattr(seeder, f"set_{self.field_name}"):
            return getattr(seeder, f"set_{self.field_name}")(raw_value)
        if hasattr(seeder, f"get_{self.field_name}"):
            return getattr(seeder, f"get_{self.field_name}")(raw_value)
        return raw_value


class RelationField(SeederField):
    """Base descriptor for model relationship fields (FK, OneToOne, ManyToMany)."""

    is_relation: bool = True
    related_instance: typing.Any = None
    related_seeder_map: dict[str, type[BaseSeeder]]

    def __init__(
        self,
        related_seeder_map: dict[str, type[BaseSeeder]],
        field_name: str,
        model: type[models.Model],
        data: typing.Any,
    ) -> None:
        self.related_seeder_map = related_seeder_map or {}
        super().__init__(field_name=field_name, model=model, data=data)

    def get_value(self, seeder: BaseSeeder) -> typing.Any:
        """Resolve relation value via seeder hook or return raw data."""
        if hasattr(seeder, f"set_{self.field_name}"):
            return getattr(seeder, f"set_{self.field_name}")(self.data)
        if hasattr(seeder, f"get_{self.field_name}"):
            return getattr(seeder, f"get_{self.field_name}")(self.data)
        if isinstance(self.data, dict) and "$ref" in self.data:
            return self.retrieve_related_instance()
        return self.data

    def retrieve_related_instance(self) -> models.Model:
        """
        Retrieve an existing related model instance using lookup criteria under `$ref`.

        Expected Payload:
            {"$ref": {"email": "user@example.com"}}
        """
        if not isinstance(self.data, dict):
            raise FieldException(
                self.field_name,
                self.model,
                "Malformed payload; expected dictionary containing '$ref' key.",
            )

        ref_lookup = self.data.get("$ref")
        if not isinstance(ref_lookup, dict):
            raise FieldException(
                self.field_name,
                self.model,
                "Malformed $ref payload; expected dictionary under '$ref' key.",
            )

        # For reverse OneToOne relations, field points back from the target model
        is_reverse_one_to_one = bool(
            getattr(self.field, "one_to_one", False)
            and getattr(self.field, "auto_created", False)
        )
        if is_reverse_one_to_one:
            target_model = self.field.field.model
        else:
            target_model = self.field.related_model

        return target_model._default_manager.get(**ref_lookup)

    def create_related_instance(
        self, seeding_instance: models.Model | None
    ) -> typing.Any:
        """
        Instantiate or look up the related instance.

        Resolves either via `$ref` dictionary lookup or delegating to a child seeder.
        """
        if isinstance(self.data, dict) and "$ref" in self.data:
            self.related_instance = self.retrieve_related_instance()
            return self.related_instance

        if self.field_name in self.related_seeder_map:
            child_seeder_cls = self.related_seeder_map[self.field_name]
            child_seeder = child_seeder_cls()
            self.related_instance = child_seeder.seed_data(
                self.data, parent=seeding_instance
            )
            return self.related_instance

        return None

    def link_relation(self, instance: models.Model) -> None:
        """Attach related instances to the parent model instance."""
        raise NotImplementedError


class ForwardSingularRelation(RelationField):
    """Descriptor for forward ForeignKey and OneToOneField relationships."""

    @property
    def is_required(self) -> bool:
        """
        Determine if the forward foreign key is mandatory for model persistence.

        A forward relation is required if the field on self.model cannot be null,
        or if it participates in a UniqueConstraint or unique_together on self.model.
        """
        if self.field.null or self.field.has_default():
            return False

        if self._constraint_requires_field(self.model, self.field_name):
            return True

        return not self.field.blank

    @staticmethod
    def _constraint_requires_field(model: type[models.Model], field_name: str) -> bool:
        """
        Check if field_name is part of any UniqueConstraint or unique_together on model.
        """
        for constraint in getattr(model._meta, "constraints", []):
            if isinstance(constraint, models.UniqueConstraint):
                if field_name in getattr(constraint, "fields", ()):
                    return True

        for unique_set in getattr(model._meta, "unique_together", ()):
            if field_name in unique_set:
                return True

        return False

    def link_relation(self, instance: models.Model) -> None:
        """Assign related instance and persist the foreign key attribute."""
        if self.related_instance is not None:
            setattr(instance, self.field_name, self.related_instance)
            instance.save(update_fields=[self.field_name])


class ReverseSingularRelation(RelationField):
    """Descriptor for reverse OneToOne relationships."""

    accessor_name: str

    def __init__(
        self,
        related_seeder_map: dict[str, type[BaseSeeder]],
        field_name: str,
        model: type[models.Model],
        data: typing.Any,
    ) -> None:
        super().__init__(
            related_seeder_map=related_seeder_map,
            field_name=field_name,
            model=model,
            data=data,
        )
        # Accessor on the related model that points back to self.model
        self.accessor_name = self.field.field.name

    @property
    def is_required(self) -> bool:
        """Reverse relationships are never required on parent creation."""
        return False

    def create_related_instance(
        self, seeding_instance: models.Model | None
    ) -> typing.Any:
        """Inject parent instance into child data before triggering child seeder."""
        if not (isinstance(self.data, dict) and "$ref" in self.data):
            if seeding_instance is None:
                raise FieldException(
                    self.field_name,
                    self.model,
                    "Parent seeding instance must be provided for reverse relation.",
                )
            if isinstance(self.data, dict):
                self.data[self.accessor_name] = seeding_instance

        return super().create_related_instance(seeding_instance)

    def link_relation(self, instance: models.Model) -> None:
        """Link relation if not already associated during child creation."""
        if self.related_instance is not None:
            if getattr(self.related_instance, self.accessor_name, None) != instance:
                setattr(self.related_instance, self.accessor_name, instance)
                self.related_instance.save(update_fields=[self.accessor_name])


class ManagerRelation(RelationField):
    """Descriptor for forward ManyToMany, reverse ForeignKey, and reverse ManyToMany."""

    accessor_name: str

    def __init__(
        self,
        related_seeder_map: dict[str, type[BaseSeeder]],
        field_name: str,
        model: type[models.Model],
        data: typing.Any,
    ) -> None:
        super().__init__(
            related_seeder_map=related_seeder_map,
            field_name=field_name,
            model=model,
            data=data,
        )
        self.accessor_name = (
            self.field.get_accessor_name()
            if getattr(self.field, "auto_created", False)
            else self.field_name
        )

    @property
    def is_required(self) -> bool:
        """Manager relationships are populated post-save and not required for initial insert."""
        return False

    def link_relation(self, instance: models.Model) -> None:
        """Add seeded related instances to the related manager."""
        if self.related_instance is None:
            return

        related_manager = getattr(instance, self.accessor_name)
        if isinstance(self.related_instance, (list, tuple)):
            related_manager.add(*self.related_instance)
        else:
            related_manager.add(self.related_instance)
