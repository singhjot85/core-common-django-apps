"""
Concrete swappable models for the core integrations framework.
"""

from core.apps.integrations import models_abstract


class Integration(models_abstract.AbstractIntegration):
    """
    Concrete swappable model representing a service integration configuration.
    """

    class Meta(models_abstract.AbstractIntegration.Meta):
        swappable = "INTEGRATIONS_INTEGRATION_MODEL"


class CredentialsManager(models_abstract.AbstractCredentialsManager):
    """
    Concrete swappable model representing provider secrets and credential storage.
    """

    class Meta(models_abstract.AbstractCredentialsManager.Meta):
        swappable = "INTEGRATIONS_CREDENTIALS_MANAGER_MODEL"
