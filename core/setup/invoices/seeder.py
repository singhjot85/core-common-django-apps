"""
Development mock seeders for Invoices application.
"""

import os

from django.conf import settings

from core.apps.invoices import (
    get_billing_organization_model,
    get_invoice_item_model,
    get_invoice_party_email_model,
    get_invoice_party_model,
    get_invoice_party_phone_model,
    get_organization_email_model,
    get_organization_phone_model,
)
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class DevBillingOrganizationSeeder(BaseSeeder):
    """Dev seeder for mock billing organizations."""

    class Meta(BaseMeta):
        model = get_billing_organization_model()
        fields = [
            "organization_name",
            "billing_suffix",
            "billing_start_sequence",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_billing_organization/organizations.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevOrganizationEmailSeeder(BaseSeeder):
    """Dev seeder for mock organization emails."""

    class Meta(BaseMeta):
        model = get_organization_email_model()
        fields = ["organization", "email", "type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_organization_email/emails.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"organization": DevBillingOrganizationSeeder}


class DevOrganizationPhoneSeeder(BaseSeeder):
    """Dev seeder for mock organization phones."""

    class Meta(BaseMeta):
        model = get_organization_phone_model()
        fields = ["organization", "phone", "type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_organization_phone/phones.json",
            )
        )
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
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party/parties.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevInvoicePartyEmailSeeder(BaseSeeder):
    """Dev seeder for mock invoice party emails."""

    class Meta(BaseMeta):
        model = get_invoice_party_email_model()
        fields = ["invoice_party", "email", "email_type"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party_email/emails.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"invoice_party": DevInvoicePartySeeder}


class DevInvoicePartyPhoneSeeder(BaseSeeder):
    """Dev seeder for mock invoice party phones."""

    class Meta(BaseMeta):
        model = get_invoice_party_phone_model()
        fields = ["invoice_party", "phone", "phone_type"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party_phone/phones.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"invoice_party": DevInvoicePartySeeder}


class DevInvoiceItemSeeder(BaseSeeder):
    """Dev seeder for mock invoice catalog items."""

    class Meta(BaseMeta):
        model = get_invoice_item_model()
        fields = ["name", "description", "price", "HSN_code", "is_active"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_item/items.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {}
