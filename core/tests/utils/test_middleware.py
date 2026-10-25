"""
Unit and integration tests for JWTCookieAuthenticationMiddleware.

Validates cookie-based JWT authentication, route exemption checks,
404 rejection on expired credentials, and automatic Set-Cookie attachment.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from core.utils.middleware import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    JWTCookieAuthenticationMiddleware,
)

User = get_user_model()


@pytest.mark.django_db
class TestJWTCookieAuthenticationMiddleware:
    """Test suite for JWTCookieAuthenticationMiddleware."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
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
            return HttpResponse(f"User:{req.user.username}")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert request.user.is_authenticated
        assert request.user == self.user

    def test_inactive_user_token_does_not_authenticate(self):
        """Valid JWT for an inactive user should not authenticate."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        token = str(AccessToken.for_user(self.user))
        request = self.factory.get("/api/users/v1/auth/login/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = token

        def dummy_view(req):
            return HttpResponse("OK")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert not request.user.is_authenticated

    def test_expired_jwt_cookie_on_non_exempt_path_returns_404_and_clears_cookies(self):
        """Expired JWT cookie on non-exempt path should return HTTP 404 and delete cookies."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=10))

        request = self.factory.get("/dashboard/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = str(token)

        def dummy_view(req):
            return HttpResponse("Should not reach here")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 404
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"] == 0

    def test_expired_jwt_cookie_on_exempt_path_allows_view_and_clears_cookies(self):
        """Expired JWT cookie on exempt path should execute view and clear cookies in response."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=10))

        request = self.factory.get("/login/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = str(token)

        def dummy_view(req):
            return HttpResponse("Login Page Content")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b"Login Page Content"
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"] == 0

    def test_drf_response_data_with_tokens_sets_cookies(self):
        """DRF Response returning access/refresh tokens should have Set-Cookie attached."""
        request = self.factory.post("/api/users/v1/auth/login/")
        request.user = AnonymousUser()

        tokens = {
            "access": "test-access-token",
            "refresh": "test-refresh-token",
            "access_expires_in": 1800,
        }

        def dummy_auth_view(req):
            return Response(tokens)

        middleware = JWTCookieAuthenticationMiddleware(dummy_auth_view)
        response = middleware(request)

        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME].value == "test-access-token"
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["samesite"] == "Lax"

        assert REFRESH_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[REFRESH_TOKEN_COOKIE_NAME].value == "test-refresh-token"
        assert response.cookies[REFRESH_TOKEN_COOKIE_NAME]["httponly"] is True

    def test_explicit_request_auth_tokens_sets_cookies(self):
        """View explicitly attaching tokens to request._auth_tokens sets response cookies."""
        request = self.factory.post("/custom-login/")
        request.user = AnonymousUser()

        def dummy_view(req):
            req._auth_tokens = {
                "access": "explicit-access",
                "refresh": "explicit-refresh",
            }
            return HttpResponse("Custom Login Success")

        middleware = JWTCookieAuthenticationMiddleware(dummy_view)
        response = middleware(request)

        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME].value == "explicit-access"
        assert REFRESH_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[REFRESH_TOKEN_COOKIE_NAME].value == "explicit-refresh"

    def test_set_auth_cookies_defaults_max_age_correctly(self):
        """Missing access_expires_in should fall back to setting ACCESS_TOKEN_LIFETIME duration."""
        response = HttpResponse("OK")
        tokens = {
            "access": "tok-1",
            "refresh": "tok-2",
        }
        JWTCookieAuthenticationMiddleware.set_auth_cookies(response, tokens)

        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        # Verify max-age is a reasonable duration in seconds (e.g. 3600), not an epoch timestamp
        max_age = int(response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"])
        assert 60 <= max_age <= 86400 * 30

    def test_pre_authenticated_user_still_attaches_cookies_when_tokens_issued(self):
        """Even if user is already authenticated, issuing new tokens sets outgoing cookies."""
        request = self.factory.post("/api/v1/auth/token/refresh/")
        request.user = self.user

        def refresh_view(req):
            return Response({"access": "new-access", "refresh": "new-refresh"})

        middleware = JWTCookieAuthenticationMiddleware(refresh_view)
        response = middleware(request)

        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME].value == "new-access"

    def test_expired_cookie_on_exempt_path_with_new_tokens_sets_new_cookies(self):
        """Expired cookie on login route followed by successful auth must preserve new tokens."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=10))

        request = self.factory.post("/login/")
        request.user = AnonymousUser()
        request.COOKIES[ACCESS_TOKEN_COOKIE_NAME] = str(token)

        def login_view(req):
            return Response(
                {"access": "fresh-access-token", "refresh": "fresh-refresh-token"}
            )

        middleware = JWTCookieAuthenticationMiddleware(login_view)
        response = middleware(request)

        assert response.status_code == 200
        assert ACCESS_TOKEN_COOKIE_NAME in response.cookies
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME].value == "fresh-access-token"
        assert response.cookies[ACCESS_TOKEN_COOKIE_NAME]["max-age"] > 0
