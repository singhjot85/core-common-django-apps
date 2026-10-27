from decimal import Decimal

import pytest
from django.db import connection

from core.apps.integrations import get_integration_model
from core.apps.integrations.constants import IntegrationKeyChoices
from core.apps.integrations.payments import get_payment_log_model
from core.apps.integrations.payments.service import get_payment_service
from core.apps.integrations.payments.constants import PaymentLogStatusChoices
from core.apps.integrations.payments.service.mock import MockPaymentService
from core.apps.integrations.payments.tasks import log_payment_dispatch

PaymentLog = get_payment_log_model()
Integration = get_integration_model()


@pytest.mark.django_db
class TestPaymentsIntegration:
    def test_payment_service_mock_routing(self):
        integration = Integration.objects.create(
            integration_key=IntegrationKeyChoices.PAYMENT,
            label="Dev Mock Gateway",
            mock=True,
        )
        service = get_payment_service(integration=integration)
        assert isinstance(service, MockPaymentService)

        charge_result = service.charge(
            amount=Decimal("49.99"),
            currency="USD",
            source="tok_visa",
        )
        assert charge_result["success"] is True
        assert charge_result["transaction_id"].startswith("mock_tx_")

        refund_result = service.refund(
            transaction_id=charge_result["transaction_id"],
            amount=Decimal("49.99"),
        )
        assert refund_result["success"] is True
        assert refund_result["refund_id"].startswith("mock_ref_")

    def test_log_payment_dispatch_task(self):
        log_id = log_payment_dispatch(
            schema_name=connection.schema_name,
            transaction_id="tx_12345",
            amount="99.00",
            currency="USD",
            status=PaymentLogStatusChoices.SUCCESS,
            gateway="ConsolePaymentBackend",
            source="card_xyz",
            message="Charged",
        )
        log = PaymentLog.objects.get(id=log_id)
        assert log.transaction_id == "tx_12345"
        assert log.amount == Decimal("99.00")
        assert log.status == PaymentLogStatusChoices.SUCCESS
