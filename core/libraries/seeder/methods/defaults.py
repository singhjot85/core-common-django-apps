"""
Standard object creation strategies for database seeders.
"""

from __future__ import annotations

import logging
import typing

from django.core.exceptions import ValidationError

from core.libraries.seeder.fields import RelationField, SeederField
from core.libraries.seeder.methods.base import BaseObjectMethods

if typing.TYPE_CHECKING:
    from django.db import models

    from core.libraries.seeder.seeder import BaseSeeder

LOGGER = logging.getLogger(__name__)


class GetorCreateObject(BaseObjectMethods):
    """
    Persistence strategy utilizing ``Model.objects.get_or_create``.

    Separates unique identity lookup fields from default mutable attributes.
    Guarantees idempotence: running the seeder repeatedly will find existing
    rows without attempting duplicate inserts.
    """

    lookup_fields: list[str]
    default_fields: list[str]
    seed_method: str = "get_or_create"

    def __init__(
        self,
        model: type[models.Model],
        lookup_fields: list[str] | tuple[str, ...],
        default_fields: list[str] | tuple[str, ...],
        related_seeder_map: dict[str, type[BaseSeeder]] | None = None,
    ) -> None:
        """
        Initialize GetorCreateObject persistence strategy.

        Args:
            model (type[models.Model]): Target Django model class.
            lookup_fields (list[str] | tuple[str, ...]): Fields used to match existing records.
            default_fields (list[str] | tuple[str, ...]): Fields populated when creating a new record.
            related_seeder_map (dict[str, type[BaseSeeder]], optional): Child seeders for relation fields.
        """
        self.lookup_fields = list(lookup_fields)
        self.default_fields = list(default_fields)
        combined_fields = self.lookup_fields + self.default_fields

        super().__init__(
            model=model,
            related_seeder_map=related_seeder_map,
            fields=combined_fields,
        )

    def split_fields(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> tuple[dict[str, typing.Any], dict[str, typing.Any], list[RelationField]]:
        """
        Split prepared fields into lookups, defaults, and post-persistence relation descriptors.

        Forward relations ($ref) are kept in defaults or lookups to ensure non-null FK columns
        are present at insert time.

        Args:
            prepared_fields (list[SeederField]): Prepared field descriptors.
            seeder (BaseSeeder): Active seeder instance.

        Returns:
            tuple[dict[str, typing.Any], dict[str, typing.Any], list[RelationField]]:
                - lookups: Kwargs for get_or_create lookup.
                - defaults: Kwargs passed as defaults dict.
                - related_fields: Non-required relation descriptors to link post-save.
        """
        lookups: dict[str, typing.Any] = {}
        defaults: dict[str, typing.Any] = {}
        related_fields: list[RelationField] = []

        for field in prepared_fields:
            is_ref = isinstance(field.data, dict) and "$ref" in field.data
            if field.field_name in self.lookup_fields:
                lookups[field.field_name] = field.get_value(seeder)
            elif field.field_name in self.default_fields:
                if (
                    field.field is not None
                    and field.field.is_relation
                    and not field.is_required
                    and not is_ref
                ):
                    if isinstance(field, RelationField):
                        related_fields.append(field)
                else:
                    defaults[field.field_name] = field.get_value(seeder)

        return lookups, defaults, related_fields

    def run_full_clean(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> None:
        """
        Validate non-relation probe attributes without writing to database.

        Filters probe attributes against genuine model fields to avoid TypeErrors
        on virtual or custom manager flags.

        Args:
            prepared_fields (list[SeederField]): Prepared field descriptors.
            seeder (BaseSeeder): Active seeder instance.

        Raises:
            ValidationError: If model validation rules fail.
        """
        try:
            lookups, defaults, _ = self.split_fields(prepared_fields, seeder)
            model_field_names = {f.name for f in self.model._meta.get_fields()}
            probe_kwargs = {
                k: v
                for k, v in {**lookups, **defaults}.items()
                if k in model_field_names
            }
            probe = self.model(**probe_kwargs)
            probe.full_clean(exclude=list(lookups.keys()), validate_unique=False)
        except ValidationError as exc:
            LOGGER.error("Validation failed for model %s: %s", self.model.__name__, exc)
            raise
        except Exception as exc:
            LOGGER.error(
                "Unexpected error validating model %s",
                self.model.__name__,
                exc_info=exc,
            )
            raise

    def perform_seed(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> models.Model:
        """
        Execute get_or_create and attach related instances.

        Args:
            prepared_fields (list[SeederField]): List of prepared field descriptors.
            seeder (BaseSeeder): Active seeder instance.

        Returns:
            models.Model: Found existing or newly created model instance.

        Side effects:
            - Queries and potentially inserts record and child relations in database.
        """
        lookups, defaults, related_fields = self.split_fields(prepared_fields, seeder)
        manager = self.model._default_manager
        instance, created = manager.get_or_create(defaults=defaults, **lookups)

        LOGGER.info(
            "%s instance for model %s: %s",
            "Created" if created else "Found existing",
            self.model.__name__,
            instance,
        )

        if created or related_fields:
            self._link_related_instances(instance, related_fields)

        return instance


class UpdateOrCreateObject(GetorCreateObject):
    """
    Persistence strategy utilizing ``Model.objects.update_or_create``.

    Updates mutable fields if the record already exists, or inserts a new record.
    """

    seed_method: str = "update_or_create"

    def perform_seed(
        self, prepared_fields: list[SeederField], seeder: BaseSeeder
    ) -> models.Model:
        """
        Execute update_or_create and attach related instances.

        Args:
            prepared_fields (list[SeederField]): List of prepared field descriptors.
            seeder (BaseSeeder): Active seeder instance.

        Returns:
            models.Model: Updated or newly created model instance.

        Side effects:
            - Performs database update or insert.
        """
        lookups, defaults, related_fields = self.split_fields(prepared_fields, seeder)
        manager = self.model._default_manager
        instance, created = manager.update_or_create(defaults=defaults, **lookups)

        LOGGER.info(
            "%s instance for model %s: %s",
            "Created" if created else "Updated",
            self.model.__name__,
            instance,
        )

        self._link_related_instances(instance, related_fields)
        return instance


class CreateObject(BaseObjectMethods):
    """
    Persistence strategy directly creating new records via ``Model.objects.create``.

    Use only when entities lack natural unique lookup fields and always require new rows.
    """

    seed_method: str = "create"

    def __init__(
        self,
        model: type[models.Model],
        fields: list[str] | tuple[str, ...],
        related_seeder_map: dict[str, type[BaseSeeder]] | None = None,
    ) -> None:
        """
        Initialize CreateObject persistence strategy.

        Args:
            model (type[models.Model]): Target Django model class.
            fields (list[str] | tuple[str, ...]): Fields passed to Model.objects.create().
            related_seeder_map (dict[str, type[BaseSeeder]], optional): Child seeders for relation fields.
        """
        super().__init__(
            model=model,
            related_seeder_map=related_seeder_map,
            fields=fields,
        )
