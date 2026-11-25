"""
Unit and integration tests for core HTTP middlewares.

Tests:
- JWTCookieAuthenticationMiddleware: cookie-based auth, route exemptions, cookie attachment.
- RequestLoggingMiddleware: metadata capture, latency calculation, PII/secret scrubbing, failsafe.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from core.apps.users.factories import UserFactory
from core.config.middlewares.jwt_cookie_auth import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    JWTCookieAuthenticationMiddleware,
)
from core.config.middlewares.request_logging import RequestLoggingMiddleware

User = get_user_model()


@pytest.mark.django_db
class TestJWTCookieAuthenticationMiddleware:
    """Test suite for JWTCookieAuthenticationMiddleware."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.user = UserFactory(
            username="jwt_middleware_user",
            email="jwt_middleware@example.com",
            password="SecurePassword123!",  # pragma: allowlist secret
            is_active=True,
        )

    def test_authenticated_user_passes_through(self):
        """Pre-authenticated requests should pass through without cookie validation."""
        request = self.factory.get("/dashboard/")
        request.user = self.user

        def dummy_view(req):
            return HttpResponse("OK")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert request.user == self.user

    def test_valid_jwt_cookie_authenticates_user(self):
        """Valid access token in cookies should attach active user to request.user."""
        token = str(AccessToken.for_user(self.user))
        request = self.factory.get("/dashboard/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = token

        def dummy_view(req):
            return HttpResponse("OK")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert request.user == self.user

    def test_expired_jwt_cookie_on_protected_path_returns_404(self):
        """Expired JWT cookie on non-exempt path rejects request with 404 Not Found."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=10))

        request = self.factory.get("/dashboard/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = str(token)

        def dummy_view(req):
            return HttpResponse("OK")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 404
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"] == 0

    def test_expired_jwt_cookie_on_exempt_path_clears_cookie_and_proceeds(self):
        """Expired JWT cookie on exempt path proceeds to view and clears expired cookie."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=10))

        request = self.factory.get("/login/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = str(token)

        def dummy_view(req):
            return HttpResponse("Login Page")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"] == 0

    def test_successful_auth_response_attaches_cookies(self):
        """View attaching tokens sets access_token and refresh_token in response cookies."""
        request = self.factory.post("/api/users/v1/auth/login/")
        request.user = AnonymousUser()

        def login_view(req):
            return Response(
                {"access": "mock-access-token", "refresh": "mock-refresh-token"}
            )

        middleware = JWTCookieAuthenticationMiddleware(login_view)
        response = middleware(request)

        assert response.status_code == 200
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert REFRESH_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME].value == "mock-access-token"
        assert response.cookies[REFRESH_TOKEN_COOKIE_NAME].value == "mock-refresh-token"
        assert response.cookies[REFRESH_TOKEN_COOKIE_NAME]["httponly"] is True


@pytest.mark.django_db
class TestRequestLoggingMiddleware:
    """Test suite for RequestLoggingMiddleware."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.user = UserFactory(
            username="req_log_user",
            email="req_log@example.com",
            is_active=True,
        )

    @patch("core.config.middlewares.request_logging.REQUEST_LOGGER.info")
    @patch("core.config.middlewares.request_logging.PERF_LOGGER.debug")
    def test_request_logging_middleware_success(self, mock_perf, mock_request_log):
        """Middleware records HTTP request metadata and latency, unmasking in local env."""
        request = self.factory.get(
            "/api/v1/customers/?page=1&password=mysecret"
        )  # pragma: allowlist secret
        request.user = self.user

        def dummy_view(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        mock_request_log.assert_called_once()
        log_msg = mock_request_log.call_args[0][0]
        assert "[GET] /api/v1/customers/" in log_msg
        assert "-> 200" in log_msg
        assert "req_log_user:" in log_msg
        # In local dev (DISABLE_SENSITIVE_CONTENT_FILTER=True), parameter is unmasked
        assert "password=mysecret" in log_msg

        mock_perf.assert_called_once()
        perf_args = mock_perf.call_args[0]
        assert perf_args[1] == "GET"
        assert perf_args[2] == "/api/v1/customers/"
        assert perf_args[3] == 200

    @override_settings(DISABLE_SENSITIVE_CONTENT_FILTER=False)
    @patch("core.config.middlewares.request_logging.REQUEST_LOGGER.info")
    @patch("core.config.middlewares.request_logging.PERF_LOGGER.debug")
    def test_request_logging_middleware_masks_when_filter_enabled(
        self, mock_perf, mock_request_log
    ):
        """When DISABLE_SENSITIVE_CONTENT_FILTER is False, query params are scrubbed."""
        request = self.factory.get(
            "/api/v1/customers/?page=1&password=mysecret"
        )  # pragma: allowlist secret
        request.user = self.user

        def dummy_view(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        mock_request_log.assert_called_once()
        log_msg = mock_request_log.call_args[0][0]
        assert "mysecret" not in log_msg

    @patch("core.config.middlewares.request_logging.REQUEST_LOGGER.info")
    @patch("core.config.middlewares.request_logging.PERF_LOGGER.debug")
    def test_request_logging_middleware_anonymous_user(
        self, mock_perf, mock_request_log
    ):
        """Anonymous user requests are logged with anonymous user identity."""
        request = self.factory.post("/api/v1/public/")
        request.user = AnonymousUser()

        def dummy_view(req):
            return HttpResponse("Created", status=201)

        middleware = RequestLoggingMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 201
        log_msg = mock_request_log.call_args[0][0]
        assert "User: anonymous" in log_msg

    @patch("core.config.middlewares.request_logging.REQUEST_LOGGER.info")
    def test_request_logging_middleware_exception_passthrough(self, mock_request_log):
        """Middleware logs status 500 when view raises an unhandled exception and re-raises."""
        request = self.factory.get("/failing-route/")
        request.user = AnonymousUser()

        def failing_view(req):
            raise ValueError("Something went wrong")

        middleware = RequestLoggingMiddleware(failing_view)

        with pytest.raises(ValueError, match="Something went wrong"):
            middleware(request)

        mock_request_log.assert_called_once()
        log_msg = mock_request_log.call_args[0][0]
        assert "-> 500" in log_msg

    @patch(
        "core.config.middlewares.request_logging.REQUEST_LOGGER.info",
        side_effect=Exception("Disk full"),
    )
    def test_request_logging_middleware_failsafe_on_logging_error(
        self, mock_request_log
    ):
        """Logging failure does not prevent client response from succeeding."""
        request = self.factory.get("/test/")
        request.user = AnonymousUser()

        def dummy_view(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
