from dj_rest_auth.views import (
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from core.apps.users.api.views import (
    GoogleLoginView,
    LoginView,
    OTPSendView,
    OTPVerifyView,
    SignupView,
)

urlpatterns = [
    # Registration & Login
    path("auth/signup/", SignupView.as_view(), name="user-signup"),
    path("auth/login/", LoginView.as_view(), name="user-login"),
    path("auth/user/", UserDetailsView.as_view(), name="user-details"),
    # JWT Tokens
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token-blacklist"),
    # OTP Flows
    path("auth/otp/send/", OTPSendView.as_view(), name="otp-send"),
    path("auth/otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
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
