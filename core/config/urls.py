"""
Tenant-schema URL configuration for the core framework.

Routes:
    - UI / Template Endpoints: `/`, `/login/`, `/signup/`, `/register/`, `/forgot-password/`
    - Django Admin: `/admin/` (private_admin_site)
    - Backend API: `/api/<app>/<version>/...` (auto-discovered tenant private apps)
"""

from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

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
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # Django Admin
    path("admin/", private_admin_site.urls),
    # Backend API Endpoints
    *build_tenant_app_urlpatterns(),
]
