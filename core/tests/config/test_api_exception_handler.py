"""
Unit tests for DRF API exception handler.

Validates delegation of standard DRF exceptions, mapping of Django and core exceptions,
and graceful 500 JSON error handling for unhandled view errors.
"""

from unittest.mock import patch

from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError as DjangoValidationError,
)
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    PermissionDenied,
    ValidationError as DRFValidationError,
)

from core.config.api_exception_handler import api_exception_handler
from core.exceptions import ObjectNotFound


class DummyAPIView:
    """Dummy view class used for exception handler context."""

    pass


class TestAPIExceptionHandler:
    """Test suite for api_exception_handler."""

    def test_drf_validation_error_delegation(self):
        """DRF ValidationErrors are handled and formatted by DRF's base handler."""
        exc = DRFValidationError({"field": ["This field is required."]})
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "field" in response.data

    def test_drf_permission_denied_delegation(self):
        """DRF PermissionDenied exceptions return HTTP 403."""
        exc = PermissionDenied("You do not have permission.")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "You do not have permission."

    def test_drf_authentication_failed_delegation(self):
        """DRF AuthenticationFailed exceptions return HTTP 401."""
        exc = AuthenticationFailed("Invalid token.")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_django_object_does_not_exist_maps_to_404(self):
        """Django ObjectDoesNotExist translates to HTTP 404 with structured JSON."""
        exc = ObjectDoesNotExist("Customer matching query does not exist.")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Customer matching query does not exist."
        assert response.data["code"] == "not_found"

    def test_core_object_not_found_maps_to_404(self):
        """Core ObjectNotFound translates to HTTP 404 with structured JSON."""
        exc = ObjectNotFound(message="Item not found")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Item not found"
        assert response.data["code"] == "not_found"

    def test_django_validation_error_maps_to_400(self):
        """Django core ValidationError translates to HTTP 400 with structured JSON."""
        exc = DjangoValidationError("Invalid postal code format.")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "validation_error"
        assert "Invalid postal code format." in response.data["detail"]

    @patch("core.config.api_exception_handler.LOGGER.error")
    def test_unhandled_generic_exception_returns_500(self, mock_logger_error):
        """Unexpected Python exceptions log error with traceback and return generic 500 JSON."""
        exc = RuntimeError("Database connection pool exhausted")
        context = {"view": DummyAPIView()}

        response = api_exception_handler(exc, context)

        assert response is not None
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["code"] == "internal_server_error"
        assert (
            response.data["detail"]
            == "An unexpected error occurred. Please try again later."
        )

        mock_logger_error.assert_called_once()
        assert "DummyAPIView" in mock_logger_error.call_args[0][1]
