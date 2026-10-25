"""
Template views for User Authentication, Registration, and Password Recovery.

These views render the unified Jinja2 `authenticated_view.jinja` template
with context tailored to each user flow (Sign In, Create Account, Password Reset).
"""

import logging
import typing

from django.shortcuts import redirect

from core.apps.users import app_settings
from core.apps.users.utils import get_auth_redirect_url
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
    auth_mode: str = "all"

    def get_context_data(self, **kwargs: typing.Any) -> dict[str, typing.Any]:
        """
        Assemble template context for the authentication gateway.

        Injects initial tab, method, auth mode, and auth view flags into the context.

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

        auth_mode = self.auth_mode
        if (
            auth_mode == "all"
            and not app_settings.ENABLE_PASSWORD_LOGIN
            and app_settings.ENABLE_OTP_LOGIN
        ):
            auth_mode = "otp_only"
        context.setdefault("auth_mode", auth_mode)

        return context


class LoginView(BaseAuthTemplateView):
    """
    Template view serving the user sign-in flow (Password and OTP).
    """

    initial_tab = "signin"
    initial_method = "password"

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect already authenticated users to the target destination.

        Validates that the redirect target is safe to prevent open redirect vulnerabilities.

        Args:
            request: The incoming HTTP request.
            *args: Positional arguments passed to dispatch.
            **kwargs: Keyword arguments passed to dispatch.

        Returns:
            HttpResponse: Redirect response if user is authenticated, otherwise standard dispatch.
        """
        if getattr(request, "user", None) and request.user.is_authenticated:
            redirect_url = get_auth_redirect_url(request)
            if redirect_url:
                return redirect(redirect_url)

        return super().dispatch(request, *args, **kwargs)


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

    def get_context_data(self, **kwargs: typing.Any) -> dict[str, typing.Any]:
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
