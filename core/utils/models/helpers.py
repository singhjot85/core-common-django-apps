import logging

from django.db import models
from model_utils.models import SoftDeletableModel

LOGGER = logging.getLogger(__name__)


def get_object_or_raise(model: type[models.Model], **lookup_kwargs):
    """Get object or raise ObjectNotFound with context"""
    from core.exceptions import ObjectNotFound

    try:
        if isinstance(model, SoftDeletableModel):
            return model.available_objects.get(**lookup_kwargs)

        return model.objects.get(**lookup_kwargs)
    except model.DoesNotExist:
        raise ObjectNotFound(model=model, **lookup_kwargs)


def safe_get_object_or_raise(model: type["models.Model"], **lookup_kwargs):
    """
    Get object or raise ObjectNotFound with context
    Safe Get the object, if multiple found log the error
    and re-query the db for single instance based on model's ``DEFAULT_ORDERING``
    if no such attribute found fallback to ``-pk``
    """
    from core.exceptions import ObjectNotFound

    try:
        if isinstance(model, SoftDeletableModel):
            return model.available_objects.get(**lookup_kwargs)

        return model.objects.get(**lookup_kwargs)
    except model.MultipleObjectsReturned as exc:
        LOGGER.error(msg="Multiple Objects found for a unique dataset", exc_info=exc)
        return (
            filter_objects_or_raise(model, **lookup_kwargs)
            .order_by(getattr(model, "DEFAULT_ORDERING", "-pk"))
            .first()
        )
    except model.DoesNotExist:
        raise ObjectNotFound(model=model, **lookup_kwargs)


def filter_objects_or_raise(
    model: type["models.Model"], **lookup_kwargs
) -> "models.QuerySet":
    """Filter for a queryset or raise ObjectNotFound"""
    from core.exceptions import ObjectNotFound

    qs = None

    if isinstance(model, SoftDeletableModel):
        qs = model.available_objects.filter(**lookup_kwargs)
    else:
        qs = model.objects.get(**lookup_kwargs)

    if not qs:
        raise ObjectNotFound(model, **lookup_kwargs)

    return qs
