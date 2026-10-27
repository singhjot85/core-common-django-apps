import typing

from django.apps import apps as django_apps
from django.conf import settings

from core.apps.integrations.sms.app_settings import IntegrationsSMSSettings

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractSMSLog, AbstractSMSTemplate


app_settings: IntegrationsSMSSettings = IntegrationsSMSSettings()


def get_sms_log_model():
    """Return the configured SMSLog model."""
    return typing.cast(
        type["AbstractSMSLog"],
        django_apps.get_model(
            settings.INTEGRATIONS_SMS_SMS_LOG_MODEL, require_ready=False
        ),
    )


def get_sms_template_model():
    """Return the configured SMSTemplate model."""
    return typing.cast(
        type["AbstractSMSTemplate"],
        django_apps.get_model(
            settings.INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL, require_ready=False
        ),
    )


__all__ = [
    "app_settings",
    "get_sms_log_model",
    "get_sms_template_model",
]
