import typing

from django.apps import apps as django_apps
from django.conf import settings

from core.apps.integrations.email.app_settings import IntegrationsEmailSettings

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractEmailLog, AbstractEmailTemplate


app_settings: IntegrationsEmailSettings = IntegrationsEmailSettings()


def get_email_log_model():
    """Return the configured EmailLog model."""
    return typing.cast(
        type["AbstractEmailLog"],
        django_apps.get_model(
            settings.INTEGRATIONS_EMAIL_EMAIL_LOG_MODEL, require_ready=False
        ),
    )


def get_email_template_model():
    """Return the configured EmailTemplate model."""
    return typing.cast(
        type["AbstractEmailTemplate"],
        django_apps.get_model(
            settings.INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL, require_ready=False
        ),
    )


__all__ = [
    "app_settings",
    "get_email_log_model",
    "get_email_template_model",
]
