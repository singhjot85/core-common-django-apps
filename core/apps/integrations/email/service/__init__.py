"""
Email service factory and service exports.
"""

from django.core.exceptions import ImproperlyConfigured

from core.apps.integrations import get_integration_model

from ...constants import IntegrationKeyChoices
from .base import BaseEmailService
from .email import EmailService
from .mock import MockEmailService


def get_email_service() -> BaseEmailService:
    """
    Resolve and instantiate the appropriate email service for the current tenant.

    Queries the active tenant schema for an email Integration record.
    Returns ``MockEmailService`` if mock mode is enabled on the integration,
    or ``EmailService`` for live delivery.

    Returns:
        BaseEmailService: Configured active email service instance.

    Raises:
        ImproperlyConfigured:
        - When no Integration record exists with ``integration_key="email"``.
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
