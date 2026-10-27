from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BaseEmailService
from .email import EmailService
from .mock import MockEmailService


def get_email_service() -> BaseEmailService:
    """
    Return MockEmailService or EmailService.
    If name is provided, resolves the Integration by label.
    If neither name nor integration is provided, returns default EmailService without DB queries.
    """
    Integration = get_integration_model()
    integration = Integration.objects.filter(
        integration_key=IntegrationKeyChoices.EMAIL.value
    ).first()

    if not integration:
        raise ImproperlyConfigured("No integration configured for email")

    if integration and integration.mock:
        return MockEmailService(integration=integration)

    return EmailService(integration=integration)


__all__ = ["BaseEmailService", "EmailService", "MockEmailService", "get_email_service"]
