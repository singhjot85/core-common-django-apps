"""
Unit tests for User Authentication Template Views.
"""

from django.test import RequestFactory
from django.urls import reverse

from core.apps.users.api.template_view import (
    ForgotPasswordView as AliasForgotPasswordView,
    LoginView as AliasLoginView,
    RegisterView as AliasRegisterView,
    SignupView as AliasSignupView,
)
from core.apps.users.api.template_views import (
    ForgotPasswordView,
    LoginView,
    RegisterView,
    SignupView,
)


class TestAuthTemplateViews:
    """Test suite for LoginView, SignupView, RegisterView, and ForgotPasswordView."""

    def test_compatibility_alias_imports(self):
        """Verify template_view.py aliases match template_views.py classes."""
        assert LoginView is AliasLoginView
        assert SignupView is AliasSignupView
        assert RegisterView is AliasRegisterView
        assert ForgotPasswordView is AliasForgotPasswordView

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
