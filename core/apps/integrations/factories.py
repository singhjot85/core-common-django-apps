"""
Model factories for root integrations and credentials, re-exporting sub-app factories.
"""

import factory

from core.apps.integrations import (
    get_credentials_manager_model,
    get_integration_model,
)
from core.apps.integrations.constants import (
    CredentialsNameChoices,
    IntegrationKeyChoices,
)
from core.apps.integrations.email.factories import (
    EmailLogFactory,
    EmailTemplateFactory,
)
from core.apps.integrations.sms.factories import (
    SMSLogFactory,
    SMSTemplateFactory,
)

Integration = get_integration_model()
CredentialsManager = get_credentials_manager_model()


class CredentialsManagerFactory(factory.django.DjangoModelFactory):
    """Factory for generating provider credentials instances."""

    class Meta:
        model = CredentialsManager

    name = CredentialsNameChoices.CUSTOM
    details = factory.LazyFunction(dict)


class IntegrationFactory(factory.django.DjangoModelFactory):
    """Factory for generating Integration service configuration instances."""

    class Meta:
        model = Integration

    integration_key = IntegrationKeyChoices.EMAIL
    label = factory.Sequence(lambda n: f"Integration {n}")
    is_active = True
    mock = True


__all__ = [
    "CredentialsManagerFactory",
    "EmailLogFactory",
    "EmailTemplateFactory",
    "IntegrationFactory",
    "SMSLogFactory",
    "SMSTemplateFactory",
]
