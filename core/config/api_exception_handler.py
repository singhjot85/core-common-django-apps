"""
API Exception Handler for Django Rest Framework.

Translates standard DRF and unhandled Python/Django exceptions into
structured, consistent JSON error responses.
"""

import logging
import typing

from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import ObjectNotFound

LOGGER = logging.getLogger("django.request")


def api_exception_handler(
    exc: Exception, context: typing.Optional[dict[str, typing.Any]] = None
) -> typing.Optional[Response]:
    """
    Handle exceptions raised in DRF views gracefully.

    First delegates to DRF's standard exception handler. If unhandled (returns None),
    maps common framework exceptions (ObjectNotFound, ObjectDoesNotExist, DjangoValidationError)
    or catches unexpected exceptions to return a safe, structured JSON response.

    Args:
        exc: The exception instance raised by the view.
        context: View context dictionary containing view, args, kwargs, and request.

    Returns:
        Response: DRF Response instance with status code and error details.
    """
    # 1. Let DRF handle standard DRF exceptions (APIException, ValidationError, etc.)
    response = drf_exception_handler(exc, context)

    if response is not None:
        return response

    # 2. Handle known Django / core exceptions
    if isinstance(exc, (ObjectNotFound, ObjectDoesNotExist)):
        return Response(
            {"detail": str(exc), "code": "not_found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DjangoValidationError):
        detail = exc.messages if hasattr(exc, "messages") else [str(exc)]
        return Response(
            {"detail": detail, "code": "validation_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Log unexpected errors with traceback
    view_name = "unknown_view"
    if context and "view" in context:
        view_obj = context["view"]
        view_name = getattr(view_obj, "__class__", type(view_obj)).__name__

    LOGGER.error(
        "Unhandled exception in API view %s: %s",
        view_name,
        exc,
        exc_info=exc,
    )

    # 4. Return clean, generic 500 response
    return Response(
        {
            "detail": "An unexpected error occurred. Please try again later.",
            "code": "internal_server_error",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
