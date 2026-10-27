from core.apps.integrations import models_abstract


class Integration(models_abstract.AbstractIntegration):
    """Concrete Integration; no fields here. Add them to AbstractIntegration."""

    class Meta(models_abstract.AbstractIntegration.Meta):
        swappable = "INTEGRATIONS_INTEGRATION_MODEL"


class CredentialsManager(models_abstract.AbstractCredentialsManager):
    """Concrete CredentialsManager; no fields here. Add them to AbstractCredentialsManager."""

    class Meta(models_abstract.AbstractCredentialsManager.Meta):
        swappable = "INTEGRATIONS_CREDENTIALS_MANAGER_MODEL"
