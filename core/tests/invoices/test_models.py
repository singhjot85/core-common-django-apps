from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from core.apps.invoices import (
    get_billing_organization_model,
    get_invoice_address_model,
    get_invoice_item_entry_model,
    get_invoice_item_fee_model,
    get_invoice_item_model,
    get_invoice_model,
    get_invoice_party_category_model,
    get_invoice_party_email_model,
    get_invoice_party_model,
    get_invoice_party_phone_model,
    get_invoice_template_model,
    get_organization_assets_model,
    get_organization_email_model,
    get_organization_financials_model,
    get_organization_phone_model,
)
from core.apps.invoices.constants import PartyTypeChoices

Invoice = get_invoice_model()
InvoiceAddress = get_invoice_address_model()
InvoiceTemplate = get_invoice_template_model()
BillingOrganization = get_billing_organization_model()
OrganizationEmail = get_organization_email_model()
OrganizationPhone = get_organization_phone_model()
OrganizationFinancials = get_organization_financials_model()
OrganizationAssets = get_organization_assets_model()
InvoiceParty = get_invoice_party_model()
InvoicePartyCategory = get_invoice_party_category_model()
InvoicePartyEmail = get_invoice_party_email_model()
InvoicePartyPhone = get_invoice_party_phone_model()
InvoiceItem = get_invoice_item_model()
InvoiceItemEntry = get_invoice_item_entry_model()
InvoiceItemFee = get_invoice_item_fee_model()


class TestInvoiceModelUnits:
    """Unit tests for Invoice models, cached properties, and calculation helpers."""

    def test_invoice_address_full_address(self):
        """Test formatted full address generation."""
        address = InvoiceAddress(
            address_line_1="123 Tech Park",
            address_line_2="Sector 62",
            landmark="Near Metro Station",
            city="Noida",
            state="Uttar Pradesh",
            postal_code="201301",
            country="IN",
        )
        assert (
            address.full_address
            == "123 Tech Park, Sector 62, Near Metro Station, Noida, Uttar Pradesh, 201301, IN"
        )

    def test_invoice_party_full_name(self):
        """Test party full name and business name fallback."""
        party_person = InvoiceParty(
            first_name="Jane",
            last_name="Doe",
            party_type=PartyTypeChoices.CUSTOMER,
        )
        assert party_person.full_name == "Jane Doe"

        party_biz = InvoiceParty(
            business_name="Acme Solutions Pvt Ltd",
            party_type=PartyTypeChoices.CUSTOMER,
        )
        assert party_biz.full_name == "Acme Solutions Pvt Ltd"

    def test_item_entry_and_fee_calculations(self):
        """Test calculation of line total, fees, and grand total."""
        entry = InvoiceItemEntry(
            item_name="Consulting Services",
            price=Decimal("1000.00"),
            quantity=Decimal("2.50"),
        )
        assert entry.total_price == Decimal("2500.00")

        fee = InvoiceItemFee(
            item_entry=entry,
            rate=Decimal("18.00"),
            description="GST 18%",
        )
        assert fee.fee_amount == Decimal("450.00")

    def test_invoice_template_version_tracking(self):
        """Test invoice template creation and default version representation."""
        template = InvoiceTemplate(
            name="Standard Tax Invoice",
            html_template="<html><body><h1>Invoice</h1></body></html>",
            version_major=1,
            version_minor=2,
            version_patch=3,
            version=None,
        )
        template.resolve_version()
        assert template.version == "1.2.3"

    def test_billing_organization_invoice_number_generation_logic(self):
        """Test sequence and suffix computation for billing organization."""
        org = BillingOrganization(
            organization_name="TechCorp",
            billing_suffix="/2026-27",
            billing_start_sequence=50,
            billing_current_sequence=0,
        )
        org.save = MagicMock()

        inv_num_1 = org.generate_next_invoice_number()
        assert inv_num_1 == "50/2026-27"
        assert org.billing_current_sequence == 50

        inv_num_2 = org.generate_next_invoice_number()
        assert inv_num_2 == "51/2026-27"
        assert org.billing_current_sequence == 51

    def test_invoice_cached_totals_aggregation(self):
        """Test aggregation of line item entries and fees on an Invoice instance."""
        invoice = Invoice(invoice_number="INV-001")

        entry1 = InvoiceItemEntry(
            invoice=invoice,
            item_name="Product A",
            price=Decimal("100.00"),
            quantity=Decimal("2.00"),
        )
        entry1.__dict__["total_fee_amount"] = Decimal("20.00")

        entry2 = InvoiceItemEntry(
            invoice=invoice,
            item_name="Product B",
            price=Decimal("200.00"),
            quantity=Decimal("1.00"),
        )
        entry2.__dict__["total_fee_amount"] = Decimal("10.00")

        # Mock entries property on invoice
        invoice.__dict__["entries"] = [entry1, entry2]

        assert invoice.subtotal == Decimal("400.00")
        assert invoice.total_fees == Decimal("30.00")
        assert invoice.grand_total == Decimal("430.00")


@pytest.mark.django_db
class TestInvoiceModelDB:
    """Database integration tests for invoice models."""

    def test_db_billing_organization_flow(self):
        """Test DB persistence and invoice creation."""
        org = BillingOrganization.objects.create(
            organization_name="TechCorp India",
            billing_suffix="/2026-27",
            billing_start_sequence=100,
        )
        inv_num = org.generate_next_invoice_number()
        assert inv_num == "100/2026-27"
        assert org.billing_current_sequence == 100
