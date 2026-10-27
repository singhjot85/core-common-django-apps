import pytest

from core.apps.integrations import get_integration_model
from core.apps.integrations.constants import IntegrationKeyChoices
from core.apps.integrations.email import (
    get_email_log_model,
    get_email_template_model,
)
from core.apps.integrations.email.constants import (
    EmailLogStatusChoices,
    EmailTemplateInterfaceTypeChoices,
)
from core.apps.integrations.email.service import get_email_service
from core.apps.integrations.email.service.mock import MockEmailService
from core.apps.integrations.email.tasks import log_email_dispatch

EmailLog = get_email_log_model()
EmailTemplate = get_email_template_model()
Integration = get_integration_model()


@pytest.mark.django_db
class TestEmailIntegration:
    def test_email_template_render(self):
        template = EmailTemplate.objects.create(
            interface_type=EmailTemplateInterfaceTypeChoices.AUTH,
            subject="Welcome {{ name }}",
            template="Hello {{ name }}, your code is {{ code }}.",
            html_template="<p>Hello {{ name }}, your code is {{ code }}.</p>",
            version="1.0.0",
        )
        assert template.version == "1.0.0"
        service = get_email_service()
        subject, plain, html = service.render_template(
            {
                "subject": template.subject,
                "template": template.template,
                "html_template": template.html_template,
            },
            {"name": "Alice", "code": "123456"},
        )
        assert "Welcome Alice" in subject
        assert "Hello Alice, your code is 123456." in plain
        assert "<p>Hello Alice" in html

    def test_email_service_mock_routing(self):
        Integration.objects.create(
            integration_key=IntegrationKeyChoices.EMAIL,
            label="Dev Mock Email",
            mock=True,
        )
        service = get_email_service(name="Dev Mock Email")
        assert isinstance(service, MockEmailService)
        success = service.send(
            to="test@example.com",
            subject="Test Mock",
            plain_body="Body",
        )
        assert success is True

    def test_log_email_dispatch_task(self):
        log_id = log_email_dispatch(
            recipient="audit@example.com",
            subject="Test Dispatch",
            status=EmailLogStatusChoices.SUCCESS,
            backend="ConsoleEmailBackend",
            message="Sent successfully",
        )
        log = EmailLog.objects.get(id=log_id)
        assert log.recipient == "audit@example.com"
        assert log.status == EmailLogStatusChoices.SUCCESS
        assert log.backend == "ConsoleEmailBackend"
