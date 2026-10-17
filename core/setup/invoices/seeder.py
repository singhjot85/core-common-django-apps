from core.apps.invoices import (
    get_billing_organization_model,
    get_invoice_item_model,
    get_invoice_model,
    get_invoice_party_email_model,
    get_invoice_party_model,
    get_invoice_party_phone_model,
    get_organization_email_model,
    get_organization_phone_model,
)
from core.seeder.base import BaseMeta, BaseSeeder


class DevBillingOrganizationSeeder(BaseSeeder):
    """Dev seeder for mock billing organizations."""

    class Meta(BaseMeta):
        model = get_billing_organization_model()
        fields = [
            "organization_name",
            "billing_suffix",
            "billing_start_sequence",
        ]
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevOrganizationEmailSeeder(BaseSeeder):
    """Dev seeder for mock organization emails."""

    class Meta(BaseMeta):
        model = get_organization_email_model()
        fields = ["organization", "email", "type", "is_primary"]
        depends_on = []
        is_fixture = False
        related_seeders = {"organization": DevBillingOrganizationSeeder}


class DevOrganizationPhoneSeeder(BaseSeeder):
    """Dev seeder for mock organization phones."""

    class Meta(BaseMeta):
        model = get_organization_phone_model()
        fields = ["organization", "phone", "type", "is_primary"]
        depends_on = []
        is_fixture = False
        related_seeders = {"organization": DevBillingOrganizationSeeder}


class DevInvoicePartySeeder(BaseSeeder):
    """Dev seeder for mock invoice parties."""

    class Meta(BaseMeta):
        model = get_invoice_party_model()
        fields = [
            "first_name",
            "last_name",
            "party_type",
            "customer",
        ]
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevInvoicePartyEmailSeeder(BaseSeeder):
    """Dev seeder for mock invoice party emails."""

    class Meta(BaseMeta):
        model = get_invoice_party_email_model()
        fields = ["invoice_party", "email", "email_type"]
        depends_on = []
        is_fixture = False
        related_seeders = {"invoice_party": DevInvoicePartySeeder}


class DevInvoicePartyPhoneSeeder(BaseSeeder):
    """Dev seeder for mock invoice party phones."""

    class Meta(BaseMeta):
        model = get_invoice_party_phone_model()
        fields = ["invoice_party", "phone", "phone_type"]
        depends_on = []
        is_fixture = False
        related_seeders = {"invoice_party": DevInvoicePartySeeder}


class DevInvoiceItemSeeder(BaseSeeder):
    """Dev seeder for mock invoice catalog items."""

    class Meta(BaseMeta):
        model = get_invoice_item_model()
        fields = ["name", "description", "price", "HSN_code", "is_active"]
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevInvoiceSeeder(BaseSeeder):
    """Dev seeder for mock invoices."""

    class Meta(BaseMeta):
        model = get_invoice_model()
        fields = [
            "invoice_number",
            "invoice_date",
            "party",
            "biller",
            "billing_address",
        ]
        depends_on = []
        is_fixture = False
        related_seeders = {
            "party": DevInvoicePartySeeder,
            "biller": DevBillingOrganizationSeeder,
        }
