from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BasePaymentService
from .mock import MockPaymentService
from .payment import PaymentService


def get_payment_service() -> BasePaymentService:
    """
    Return MockPaymentService or PaymentService.
    If name is provided, resolves the Integration by label.
    If neither name nor integration is provided, returns default PaymentService without DB queries.
    """
    Integration = get_integration_model()
    integration = Integration.objects.filter(
        label=IntegrationKeyChoices.PAYMENT.value
    ).first()

    if not integration:
        raise ImproperlyConfigured("No Integration Configured for Payments.")

    if integration and integration.mock:
        return MockPaymentService(integration=integration)

    return PaymentService(integration=integration)


__all__ = [
    "BasePaymentService",
    "MockPaymentService",
    "PaymentService",
    "get_payment_service",
]
