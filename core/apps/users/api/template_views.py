"""
Template views for User Authentication, Registration, and Password Recovery.

These views render the unified Jinja2 `authenticated_view.jinja` template
with context tailored to each user flow (Sign In, Create Account, Password Reset).
"""

import logging
from typing import Any

from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.views.generic.base import TemplateView

LOGGER = logging.getLogger(__name__)


def _safe_reverse(viewname: str, fallback: str) -> str:
    """
    Safely reverse a URL name or return a fallback path if resolution fails.

    Args:
        viewname: Django URL pattern name.
        fallback: Fallback URL string.

    Returns:
        Reversed URL string or fallback.
    """
    try:
        return reverse(viewname)
    except NoReverseMatch:
        return fallback


class BaseAuthTemplateView(TemplateView):
    """
    Base TemplateView for authentication-related server-rendered views.

    Supplies default configuration, action endpoints, SSO links,
    and brand metadata to `core/views/authenticated_view.jinja`.
    """

    template_name = "core/views/authenticated_view.jinja"
    initial_tab: str = "signin"
    initial_method: str = "password"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Assemble template context for the authentication gateway.
        """
        context = super().get_context_data(**kwargs)

        # Tab & Mode Configuration
        context.setdefault("initial_tab", self.initial_tab)
        context.setdefault("initial_method", self.initial_method)

        # Action Targets (API Endpoints)
        context.setdefault(
            "login_action",
            _safe_reverse("user-login", "/api/users/v1/auth/login/"),
        )
        context.setdefault(
            "signup_action",
            _safe_reverse("user-signup", "/api/users/v1/auth/signup/"),
        )
        context.setdefault(
            "otp_send_action",
            _safe_reverse("otp-send", "/api/users/v1/auth/otp/send/"),
        )
        context.setdefault(
            "otp_verify_action",
            _safe_reverse("otp-verify", "/api/users/v1/auth/otp/verify/"),
        )
        context.setdefault(
            "forgot_password_action",
            _safe_reverse("password-reset", "/api/users/v1/auth/password/reset/"),
        )

        # Navigation URLs
        context.setdefault(
            "login_url",
            _safe_reverse("ui-login", "/login/"),
        )
        context.setdefault(
            "signup_url",
            _safe_reverse("ui-signup", "/signup/"),
        )
        context.setdefault(
            "register_url",
            _safe_reverse("ui-register", "/register/"),
        )
        context.setdefault(
            "forgot_password_url",
            _safe_reverse("ui-forgot-password", "/forgot-password/"),
        )

        # Brand & Project Metadata
        project_label = getattr(settings, "PROJECT_LABEL", "Core Platform")
        context.setdefault("PROJECT_LABEL", project_label)
        context.setdefault("brand_logo_url", getattr(settings, "BRAND_LOGO_URL", None))

        # Legal & Status URLs
        context.setdefault("privacy_url", getattr(settings, "PRIVACY_URL", "#privacy"))
        context.setdefault("terms_url", getattr(settings, "TERMS_URL", "#terms"))
        context.setdefault("status_url", getattr(settings, "STATUS_URL", "#status"))

        # Social SSO URLs
        context.setdefault(
            "sso_google_url",
            _safe_reverse("social-google-login", "/api/users/v1/auth/social/google/"),
        )
        context.setdefault("sso_apple_url", "#apple")
        context.setdefault("sso_meta_url", "#meta")

        return context


class LoginView(BaseAuthTemplateView):
    """
    Template view serving the user sign-in flow (Password and OTP).
    """

    initial_tab = "signin"
    initial_method = "password"


class SignupView(BaseAuthTemplateView):
    """
    Template view serving the organization / user account provisioning flow.
    """

    initial_tab = "signup"
    initial_method = "password"


class RegisterView(SignupView):
    """
    Semantic alias for SignupView for registration endpoints.
    """

    pass


class ForgotPasswordView(BaseAuthTemplateView):
    """
    Template view serving the password recovery / credential reset flow.
    """

    initial_tab = "signin"
    initial_method = "password"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["show_forgot_password"] = True
        return context
