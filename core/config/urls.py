"""
Tenant-schema URL configuration for the core framework.

Routes:
    - UI / Template Endpoints: `/`, `/login/`, `/signup/`, `/register/`, `/forgot-password/`
    - Django Admin: `/admin/` (private_admin_site)
    - Backend API: `/api/<app>/<version>/...` (auto-discovered tenant private apps)
"""

from django.urls import path

from core.apps.users.api.template_views import (
    ForgotPasswordView,
    LoginView,
    RegisterView,
    SignupView,
)
from core.utils.admin import private_admin_site
from core.utils.urls import build_tenant_app_urlpatterns

urlpatterns = [
    # UI / Template Endpoints
    path("", LoginView.as_view(), name="ui-root"),
    path("login/", LoginView.as_view(), name="ui-login"),
    path("signup/", SignupView.as_view(), name="ui-signup"),
    path("register/", RegisterView.as_view(), name="ui-register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="ui-forgot-password"),
    # Django Admin
    path("admin/", private_admin_site.urls),
    # Backend API Endpoints
    *build_tenant_app_urlpatterns(),
]
