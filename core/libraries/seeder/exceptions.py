"""
Domain exceptions for seeder framework.

Defines formatted, contextual exceptions raised during seeder registration,
data loading, field transformation, and DAG execution.
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from django.db import models


class SeederDataLoaderException(Exception):
    """
    Raised when a data loader fails to discover, read, or parse data.

    Args:
        loader_type (str): Identifier of the loader that failed (e.g. 'file_loader').
        message (str): Detailed error description from the underlying failure.
    """

    def __init__(self, loader_type: str, message: str, *args):
        formatted_message = f"Exception loading data from {loader_type}: {message}"
        super().__init__(formatted_message, *args)


class SeederException(Exception):
    """
    Base exception for all runtime errors encountered during seeder execution.

    Prefixes the message with ``[<label>]`` when a seeder label is provided.

    Args:
        label (str, optional): Label of the failing seeder or runner component.
        message (str): Failure reason or wrapped exception message.
    """

    def __init__(self, label: str | None = None, message: str = "", *args):
        formatted_message = f"[{label}] {message}" if label else message
        super().__init__(formatted_message, *args)


class InvalidFieldError(Exception):
    """
    Raised when an undeclared or unresolvable field descriptor is processed.

    Args:
        field_name (str): Name of the invalid field attribute.
        model_kls (type[models.Model]): Target Django model class.
    """

    def __init__(self, field_name: str, model_kls: type[models.Model], *args):
        message = f"'{field_name}' is an invalid field for model: {model_kls.__name__}"
        super().__init__(message, *args)


class FieldException(Exception):
    """
    Raised when a field-level transform, validation, or relation retrieval fails.

    Args:
        field_name (str): Name of the field that encountered an error.
        model_kls (type[models.Model]): Target Django model class.
        message (str): Explanation of why field resolution failed.
    """

    def __init__(
        self, field_name: str, model_kls: type[models.Model], message: str, *args
    ):
        formatted_message = (
            f"Error in field '{field_name}' of model '{model_kls.__name__}': {message}"
        )
        super().__init__(formatted_message, *args)
