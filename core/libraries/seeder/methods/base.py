import logging
import typing
from functools import lru_cache

from django.core.exceptions import ValidationError
from django.db import models

from core.libraries.seeder.fields import (
    ForwardSingularRelation,
    InvalidFieldError,
    ManagerRelation,
    ReverseSingularRelation,
    SeederField,
)

if typing.TYPE_CHECKING:
    from core.libraries.seeder import BaseSeeder
    from core.libraries.seeder.fields import RelationField

LOGGER = logging.getLogger(__name__)


class BaseObjectMethods:
    """
    Base class to store object methods and its configurations.
    """

    model: type["models.Model"]
    related_seeder_map: dict[str, "BaseSeeder"]
    fields: list[str]
    seed_method = "create"

    def __init__(
        self,
        model: type["models.Model"],
        related_seeder_map: dict[str, "BaseSeeder"],
        fields: list[str],
    ):
        """ """
        self.model = model
        self.related_seeder_map = related_seeder_map

        self.fields = fields

    def _create_field(self, field_name, value):
        """ """
        field = self.model._meta.get_field(field_name)

        if field_name not in self.fields:
            LOGGER.warning(
                f"Field {field_name} is not included in seeder but passed in data"
            )
            return None

        if field.concrete and not field.is_relation:
            return SeederField(field_name=field_name, model=self.model, data=value)

        # Handle both ForeignKey and OneToOne
        if field.many_to_one or (field.one_to_one and not field.auto_created):
            return ForwardSingularRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        # Handle reverse OneToOne
        elif field.one_to_one and field.auto_created:
            return ReverseSingularRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        # Handle ManyToMany, reverse ForeignKey and reverse ManyToMany
        elif field.many_to_many or field.one_to_many:
            return ManagerRelation(
                related_seeder_map=self.related_seeder_map,
                field_name=field_name,
                model=self.model,
                data=value,
            )

        raise InvalidFieldError(field_name, self.model)

    def prepare_fields(self, data: dict) -> list[SeederField]:
        """ """
        cleaned_data = []
        for field_name, value in data.items():
            try:
                if field := self._create_field(field_name, value):
                    cleaned_data.append(field)
            except Exception as e:
                LOGGER.error(f"Error cleaning field: {field_name}")
                raise e

        return cleaned_data

    @lru_cache  # noqa: B019
    def split_fields(self, prepared_fields: list[SeederField], seeder):
        """ """
        self.related_fields: list[RelationField] = []
        create_kwargs = {}
        for field in prepared_fields:
            if field.field.is_relation and not field.is_required:
                self.related_fields.append[field]
            else:
                create_kwargs[field.field_name] = field.get_value(seeder)

        return create_kwargs

    def run_full_clean(self, prepared_fields: list[SeederField], seeder):
        """ """
        try:
            create_kwargs = self.split_fields(prepared_fields, seeder)
            probe = self.model(**create_kwargs)
            probe.full_clean()
        except ValidationError as e:
            LOGGER.error(f"Invalid data for seeding model: {self.model.__name__}")
            raise e
        except Exception as e:
            LOGGER.error(
                f"Unknown error in cleaning data for model: {self.model.__name__}",
                exc_info=e,
            )
            raise e

    def perform_seed(self, prepared_fields: list[SeederField], seeder):
        """ """
        try:
            create_kwargs = self.split_fields(prepared_fields, seeder)
            instance = getattr(self.model.objects, self.seed_method)(**create_kwargs)
            LOGGER.info(
                f"Created a new instance for model: {self.model.__name__} >>> {instance}"
            )
        except Exception as e:
            LOGGER.error(
                f"Error in creating instance for model: {self.model.__name__}",
                exc_info=e,
            )
            raise e

        self._link_related_instances(instance)
        return instance

    def _link_related_instances(self, instance: models.Model):
        """ """

        if not self.related_fields:
            return

        for field in self.related_fields:
            try:
                field.create_related_instance(instance)
                field.link_relation(instance)
            except Exception as e:
                LOGGER.error(
                    f"Error linking related instance: {field.field_name} to instance: {instance}"
                )
                raise e

    def seed(self, data: dict, seeder: "BaseSeeder") -> "models.Model":
        """
        Seed the instance to database using the configured methods logic.
        """
        # Phase 1: Raw → validated Python values
        prepared_fields = self.prepare_fields(data)  # calls field.clean() per field
        self.run_full_clean(prepared_fields, seeder)
        instance = self.perform_seed()

        return instance
