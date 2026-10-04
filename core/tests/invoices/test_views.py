from decimal import Decimal
from unittest.mock import MagicMock

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from core.apps.invoices.api.serializers import (
    InvoiceAddressSerializer,
    InvoiceItemEntrySerializer,
)
from core.apps.invoices.api.views import BillingOrganizationViewSet, InvoiceViewSet
from core.apps.invoices.models import InvoiceAddress, InvoiceItemEntry


class TestInvoiceViewSetRestrictions:
    """Unit tests ensuring HTTP method restrictions and custom actions work properly."""

    def _get_auth_user(self):
        user = MagicMock()
        user.is_authenticated = True
        return user

    def test_invoice_viewset_delete_blocked(self):
        """Invoices are immutable snapshot records and cannot be deleted via API."""
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = InvoiceViewSet.as_view({"delete": "destroy"})

        delete_request = factory.delete("/invoices/123/")
        force_authenticate(delete_request, user=user)
        response = view(delete_request, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_billing_org_viewset_delete_blocked(self):
        """Resource viewsets block hard deletion."""
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = BillingOrganizationViewSet.as_view({"delete": "destroy"})

        delete_request = factory.delete("/billing-organizations/123/")
        force_authenticate(delete_request, user=user)
        response = view(delete_request, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestInvoiceSerializers:
    """Unit tests for invoice API serializers."""

    def test_address_serializer_full_address(self):
        address = InvoiceAddress(
            address_line_1="100 Innovation Blvd",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
            country="IN",
        )
        serializer = InvoiceAddressSerializer(address)
        assert (
            serializer.data["full_address"]
            == "100 Innovation Blvd, Pune, Maharashtra, 411001, IN"
        )

    def test_item_entry_serializer_computed_fields(self):
        entry = InvoiceItemEntry(
            item_name="Consulting Hours",
            price=Decimal("2000.00"),
            quantity=Decimal("3.00"),
        )
        entry.__dict__["total_fee_amount"] = Decimal("1080.00")
        entry.__dict__["grand_total"] = Decimal("7080.00")

        # Mock reverse relation on instance
        original_fees = InvoiceItemEntry.fees
        try:
            mock_fees_manager = MagicMock()
            mock_fees_manager.__get__ = MagicMock(
                return_value=MagicMock(all=MagicMock(return_value=[]))
            )
            InvoiceItemEntry.fees = mock_fees_manager

            serializer = InvoiceItemEntrySerializer(entry)
            assert serializer.data["total_price"] == "6000.00"
            assert serializer.data["total_fee_amount"] == "1080.00"
            assert serializer.data["grand_total"] == "7080.00"
        finally:
            InvoiceItemEntry.fees = original_fees
