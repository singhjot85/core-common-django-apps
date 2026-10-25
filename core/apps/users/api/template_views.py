"""
Template views for User Authentication, Registration, and Password Recovery.

These views render the unified Jinja2 `authenticated_view.jinja` template
with context tailored to each user flow (Sign In, Create Account, Password Reset).
"""

import logging
from typing import Any

from core.utils.views import BaseTemplateView

LOGGER = logging.getLogger(__name__)


class BaseAuthTemplateView(BaseTemplateView):
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

        Injects initial tab, method, and auth view flags into the context.

        Args:
            **kwargs: Keyword arguments passed to get_context_data.

        Returns:
            dict[str, Any]: Template context dictionary.
        """
        context: dict = super().get_context_data(social_urls=True, **kwargs)

        # Tab & Mode Configuration
        context.setdefault("initial_tab", self.initial_tab)
        context.setdefault("initial_method", self.initial_method)
        context.setdefault("is_login_view", True)

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
        """
        Assemble template context with password reset display flag.

        Args:
            **kwargs: Keyword arguments passed to get_context_data.

        Returns:
            dict[str, Any]: Template context dictionary with ``show_forgot_password=True``.
        """
        context = super().get_context_data(**kwargs)
        context["show_forgot_password"] = True
        return context
