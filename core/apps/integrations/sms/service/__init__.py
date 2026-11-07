"""
SMS service factory and service exports.
"""

from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BaseSMSService
from .mock import MockSMSService
from .sms import SMSService


def get_sms_service() -> BaseSMSService:
    """
    Resolve and instantiate the appropriate SMS service for the current tenant.

    Queries the active tenant schema for an SMS Integration record.
    Returns ``MockSMSService`` if mock mode is enabled on the integration,
    or ``SMSService`` for live delivery.

    Returns:
        BaseSMSService: Configured active SMS service instance.

    Raises:
        ImproperlyConfigured:
        - When no Integration record exists with ``integration_key="sms"``.
    """
    Integration = get_integration_model()
    integration = Integration.objects.filter(
        integration_key=IntegrationKeyChoices.SMS.value
    ).first()

    if not integration:
        raise ImproperlyConfigured("No Integration Configured for sms")

    if integration and integration.mock:
        return MockSMSService(integration=integration)

    return SMSService(integration=integration)


__all__ = ["BaseSMSService", "MockSMSService", "SMSService", "get_sms_service"]
