from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel

from core.utils.models.soft_delete import DeletionTrackingModel


class BaseModel(UUIDModel, TimeStampedModel, DeletionTrackingModel):
    """Base Model to be used by most of the models,

    Attributes:
        id (uuid): Sets the primary key for the model to a uuid field.
        created (DateTimeField): Adds the created field that gets auto-updated on model creation.
        modified (DateTimeField): Adds the modified field that gets auto-updated on model update(s).
        is_removed (BooleanField): Is the Model Soft Deleted
        removed_by (ForeignKey): User that deleted the instance
    """

    DEFAULT_ORDERING = ("-created", "-modified", "-pk")

    class Meta:
        abstract = True

    @classmethod
    def get_object(cls, **unique_filters) -> models.Model:
        """
        Getter to fetch database object for current class
        It uses ``available_objects.get``, as we have ``SotDeleteModel``, this is necessary

        Kwargs:
            unique_filters that define's a unique object

        Raises:
            ObjectNotFound
        """
        from core.utils.models.helpers import safe_get_object_or_raise  # noqa: PLC0415

        return safe_get_object_or_raise(cls, **unique_filters)
