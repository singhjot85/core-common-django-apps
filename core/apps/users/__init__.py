import typing

from django.apps import apps as django_apps
from django.conf import settings

from core.apps.users.app_settings import UsersSettings

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractOTPLog, AbstractSocialAccount, AbstractUser


app_settings: UsersSettings = UsersSettings()


def get_user_model():
    """
    Get the configured User model dynamically.
    """
    return typing.cast(
        type["AbstractUser"],
        django_apps.get_model(settings.AUTH_USER_MODEL, require_ready=False),
    )


def get_social_account_model():
    """
    Get the configured SocialAccount model dynamically.
    """
    return typing.cast(
        type["AbstractSocialAccount"],
        django_apps.get_model(settings.USERS_SOCIAL_ACCOUNT_MODEL, require_ready=False),
    )


def get_otp_log_model():
    """
    Get the configured OTPLog model dynamically.
    """
    return typing.cast(
        type["AbstractOTPLog"],
        django_apps.get_model(settings.USERS_OTP_LOG_MODEL, require_ready=False),
    )
