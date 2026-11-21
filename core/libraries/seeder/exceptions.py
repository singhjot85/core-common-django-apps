"""
Domain exceptions for seeder framework.
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from django.db import models


class SeederDataLoaderException(Exception):
    """Exception raised during seeder data loading."""

    def __init__(self, loader_type: str, message: str, *args):
        formatted_message = f"Exception loading data from {loader_type}: {message}"
        super().__init__(formatted_message, *args)


class SeederException(Exception):
    """Base exception for seeder execution errors."""

    def __init__(self, label: str | None = None, message: str = "", *args):
        formatted_message = f"[{label}] {message}" if label else message
        super().__init__(formatted_message, *args)


class InvalidFieldError(Exception):
    """Exception raised when an invalid field is encountered."""

    def __init__(self, field_name: str, model_kls: type[models.Model], *args):
        message = f"'{field_name}' is an invalid field for model: {model_kls.__name__}"
        super().__init__(message, *args)


class FieldException(Exception):
    """Exception raised for field-specific processing errors."""

    def __init__(
        self, field_name: str, model_kls: type[models.Model], message: str, *args
    ):
        formatted_message = (
            f"Error in field '{field_name}' of model '{model_kls.__name__}': {message}"
        )
        super().__init__(formatted_message, *args)
