"""
Request logging and performance telemetry middleware.

Captures and records HTTP request metadata, latency, and tenant context.
"""

import logging
import time
import typing
from urllib.parse import urlencode

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse

from core.utils.error_handling.content_masking import ContentMaskingUtils

LOGGER = logging.getLogger(__name__)
REQUEST_LOGGER = logging.getLogger("core.requests")
PERF_LOGGER = logging.getLogger("performance")


class RequestLoggingMiddleware:
    """
    Middleware that logs incoming HTTP requests and performance telemetry.

    Captures:
    - HTTP method, path, query parameters (scrubbed of secrets/PII).
    - Response status code, execution duration in milliseconds.
    - Remote client IP, authenticated user identity, and tenant schema.

    Dispatches detailed request traces to 'core.requests' and execution latency
    metrics to 'performance'.
    """

    def __init__(
        self, get_response: typing.Callable[[HttpRequest], HttpResponse]
    ) -> None:
        """
        Initialize the middleware with the next handler in the chain.

        Args:
            get_response: Next middleware or view handler.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the incoming request and log its metadata and latency.

        Args:
            request: Incoming Django HttpRequest.

        Returns:
            HttpResponse: Outgoing Django HttpResponse.
        """
        start_time = time.perf_counter()
        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = getattr(response, "status_code", 500) if response else 500
            self._log_request(request, status_code, duration_ms)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Extract the client IP address from request headers or remote address.

        Args:
            request: Incoming Django HttpRequest.

        Returns:
            str: Client IP address string.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _log_request(
        self, request: HttpRequest, status_code: int, duration_ms: float
    ) -> None:
        """
        Safely construct and emit request trace and latency records.

        Args:
            request: The processed HttpRequest.
            status_code: HTTP response status code.
            duration_ms: Processing duration in milliseconds.
        """
        try:
            method = request.method
            path = request.path
            client_ip = self._get_client_ip(request)

            user_repr = "anonymous"
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                user_id = getattr(user, "id", None) or getattr(user, "pk", None)
                username = getattr(user, "username", getattr(user, "email", "user"))
                user_repr = f"{username}:{user_id}"

            schema_name = getattr(connection, "schema_name", "public")

            # Sanitize query parameters to prevent leaking secrets/PII unless disabled in local env
            query_str = ""
            if request.GET:
                if getattr(settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False):
                    params = request.GET.dict()
                else:
                    params = ContentMaskingUtils.filter_sensitive_content(
                        **request.GET.dict()
                    )
                query_str = f"?{urlencode(params)}"

            log_message = (
                f"[{method}] {path}{query_str} -> {status_code} "
                f"({duration_ms:.2f}ms) | User: {user_repr} | IP: {client_ip} | Schema: {schema_name}"
            )
            REQUEST_LOGGER.info(log_message)

            # Performance telemetry
            PERF_LOGGER.debug(
                "API Latency: [%s] %s -> %s (%.2fms) [User: %s | Schema: %s]",
                method,
                path,
                status_code,
                duration_ms,
                user_repr,
                schema_name,
            )
        except Exception:
            # Request logging must never fail the application request
            LOGGER.debug("Failed to log request details", exc_info=True)
