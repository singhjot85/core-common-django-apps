from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.apps.users import get_user_model
from core.apps.users.api.views import (
    GoogleLoginView,
    LoginView,
    OTPSendView,
    OTPVerifyView,
    SignupView,
    get_auth_redirect_url,
)
from core.apps.users.constants import OTPChannelChoices, OTPPurposeChoices

User = get_user_model()


class TestUsersViews:
    """Tests for Users API endpoints."""

    def setup_method(self):
        self.factory = APIRequestFactory()

    @patch.object(User.objects, "filter")
    @patch("core.apps.users.api.views.get_jwt_tokens_for_user")
    @patch.object(User.objects, "create_user")
    def test_signup_view_success(self, mock_create_user, mock_jwt, mock_filter):
        mock_filter.return_value.exists.return_value = False
        mock_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="john_doe",
            email="john@example.com",
        )
        mock_create_user.return_value = mock_user
        mock_jwt.return_value = {"access": "access-xyz", "refresh": "refresh-xyz"}

        view = SignupView.as_view()
        request = self.factory.post(
            "/api/users/auth/signup/",
            {"first_name": "John", "last_name": "Doe", "email": "john@example.com"},
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "user" in response.data

    def test_otp_send_view_invalid_format_returns_400(self):
        view = OTPSendView.as_view()
        request = self.factory.post(
            "/api/users/auth/otp/send/",
            {"identifier": "invalid-email", "channel": OTPChannelChoices.EMAIL},
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("core.apps.users.api.views.queue_task")
    def test_otp_send_view_valid_format_returns_202_accepted(self, mock_queue_task):
        view = OTPSendView.as_view()
        request = self.factory.post(
            "/api/users/auth/otp/send/",
            {
                "identifier": "+1234567890",
                "channel": OTPChannelChoices.PHONE,
                "purpose": OTPPurposeChoices.LOGIN,
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "detail" in response.data
        # Ensure task was queued
        assert mock_queue_task.called

    @patch("core.apps.users.api.views.OTPServiceFactory.send_otp")
    @patch("core.apps.users.api.views.queue_task")
    def test_otp_send_view_queue_failure_does_not_execute_sync_fallback(
        self, mock_queue_task, mock_send_otp
    ):
        mock_queue_task.side_effect = Exception("Broker unavailable")
        view = OTPSendView.as_view()
        request = self.factory.post(
            "/api/users/auth/otp/send/",
            {
                "identifier": "+1234567890",
                "channel": OTPChannelChoices.PHONE,
                "purpose": OTPPurposeChoices.LOGIN,
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_send_otp.assert_not_called()

    @patch("core.apps.users.api.views.OTPServiceFactory.verify_otp")
    def test_otp_verify_view_invalid_otp_returns_400(self, mock_verify):
        mock_verify.return_value = (False, "Invalid OTP code.")

        view = OTPVerifyView.as_view()
        request = self.factory.post(
            "/api/users/auth/otp/verify/",
            {
                "identifier": "+1234567890",
                "code": "000000",
                "channel": OTPChannelChoices.PHONE,
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("core.apps.users.api.views.get_jwt_tokens_for_user")
    @patch(
        "core.apps.users.api.views.SocialAuthServiceFactory.authenticate_or_register"
    )
    def test_google_login_view_success(self, mock_auth_or_reg, mock_jwt):
        mock_user = User(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="google_user",
            email="g@example.com",
        )
        mock_auth_or_reg.return_value = (mock_user, False)
        mock_jwt.return_value = {"access": "access-xyz", "refresh": "refresh-xyz"}

        view = GoogleLoginView.as_view()
        request = self.factory.post(
            "/api/users/auth/social/google/",
            {"id_token": "valid-google-id-token"},
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.data["created"] is False

    def test_get_auth_redirect_url_safe_and_fallback(self):
        """get_auth_redirect_url returns safe relative or in-app url and rejects malicious external targets."""
        req_safe = self.factory.get("/api/v1/auth/login/?next=/orders/")
        assert get_auth_redirect_url(req_safe) == "/orders/"

        req_in_app_host = self.factory.get(
            "/api/v1/auth/login/?next=http://testserver/orders/"
        )
        assert get_auth_redirect_url(req_in_app_host) == "http://testserver/orders/"

        req_unsafe = self.factory.get(
            "/api/v1/auth/login/?next=https://attacker.com/evil"
        )
        assert get_auth_redirect_url(req_unsafe) == "/"

        req_proto_relative = self.factory.get(
            "/api/v1/auth/login/?next=//attacker.com/evil"
        )
        assert get_auth_redirect_url(req_proto_relative) == "/"

        req_payload = self.factory.post(
            "/api/v1/auth/login/",
            {"next": "/profile/"},
            format="json",
        )
        assert get_auth_redirect_url(req_payload) == "/profile/"

    @pytest.mark.django_db
    def test_login_view_trims_password_whitespace(self):
        """Password containing leading and trailing spaces is trimmed during login."""
        User.objects.create_user(
            username="spaced_password_user",
            email="spaced@example.com",
            password="SecretPass123!",  # pragma: allowlist secret
            is_active=True,
        )

        view = LoginView.as_view()
        request = self.factory.post(
            "/api/users/v1/auth/login/",
            {
                "username": "spaced_password_user",
                "password": "  SecretPass123!  ",  # pragma: allowlist secret
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.data["user"]["username"] == "spaced_password_user"

    @pytest.mark.django_db
    @patch("core.apps.users.api.views.OTPServiceFactory.verify_otp")
    def test_otp_verify_view_case_insensitive_email(self, mock_verify):
        """OTPVerifyView matches registered email case-insensitively."""
        mock_verify.return_value = (True, "OTP verified")
        user = User.objects.create_user(
            username="mixed_case_user",
            email="john.doe@example.com",
            is_active=True,
        )

        view = OTPVerifyView.as_view()
        request = self.factory.post(
            "/api/users/v1/auth/otp/verify/",
            {
                "identifier": "JOHN.DOE@EXAMPLE.COM",
                "code": "123456",
                "channel": OTPChannelChoices.EMAIL,
            },
            format="json",
        )
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["id"] == str(user.pk)
        assert response.data["created"] is False
