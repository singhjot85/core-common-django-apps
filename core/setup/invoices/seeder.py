"""
Development mock seeders for Invoices application.
"""

from __future__ import annotations

from core.apps.invoices import (
    get_billing_organization_model,
    get_invoice_item_model,
    get_invoice_party_email_model,
    get_invoice_party_model,
    get_invoice_party_phone_model,
    get_organization_email_model,
    get_organization_phone_model,
)
from core.libraries.seeder import (
    BaseSeeder,
    CreateObject,
    FileBasedLoader,
    GetorCreateObject,
)
from core.setup.crm.seeder import DevCustomerSeeder

BillingOrg = get_billing_organization_model()
OrgEmail = get_organization_email_model()
OrgPhone = get_organization_phone_model()
InvoiceParty = get_invoice_party_model()
InvoicePartyEmail = get_invoice_party_email_model()
InvoicePartyPhone = get_invoice_party_phone_model()
InvoiceItem = get_invoice_item_model()


class DevBillingOrganizationSeeder(BaseSeeder):
    """Dev seeder for mock billing organizations."""

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_billing_organization/organizations.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = GetorCreateObject(
        model=BillingOrg,
        lookup_fields=["organization_name"],
        default_fields=["billing_suffix", "billing_start_sequence"],
    )


class DevOrganizationEmailSeeder(BaseSeeder):
    """Dev seeder for mock organization emails."""

    depends_on = [DevBillingOrganizationSeeder]

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_organization_email/emails.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = CreateObject(
        model=OrgEmail,
        fields=["organization", "email", "type", "is_primary"],
    )


class DevOrganizationPhoneSeeder(BaseSeeder):
    """Dev seeder for mock organization phones."""

    depends_on = [DevBillingOrganizationSeeder]

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_organization_phone/phones.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = CreateObject(
        model=OrgPhone,
        fields=["organization", "phone", "type", "is_primary"],
    )


class DevInvoicePartySeeder(BaseSeeder):
    """Dev seeder for mock invoice parties."""

    depends_on = [DevCustomerSeeder]
    execution_order: int = 3

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_invoice_party/parties.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = GetorCreateObject(
        model=InvoiceParty,
        lookup_fields=["first_name", "last_name"],
        default_fields=["party_type", "customer"],
    )


class DevInvoicePartyEmailSeeder(BaseSeeder):
    """Dev seeder for mock invoice party emails."""

    depends_on = [DevInvoicePartySeeder]

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_invoice_party_email/emails.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = CreateObject(
        model=InvoicePartyEmail,
        fields=["invoice_party", "email", "email_type"],
    )


class DevInvoicePartyPhoneSeeder(BaseSeeder):
    """Dev seeder for mock invoice party phones."""

    depends_on = [DevInvoicePartySeeder]

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_invoice_party_phone/phones.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = CreateObject(
        model=InvoicePartyPhone,
        fields=["invoice_party", "phone", "phone_type"],
    )


class DevInvoiceItemSeeder(BaseSeeder):
    """Dev seeder for mock invoice catalog items."""

    loader = FileBasedLoader(
        directory_name="setup/invoices/dev_invoice_item/items.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = GetorCreateObject(
        model=InvoiceItem,
        lookup_fields=["name"],
        default_fields=["description", "price", "HSN_code", "is_active"],
    )
