import pytest

from core.apps.integrations import (
    get_credentials_manager_model,
    get_integration_model,
)
from core.apps.integrations.constants import (
    CredentialsNameChoices,
    IntegrationKeyChoices,
)
from core.apps.integrations.utils import send_email, send_sms

Integration = get_integration_model()
CredentialsManager = get_credentials_manager_model()


@pytest.mark.django_db
class TestIntegrationsModels:
    def test_credentials_manager_lifecycle(self):
        creds = CredentialsManager.objects.create(
            name=CredentialsNameChoices.TWILIO,
            details={
                "account_sid": "AC123",
                "auth_token": "mock_token",
            },  # pragma: allowlist secret
        )
        assert creds.name == CredentialsNameChoices.TWILIO
        assert creds.details["account_sid"] == "AC123"
        assert str(creds) == f"{creds.get_name_display()} ({creds.pk})"

    def test_integration_lifecycle(self):
        creds = CredentialsManager.objects.create(
            name=CredentialsNameChoices.SENDGRID,
            details={"api_key": "SG.mock_key"},  # pragma: allowlist secret
        )
        integration = Integration.objects.create(
            integration_key=IntegrationKeyChoices.EMAIL,
            label="Corporate SendGrid",
            credentials=creds,
            mock=True,
            has_webhooks=True,
        )
        assert integration.mock is True
        assert integration.has_webhooks is True
        assert integration.credentials == creds
        assert (
            str(integration)
            == f"Corporate SendGrid ({integration.get_integration_key_display()})"
        )

    def test_send_email_and_sms_facades(self):
        # With mock=True on integration
        email_integration = Integration.objects.create(
            integration_key=IntegrationKeyChoices.EMAIL,
            label="Mock Email",
            mock=True,
        )
        sms_integration = Integration.objects.create(
            integration_key=IntegrationKeyChoices.SMS,
            label="Mock SMS",
            mock=True,
        )

        email_result = send_email(
            to="user@example.com",
            subject="Hello",
            plain_body="Test message",
            integration=email_integration,
        )
        assert email_result is True

        sms_result = send_sms(
            to="+15550001111",
            message="Test SMS",
            integration=sms_integration,
        )
        assert sms_result is True
