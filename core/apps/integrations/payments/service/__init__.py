"""
Payment service factory and service exports.
"""

from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BasePaymentService
from .mock import MockPaymentService
from .payment import PaymentService


def get_payment_service() -> BasePaymentService:
    """
    Resolve and instantiate the appropriate payment service for the current tenant.

    Queries the active tenant schema for a payment Integration record.
    Returns ``MockPaymentService`` if mock mode is enabled on the integration,
    or ``PaymentService`` for live gateway processing.

    Returns:
        BasePaymentService: Configured active payment service instance.

    Raises:
        ImproperlyConfigured:
        - When no Integration record exists with ``integration_key="payment"``.
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
