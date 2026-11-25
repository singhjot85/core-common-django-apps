"""
Request logging and performance telemetry middleware.

Captures and records HTTP request metadata, headers, payload, response data,
latency, and tenant context.
"""

import json
import logging
import time
import typing
from urllib.parse import urlencode

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse

from core.utils.error_handling.content_masking import ContentMaskingUtils

LOGGER = logging.getLogger(__name__)
REQUEST_LOGGER = logging.getLogger("core.requests")
PERF_LOGGER = logging.getLogger("performance")

DEFAULT_MAX_PAYLOAD_LENGTH = 1000
SENSITIVE_HEADER_KEYS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
        "x-auth-token",
        "token",
    }
)


class RequestLoggingMiddleware:
    """
    Middleware that logs incoming HTTP requests, headers, payloads, responses, and latency.

    Captures:
    - HTTP method, full URL, query parameters.
    - Request headers (with sensitive auth tokens and cookies sanitized).
    - Request payload (JSON, form fields, or file upload descriptors with size truncation).
    - Response status code, latency duration, and response body (with size truncation).
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
            self._log_request(request, response, status_code, duration_ms)

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

    def _truncate_text(
        self, text: str, max_len: int = DEFAULT_MAX_PAYLOAD_LENGTH
    ) -> str:
        """
        Truncate strings that exceed max_len with a descriptive suffix.

        Args:
            text: Input string.
            max_len: Maximum length limit.

        Returns:
            str: Truncated or original string.
        """
        if len(text) > max_len:
            excess = len(text) - max_len
            return f"{text[:max_len]}... [truncated {excess} chars]"
        return text

    def _format_headers(self, request: HttpRequest) -> dict[str, typing.Any]:
        """
        Extract and sanitize request headers.

        Args:
            request: Incoming HttpRequest.

        Returns:
            dict[str, Any]: Sanitized request headers.
        """
        headers: dict[str, typing.Any] = {}
        disable_filter = getattr(settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False)

        for header_name, header_value in request.headers.items():
            if not disable_filter and header_name.lower() in SENSITIVE_HEADER_KEYS:
                headers[header_name] = "********"
            else:
                headers[header_name] = self._truncate_text(str(header_value), 256)

        return headers

    def _format_request_body(self, request: HttpRequest) -> str:
        """
        Safely extract, format, and truncate incoming request payload.

        Handles JSON bodies, standard form submissions, file uploads, and raw data.

        Args:
            request: Incoming HttpRequest.

        Returns:
            str: Formatted request body description or JSON.
        """
        disable_filter = getattr(settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False)

        # Handle uploaded files metadata
        files_summary: dict[str, str] = {}
        if request.FILES:
            for file_key, uploaded_file in request.FILES.items():
                size = getattr(uploaded_file, "size", 0)
                name = getattr(uploaded_file, "name", "unknown")
                content_type = getattr(
                    uploaded_file, "content_type", "application/octet-stream"
                )
                files_summary[file_key] = (
                    f"<file: {name}, size: {size} bytes, type: {content_type}>"
                )

        # Handle POST form data
        if request.POST:
            form_dict = request.POST.dict()
            if files_summary:
                form_dict.update(files_summary)
            if not disable_filter:
                form_dict = ContentMaskingUtils.filter_sensitive_content(
                    deep_search=True, **form_dict
                )
            return self._truncate_text(json.dumps(form_dict, default=str))

        if files_summary:
            return json.dumps(files_summary)

        # Handle raw body (e.g., application/json)
        try:
            body = request.body
            if not body:
                return ""
            raw_text = body.decode("utf-8", errors="replace").strip()
            if not raw_text:
                return ""

            # Attempt JSON parse for formatting and sensitive field scrubbing
            try:
                parsed_json = json.loads(raw_text)
                if isinstance(parsed_json, dict) and not disable_filter:
                    parsed_json = ContentMaskingUtils.filter_sensitive_content(
                        deep_search=True, **parsed_json
                    )
                return self._truncate_text(json.dumps(parsed_json, default=str))
            except Exception:
                return self._truncate_text(raw_text)
        except Exception:
            return "<binary or unreadable stream>"

    def _format_response_body(self, response: typing.Optional[HttpResponse]) -> str:
        """
        Safely extract, format, and truncate outgoing response content.

        Args:
            response: Outgoing HttpResponse object.

        Returns:
            str: Formatted response body description or JSON.
        """
        if response is None:
            return "<no response>"

        if isinstance(response, StreamingHttpResponse):
            return "<streaming response>"

        content_type = response.headers.get("Content-Type", "")
        if (
            "application/octet-stream" in content_type
            or "image/" in content_type
            or "pdf" in content_type
        ):
            length = len(response.content) if hasattr(response, "content") else 0
            return f"<binary data: {content_type}, {length} bytes>"

        try:
            content = response.content
            if not content:
                return ""
            text = content.decode("utf-8", errors="replace").strip()
            if not text:
                return ""

            disable_filter = getattr(
                settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False
            )
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict) and not disable_filter:
                    parsed = ContentMaskingUtils.filter_sensitive_content(
                        deep_search=True, **parsed
                    )
                return self._truncate_text(json.dumps(parsed, default=str))
            except Exception:
                return self._truncate_text(text)
        except Exception:
            return "<binary or unreadable content>"

    def _log_request(
        self,
        request: HttpRequest,
        response: typing.Optional[HttpResponse],
        status_code: int,
        duration_ms: float,
    ) -> None:
        """
        Safely construct and emit request trace and latency records.

        Args:
            request: The processed HttpRequest.
            response: The returned HttpResponse (if any).
            status_code: HTTP response status code.
            duration_ms: Processing duration in milliseconds.
        """
        try:
            method = request.method
            full_path = request.get_full_path()
            client_ip = self._get_client_ip(request)

            user_repr = "anonymous"
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                user_id = getattr(user, "id", None) or getattr(user, "pk", None)
                username = getattr(user, "username", getattr(user, "email", "user"))
                user_repr = f"{username}:{user_id}"

            schema_name = getattr(connection, "schema_name", "public")

            # Extract sanitized query string
            disable_filter = getattr(
                settings, "DISABLE_SENSITIVE_CONTENT_FILTER", False
            )
            query_str = ""
            if request.GET:
                if disable_filter:
                    params = request.GET.dict()
                else:
                    params = ContentMaskingUtils.filter_sensitive_content(
                        **request.GET.dict()
                    )
                query_str = f"?{urlencode(params)}"

            base_path = request.path
            url_with_query = f"{base_path}{query_str}"

            # Format headers, request body, response body
            headers = self._format_headers(request)
            request_body = self._format_request_body(request)
            response_body = self._format_response_body(response)

            log_parts = [
                f"[{method}] {url_with_query} -> {status_code} ({duration_ms:.2f}ms) "
                f"| User: {user_repr} | IP: {client_ip} | Schema: {schema_name}",
                f"Headers: {json.dumps(headers, default=str)}",
            ]
            if request_body:
                log_parts.append(f"Request Body: {request_body}")
            if response_body:
                log_parts.append(f"Response ({status_code}): {response_body}")

            log_message = "\n  ".join(log_parts)
            REQUEST_LOGGER.info(log_message)

            # Performance telemetry
            PERF_LOGGER.debug(
                "API Latency: [%s] %s -> %s (%.2fms) [User: %s | Schema: %s]",
                method,
                full_path,
                status_code,
                duration_ms,
                user_repr,
                schema_name,
            )
        except Exception:
            # Request logging must never fail the application request
            LOGGER.debug("Failed to log request details", exc_info=True)
