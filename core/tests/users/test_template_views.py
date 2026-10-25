"""
Unit tests for User Authentication Template Views.
"""

from unittest.mock import MagicMock

from constance.test import override_config
from django.test import RequestFactory
from django.urls import reverse

from core.apps.users.api.template_views import (
    ForgotPasswordView,
    LoginView,
    RegisterView,
    SignupView,
)


class TestAuthTemplateViews:
    """Test suite for LoginView, SignupView, RegisterView, and ForgotPasswordView."""

    def test_login_view_context_and_rendering(self):
        """Verify LoginView sets signin initial tab and renders HTTP 200."""
        factory = RequestFactory()
        request = factory.get("/login/")
        response = LoginView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["initial_tab"] == "signin"
        assert response.context_data["initial_method"] == "password"
        assert "login_action" in response.context_data
        assert "otp_send_action" in response.context_data
        assert "otp_verify_action" in response.context_data

        # Check rendered HTML contains signin tab element
        content = response.rendered_content
        assert 'data-auth-tab="signin"' in content
        assert 'data-auth-tab="signup"' in content

    def test_signup_view_context_and_rendering(self):
        """Verify SignupView sets signup initial tab and renders HTTP 200."""
        factory = RequestFactory()
        request = factory.get("/signup/")
        response = SignupView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["initial_tab"] == "signup"
        assert "signup_action" in response.context_data

    def test_register_view_is_signup_alias(self):
        """Verify RegisterView is an alias/subclass of SignupView."""
        assert issubclass(RegisterView, SignupView)
        factory = RequestFactory()
        request = factory.get("/register/")
        response = RegisterView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["initial_tab"] == "signup"

    def test_forgot_password_view_context(self):
        """Verify ForgotPasswordView sets show_forgot_password flag."""
        factory = RequestFactory()
        request = factory.get("/forgot-password/")
        response = ForgotPasswordView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["show_forgot_password"] is True
        assert "forgot_password_action" in response.context_data

    def test_ui_endpoints_url_reversal(self):
        """Verify named UI endpoints reverse correctly."""
        assert reverse("ui-root") == "/"
        assert reverse("ui-login") == "/login/"
        assert reverse("ui-signup") == "/signup/"
        assert reverse("ui-register") == "/register/"
        assert reverse("ui-forgot-password") == "/forgot-password/"

    def test_login_view_authenticated_user_redirects_safely(self):
        """Authenticated users visiting /login/ should be safely redirected."""
        factory = RequestFactory()
        request = factory.get("/login/?next=/dashboard/")
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        request.user = mock_user

        response = LoginView.as_view()(request)
        assert response.status_code == 302
        assert response.url == "/dashboard/"

    def test_login_view_authenticated_user_rejects_open_redirect(self):
        """Authenticated users with external redirect target should fall back to safe default."""

        factory = RequestFactory()
        mock_user = MagicMock()
        mock_user.is_authenticated = True

        # External host rejected
        request = factory.get("/login/?next=https://evil.com/phishing")
        request.user = mock_user
        response = LoginView.as_view()(request)
        assert response.status_code == 302
        assert response.url == "/"

        # Scheme-relative URL rejected
        request_proto = factory.get("/login/?next=//evil.com/phishing")
        request_proto.user = mock_user
        response_proto = LoginView.as_view()(request_proto)
        assert response_proto.status_code == 302
        assert response_proto.url == "/"

        # In-app host allowed
        request_inapp = factory.get("/login/?next=http://testserver/dashboard/")
        request_inapp.user = mock_user
        response_inapp = LoginView.as_view()(request_inapp)
        assert response_inapp.status_code == 302
        assert response_inapp.url == "http://testserver/dashboard/"

    def test_login_view_otp_only_mode(self):
        """When password login is disabled, auth_mode defaults to otp_only."""
        factory = RequestFactory()
        request = factory.get("/login/")
        with override_config(CORE_USERS_ENABLE_PASSWORD_LOGIN=False):
            response = LoginView.as_view()(request)
            assert response.status_code == 200
            assert response.context_data["auth_mode"] == "otp_only"
