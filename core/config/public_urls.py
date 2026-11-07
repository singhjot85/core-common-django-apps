"""
Public-schema URL configuration for the core framework.

Routes:
    - UI / Template Endpoints: `/`, `/login/`, `/signup/`, `/register/`, `/forgot-password/`
    - Django Admin: `/admin/` (public_admin_site)
    - Backend API: `/api/<app>/<version>/...` (auto-discovered public apps)
"""

from django.conf import settings
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
from core.config.api_protected import core_public_url_mapping, resolve_and_build_paths
from core.utils.admin import public_admin_site

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
    path("admin/", public_admin_site.urls),
    # Backend API Endpoints
    *resolve_and_build_paths(core_public_url_mapping),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
