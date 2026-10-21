"""
Compatibility alias module for `core.apps.users.api.template_views`.
"""

from core.apps.users.api.template_views import (
    BaseAuthTemplateView,
    ForgotPasswordView,
    LoginView,
    RegisterView,
    SignupView,
)

__all__ = [
    "BaseAuthTemplateView",
    "ForgotPasswordView",
    "LoginView",
    "RegisterView",
    "SignupView",
]
