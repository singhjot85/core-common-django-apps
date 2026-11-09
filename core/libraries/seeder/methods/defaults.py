import logging
from functools import lru_cache

from django.core.exceptions import ValidationError

from core.libraries.seeder.fields import SeederField
from core.libraries.seeder.methods.base import BaseObjectMethods

LOGGER = logging.getLogger(__name__)


class GetorCreateObject(BaseObjectMethods):
    """ """

    lookup_fields: list[str]
    default_fields: list[str]
    seed_method = "get_or_create"

    def __init__(
        self,
        model,
        related_seeder_map,
        lookup_fields: list | tuple,
        default_fields: list | tuple,
    ):
        """ """

        self.lookup_fields = lookup_fields
        self.default_fields = default_fields

        fields = list(self.lookup_fields).extend(self.default_fields)

        super().__init__(
            model,
            related_seeder_map,
            fields=fields,
        )

    @lru_cache  # noqa: B019
    def split_fields(self, prepared_fields: list[SeederField], seeder):
        """ """
        lookups, defaults, self.related_fields = ({}, {}, [])
        for field in prepared_fields:
            if field.field_name in self.lookup_fields:
                lookups[field.field_name] = field.get_value(seeder)

            if field.field_name in self.default_fields:
                # Only filter out fields that are required
                if field.field.is_relation and not field.is_required:
                    self.related_fields.append(field)

                defaults[field.field_name] = field.get_value(seeder)

        return lookups, defaults

    def run_full_clean(self, prepared_fields: list[SeederField], seeder):
        """ """
        try:
            lookups, defaults = self.split_fields(prepared_fields, seeder)
            probe = self.model(**{**lookups, **defaults})
            probe.full_clean(exclude=[f for f in lookups])
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
            lookups, defaults = self.split_fields(prepared_fields, seeder)
            instance, created = getattr(self.model.objects, self.seed_method)(
                defaults, **lookups
            )
            LOGGER.info(
                f"Created a new instance for model: {self.model.__name__} >>> {instance}"
            )
        except Exception as e:
            LOGGER.error(
                f"Error in creating instance for model: {self.model.__name__}",
                exc_info=e,
            )
            raise e

        if created:
            self._link_related_instances(instance)

        return instance


class UpdateOrCreateObject(GetorCreateObject):
    """ """

    lookup_fields: list[str]
    default_fields: list[str]
    seed_method = "update_or_create"

    def __init__(
        self,
        model,
        related_seeder_map,
        lookup_fields: list | tuple,
        default_fields: list | tuple,
    ):
        """ """

        self.lookup_fields = lookup_fields
        self.default_fields = default_fields

        fields = list(self.lookup_fields).extend(self.default_fields)

        super().__init__(
            model,
            related_seeder_map,
            fields=fields,
        )

    def create_object(self, related_fields, default, **lookup):
        """ """
        instance, created = self.model._default_manager.update_or_create(
            defaults=default, **lookup
        )

        return instance, created


class CreateObject(BaseObjectMethods):
    """ """

    seed_method = "create"


class UpdateObject(BaseObjectMethods):
    """ """

    seed_method = "update"
