import pytest
from django.db import connection

from core.apps.integrations import get_integration_model
from core.apps.integrations.constants import IntegrationKeyChoices
from core.apps.integrations.sms import (
    get_sms_log_model,
    get_sms_template_model,
)
from core.apps.integrations.sms.service import get_sms_service
from core.apps.integrations.sms.constants import (
    SMSLogStatusChoices,
    SMSTemplateInterfaceTypeChoices,
)
from core.apps.integrations.sms.service.mock import MockSMSService
from core.apps.integrations.sms.tasks import log_sms_dispatch

SMSLog = get_sms_log_model()
SMSTemplate = get_sms_template_model()
Integration = get_integration_model()


@pytest.mark.django_db
class TestSMSIntegration:
    def test_sms_template_render(self):
        template = SMSTemplate.objects.create(
            interface_type=SMSTemplateInterfaceTypeChoices.OTP,
            plain_content="Your code is {{ code }}",
            version="1.0.0",
        )
        assert template.version == "1.0.0"
        rendered = MockSMSService().render_template(template, {"code": "654321"})
        assert "Your code is 654321" in rendered

    def test_sms_service_mock_routing(self):
        integration = Integration.objects.create(
            integration_key=IntegrationKeyChoices.SMS,
            label="Dev Mock SMS",
            mock=True,
        )
        service = get_sms_service(integration=integration)
        assert isinstance(service, MockSMSService)
        success = service.send(
            to="+15551234567",
            message="Your OTP is 112233",
        )
        assert success is True

    def test_log_sms_dispatch_task(self):
        log_id = log_sms_dispatch(
            schema_name=connection.schema_name,
            recipient="+15559876543",
            status=SMSLogStatusChoices.SUCCESS,
            backend_used="ConsoleSMSBackend",
            message="Delivered",
        )
        log = SMSLog.objects.get(id=log_id)
        assert log.recipient == "+15559876543"
        assert log.status == SMSLogStatusChoices.SUCCESS
        assert log.backend_used == "ConsoleSMSBackend"
