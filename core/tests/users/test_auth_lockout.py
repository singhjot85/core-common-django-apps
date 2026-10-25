"""
Tests for JWT Token Jitter, Auth Cookies, Attempt Tracking, Account Lockout,
and Zero-Enumeration Authentication Responses.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.settings import api_settings as jwt_settings

from core.apps.users.api.views import (
    AccountUnlockView,
    LoginView,
    OTPVerifyView,
    get_jwt_tokens_for_user,
)
from core.apps.users.constants import OTPChannelChoices
from core.apps.users.services.auth_lockout import AuthLockoutService
from core.utils.middleware import JWTCookieAuthenticationMiddleware

User = get_user_model()


@pytest.fixture(autouse=True)
def clear_test_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestJWTJitterAndCookies:
    def test_jwt_tokens_have_65_to_75_percent_jitter(self):
        user = User.objects.create_user(
            username="jitter_user",
            email="jitter@test.com",
            password="TestPassword123!",  # pragma: allowlist secret
        )

        base_seconds = jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds()
        min_expected = int(base_seconds * 0.65)
        max_expected = int(base_seconds * 0.75) + 2

        for _ in range(10):
            tokens = get_jwt_tokens_for_user(user)
            assert "access" in tokens
            assert "refresh" in tokens
            assert "access_expires_in" in tokens
            assert min_expected <= tokens["access_expires_in"] <= max_expected

    def test_set_auth_cookies_sets_expected_cookies(self):
        tokens = {
            "access": "mock-access-token",
            "refresh": "mock-refresh-token",
            "access_expires_in": 1800,
        }
        response = Response({"success": True})
        JWTCookieAuthenticationMiddleware.set_auth_cookies(response, tokens)

        assert "access_token" in response.cookies
        assert response.cookies["access_token"].value == "mock-access-token"
        assert response.cookies["access_token"]["samesite"] == "Lax"

        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"].value == "mock-refresh-token"
        assert response.cookies["refresh_token"]["httponly"] is True


class TestAuthLockoutService:
    def test_record_failed_attempts_decrements_remaining(self):
        identifier = "user@tenant.io"
        remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
        assert remaining == 4
        assert is_locked is False

        remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
        assert remaining == 3
        assert is_locked is False

    @patch("core.apps.users.services.auth_lockout.queue_task")
    def test_lockout_on_exhausting_attempts(self, mock_queue_task):
        identifier = "target_user"
        for _ in range(4):
            remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
            assert is_locked is False

        # 5th attempt triggers lockout
        remaining, is_locked = AuthLockoutService.record_failed_attempt(identifier)
        assert remaining == 0
        assert is_locked is True
        assert AuthLockoutService.is_locked(identifier) is True

    @pytest.mark.django_db
    def test_verify_and_unlock_account_reactivates_user(self):
        user = User.objects.create_user(
            username="locked_user",
            email="locked@test.com",
            password="TestPassword123!",  # pragma: allowlist secret
            is_active=False,
        )
        token = "valid-unlock-token-xyz"
        cache.set(
            AuthLockoutService._unlock_token_key(token), str(user.pk), timeout=3600
        )

        success, msg = AuthLockoutService.verify_and_unlock_account(token)
        assert success is True
        assert "unlocked" in msg.lower()

        user.refresh_from_db()
        assert user.is_active is True

    def test_verify_and_unlock_invalid_or_expired_token(self):
        success, msg = AuthLockoutService.verify_and_unlock_account("invalid-token")
        assert success is False
        assert "invalid" in msg.lower() or "expired" in msg.lower()


@pytest.mark.django_db
class TestZeroEnumerationAuthentication:
    def setup_method(self):
        self.factory = APIRequestFactory()

    def test_password_login_invalid_credentials_returns_generic_error(self):
        view = LoginView.as_view()
        request = self.factory.post(
            "/api/users/v1/auth/login/",
            {
                "username": "non_existing_user",
                "password": "WrongPassword123!",  # pragma: allowlist secret
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"] == "Username or password combination is incorrect."
        )
        assert response.data["remaining_attempts"] == 4
        assert response.data["is_locked"] is False

    def test_password_login_lockout_after_max_attempts(self):
        view = LoginView.as_view()
        username = "attacked_account"
        for _ in range(4):
            req = self.factory.post(
                "/api/users/v1/auth/login/",
                {"username": username, "password": "Bad"},  # pragma: allowlist secret
                format="json",
            )
            res = view(req)
            assert res.status_code == status.HTTP_400_BAD_REQUEST

        # 5th attempt locks out
        req = self.factory.post(
            "/api/users/v1/auth/login/",
            {"username": username, "password": "Bad"},  # pragma: allowlist secret
            format="json",
        )
        res = view(req)
        assert res.status_code == status.HTTP_423_LOCKED
        assert "Account locked" in res.data["detail"]
        assert res.data["remaining_attempts"] == 0
        assert res.data["is_locked"] is True

    @patch("core.apps.users.api.views.OTPServiceFactory.verify_otp")
    def test_otp_verify_invalid_code_returns_generic_error_and_remaining(
        self, mock_verify
    ):
        mock_verify.return_value = (False, "Code is invalid")

        view = OTPVerifyView.as_view()
        request = self.factory.post(
            "/api/users/v1/auth/otp/verify/",
            {
                "identifier": "+15551234567",
                "code": "999999",
                "channel": OTPChannelChoices.PHONE,
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Incorrect OTP."
        assert response.data["remaining_attempts"] == 4
        assert response.data["is_locked"] is False

    def test_account_unlock_api_view_endpoint(self):
        view = AccountUnlockView.as_view()
        request = self.factory.get("/api/users/v1/auth/unlock/?token=fake-token")
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["unlocked"] is False
