from dj_rest_auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.urls import include, path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from core.apps.users.api.views import (
    AccountUnlockView,
    EmailOTPAuthViewSet,
    GoogleLoginView,
    PasswordAuthViewSet,
    SMSOTPAuthViewSet,
)
from core.utils.routers import get_api_router_instance

# Setup auth router
core_auth_router = get_api_router_instance()
core_auth_router.register(r"password", PasswordAuthViewSet, basename="auth-password")
core_auth_router.register(r"otp/email", EmailOTPAuthViewSet, basename="auth-otp-email")
core_auth_router.register(r"otp/sms", SMSOTPAuthViewSet, basename="auth-otp-sms")

urlpatterns = [
    # Core Auth Router (Password, Email OTP, SMS OTP login, signup & send)
    path("auth/", include(core_auth_router.urls)),
    # Auxiliary Auth Endpoints
    path("auth/unlock/", AccountUnlockView.as_view(), name="user-unlock"),
    path("auth/user/", UserDetailsView.as_view(), name="user-details"),
    # JWT Tokens
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token-blacklist"),
    # Social Logins
    path("auth/social/google/", GoogleLoginView.as_view(), name="social-google-login"),
    # Password Management
    path("auth/password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("auth/password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
