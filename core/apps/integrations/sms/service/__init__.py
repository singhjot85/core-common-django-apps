from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BaseSMSService
from .mock import MockSMSService
from .sms import SMSService


def get_sms_service() -> BaseSMSService:
    """
    Return MockSMSService or SMSService.
    If name is provided, resolves the Integration by label.
    If neither name nor integration is provided, returns default SMSService without DB queries.
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
