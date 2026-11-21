"""
Base persistence strategies for database seeders.
"""

from __future__ import annotations

import logging
import typing

from django.core.exceptions import FieldDoesNotExist, ValidationError

from core.libraries.seeder.exceptions import InvalidFieldError
from core.libraries.seeder.fields import (
    ForwardSingularRelation,
    ManagerRelation,
    RelationField,
    ReverseSingularRelation,
    SeederField,
)

if typing.TYPE_CHECKING:
    from django.db import models

    from core.libraries.seeder.seeder import BaseSeeder

LOGGER = logging.getLogger(__name__)


class BaseObjectMethods:
    """
    Base strategy class managing model object extraction, validation, and persistence.
    """

    model: type[models.Model]
    related_seeder_map: dict[str, type[BaseSeeder]]
    fields: list[str]
    seed_method: str = "create"

    def __init__(
        self,
        model: type[models.Model],
        related_seeder_map: dict[str, type[BaseSeeder]] | None = None,
        fields: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        self.model = model
        self.related_seeder_map = related_seeder_map or {}
        self.fields = list(fields) if fields is not None else []

    def _create_field(self, field_name: str, value: typing.Any) -> SeederField | None:
        """
        Map a field name and value to a concrete SeederField or RelationField descriptor.

        Returns None if field_name is not configured in allowed self.fields.
        """
        if field_name not in self.fields:
            LOGGER.warning(
                "Field '%s' is not declared for seeder %s; skipping.",
                field_name,
                self.model.__name__,
            )
            return None

        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return SeederField(field_name=field_name, model=self.model, data=value)

        # Standard non-relational model field
        if field.concrete and not field.is_relation:
            return SeederField(field_name=field_name, model=self.model, data=value)

        # Forward ForeignKey or forward OneToOneField
        if field.many_to_one or (field.one_to_one and not field.auto_created):
            return ForwardSingularRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        # Reverse OneToOneField
        if field.one_to_one and field.auto_created:
            return ReverseSingularRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        # ManyToManyField (forward/reverse) or reverse ForeignKey (one_to_many)
        if field.many_to_many or field.one_to_many:
            return ManagerRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        raise InvalidFieldError(field_name, self.model)

    def prepare_fields(self, data: dict) -> list[SeederField]:
        """Convert input data dictionary into prepared SeederField descriptors."""
        cleaned_fields: list[SeederField] = []
        for field_name, value in data.items():
            field_descriptor = self._create_field(field_name, value)
            if field_descriptor is not None:
                cleaned_fields.append(field_descriptor)

        return cleaned_fields

    def split_fields(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> tuple[dict[str, typing.Any], list[RelationField]]:
        """
        Separate regular field values from non-required relation descriptors.

        Does not trigger side-effecting database creation for relationships.
        """
        create_kwargs: dict[str, typing.Any] = {}
        related_fields: list[RelationField] = []

        for field in prepared_fields:
            is_ref = isinstance(field.data, dict) and "$ref" in field.data
            if (
                field.field is not None
                and field.field.is_relation
                and not field.is_required
                and not is_ref
            ):
                if isinstance(field, RelationField):
                    related_fields.append(field)
            else:
                create_kwargs[field.field_name] = field.get_value(seeder)

        return create_kwargs, related_fields

    def run_full_clean(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> None:
        """
        Validate data against model field validation rules without creating related DB rows.
        """
        try:
            probe_kwargs: dict[str, typing.Any] = {}
            excluded_fields: list[str] = []

            for field in prepared_fields:
                if field.field is not None and field.field.is_relation:
                    excluded_fields.append(field.field_name)
                elif field.field is not None:
                    probe_kwargs[field.field_name] = field.get_value(seeder)

            probe = self.model(**probe_kwargs)
            probe.full_clean(exclude=excluded_fields, validate_unique=False)
        except ValidationError as exc:
            LOGGER.error("Validation failed for model %s: %s", self.model.__name__, exc)
            raise
        except Exception as exc:
            LOGGER.error(
                "Unexpected error during validation for model %s",
                self.model.__name__,
                exc_info=exc,
            )
            raise

    def _link_related_instances(
        self, instance: models.Model, related_fields: list[RelationField]
    ) -> None:
        """Create and link all related child instances post-parent persistence."""
        for field in related_fields:
            try:
                field.create_related_instance(instance)
                field.link_relation(instance)
            except Exception as exc:
                LOGGER.error(
                    "Error linking relation '%s' to %s: %s",
                    field.field_name,
                    instance,
                    exc,
                    exc_info=exc,
                )
                raise

    def perform_seed(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> models.Model:
        """Persist model instance using the configured manager seed method."""
        create_kwargs, related_fields = self.split_fields(prepared_fields, seeder)
        manager = self.model._default_manager
        instance = getattr(manager, self.seed_method)(**create_kwargs)

        LOGGER.info("Seeded instance for model %s: %s", self.model.__name__, instance)
        self._link_related_instances(instance, related_fields)
        return instance

    def seed(self, data: dict, seeder: BaseSeeder) -> models.Model:
        """Execute full seeding pipeline: prepare fields, validate, and persist."""
        prepared_fields = self.prepare_fields(data)
        self.run_full_clean(prepared_fields, seeder)
        return self.perform_seed(prepared_fields, seeder)
