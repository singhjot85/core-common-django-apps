from django.db import models

from .content_masking import ContentMaskingUtils


class InvalidTypeError(TypeError):
    """
    Common Error util to raise an invalid type error
    """

    def __init__(self, type, expected):
        message = f"Invalid data of type: {type}, expected: {expected}"
        super().__init__(message)


class ObjectNotFound(Exception):
    """
    Raised when an object is not found in the database.
    Automatically includes model information when available.
    """

    model: "models.Model"
    message: str

    DEFAULT_MODEL_NAME = "Object"

    def __init__(self, model=None, message=None, *args, **lookup_kwargs):
        self.model = model
        self.lookup_kwargs = lookup_kwargs

        super().__init__(message)

    def _get_model_name(self):

        if not self.model:
            return self.DEFAULT_MODEL_NAME

        if hasattr(self.model, "_meta"):
            return self.model._meta.verbose_name.title()

        return self.model.__name__

    def _build_message(self):

        model_name = self._get_model_name()

        if self.lookup_kwargs:
            lookup_str = ContentMaskingUtils.filter_sensitive_content(
                stringified=True, deep_search=True, **self.lookup_kwargs
            )

            return f"{model_name} with {lookup_str} not found"

        return f"{model_name} not found"


class CycleError(ValueError):
    """
    Raised when a circular dependency or cycle is detected in a graph.
    """

    pass


class SeederException(Exception):
    """General Exception raised when from seeder."""

    pass


class ObjectCreatorException(Exception):
    """
    General Exception raised when creating an object.
    """

    pass


class RegistryException(Exception):
    """Raise when re-registring something to registry."""

    pass
