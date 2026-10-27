import typing

from django.apps import apps as django_apps
from django.conf import settings

from core.apps.integrations.payments.app_settings import (
    IntegrationsPaymentsSettings,
)

if typing.TYPE_CHECKING:
    from .models_abstract import AbstractPaymentLog


app_settings: IntegrationsPaymentsSettings = IntegrationsPaymentsSettings()


def get_payment_log_model():
    """Return the configured PaymentLog model."""
    return typing.cast(
        type["AbstractPaymentLog"],
        django_apps.get_model(
            settings.INTEGRATIONS_PAYMENTS_PAYMENT_LOG_MODEL,
            require_ready=False,
        ),
    )


__all__ = [
    "app_settings",
    "get_payment_log_model",
]
