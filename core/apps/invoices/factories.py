"""
Model factories for the invoices application.
"""

from decimal import Decimal

import factory

from core.apps.invoices import (
    get_billing_organization_model,
    get_invoice_address_model,
    get_invoice_item_model,
    get_invoice_model,
    get_invoice_party_category_model,
    get_invoice_party_email_model,
    get_invoice_party_model,
    get_invoice_party_phone_model,
    get_invoice_template_model,
)
from core.apps.invoices.constants import ContactTypeChoices

BillingOrganization = get_billing_organization_model()
InvoicePartyCategory = get_invoice_party_category_model()
InvoiceParty = get_invoice_party_model()
InvoicePartyEmail = get_invoice_party_email_model()
InvoicePartyPhone = get_invoice_party_phone_model()
InvoiceAddress = get_invoice_address_model()
InvoiceTemplate = get_invoice_template_model()
Invoice = get_invoice_model()
InvoiceItem = get_invoice_item_model()


class BillingOrganizationFactory(factory.django.DjangoModelFactory):
    """Factory for generating BillingOrganization records."""

    class Meta:
        model = BillingOrganization

    organization_name = factory.Sequence(lambda n: f"Billing Org {n}")
    billing_suffix = ""
    billing_start_sequence = 1


class InvoicePartyCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoicePartyCategory records."""

    class Meta:
        model = InvoicePartyCategory

    category_name = factory.Sequence(lambda n: f"Category {n}")


class InvoicePartyFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoiceParty records."""

    class Meta:
        model = InvoiceParty

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class InvoicePartyEmailFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoicePartyEmail records."""

    class Meta:
        model = InvoicePartyEmail

    invoice_party = factory.SubFactory(InvoicePartyFactory)
    email = factory.Sequence(lambda n: f"party_{n}@example.com")
    email_type = ContactTypeChoices.PRIMARY


class InvoicePartyPhoneFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoicePartyPhone records."""

    class Meta:
        model = InvoicePartyPhone

    invoice_party = factory.SubFactory(InvoicePartyFactory)
    phone = factory.Sequence(lambda n: f"+1555222{n:04d}")
    phone_type = ContactTypeChoices.PRIMARY


class InvoiceAddressFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoiceAddress records."""

    class Meta:
        model = InvoiceAddress

    address_line_1 = factory.Faker("street_address")
    city = factory.Faker("city")
    postal_code = "10001"
    country = "US"


class InvoiceTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoiceTemplate records."""

    class Meta:
        model = InvoiceTemplate

    name = factory.Sequence(lambda n: f"Invoice Template {n}")
    template = "<h1>Invoice</h1>"
    html_template = "<h1>Invoice</h1>"
    interface_type = "base_template"
    version = "1.0.0"


class InvoiceItemFactory(factory.django.DjangoModelFactory):
    """Factory for generating InvoiceItem records."""

    class Meta:
        model = InvoiceItem

    name = factory.Sequence(lambda n: f"Item {n}")
    price = Decimal("10.00")
    current_stock = 100
    is_active = True


class InvoiceFactory(factory.django.DjangoModelFactory):
    """Factory for generating Invoice records."""

    class Meta:
        model = Invoice

    invoice_number = factory.Sequence(lambda n: f"INV-{n:05d}")
    party = factory.SubFactory(InvoicePartyFactory)
    biller = factory.SubFactory(BillingOrganizationFactory)
    billing_address = factory.SubFactory(InvoiceAddressFactory)
