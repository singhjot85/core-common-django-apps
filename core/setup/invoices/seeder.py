"""
Development mock seeders for Invoices application.
"""

import os

from django.conf import settings

from core.apps.crm import get_customer_model  # noqa: F401
from core.apps.invoices import (  # noqa: F401
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


class DevOrganizationEmailSeeder(BaseSeeder):
    """Dev seeder for mock organization emails."""

    class Meta(BaseMeta):
        model = get_organization_email_model()
        fields = ["organization__organization_name", "email", "type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_organization_email/emails.json",
            )
        )
        depends_on = [get_billing_organization_model()]


class DevOrganizationPhoneSeeder(BaseSeeder):
    """Dev seeder for mock organization phones."""

    class Meta(BaseMeta):
        model = get_organization_phone_model()
        fields = ["organization__organization_name", "phone", "type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_organization_phone/phones.json",
            )
        )
        depends_on = [get_billing_organization_model()]


class DevInvoicePartySeeder(BaseSeeder):
    """Dev seeder for mock invoice parties."""

    class Meta(BaseMeta):
        model = get_invoice_party_model()
        fields = [
            "first_name",
            "last_name",
            "party_type",
            "customer__first_name",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party/parties.json",
            )
        )
        depends_on = [get_customer_model()]
        execution_order = 3


class DevInvoicePartyEmailSeeder(BaseSeeder):
    """Dev seeder for mock invoice party emails."""

    class Meta(BaseMeta):
        model = get_invoice_party_email_model()
        fields = ["invoice_party__first_name", "email", "email_type"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party_email/emails.json",
            )
        )
        depends_on = [get_invoice_party_model()]


class DevInvoicePartyPhoneSeeder(BaseSeeder):
    """Dev seeder for mock invoice party phones."""

    class Meta(BaseMeta):
        model = get_invoice_party_phone_model()
        fields = ["invoice_party__first_name", "phone", "phone_type"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/invoices/dev_invoice_party_phone/phones.json",
            )
        )
        depends_on = [get_invoice_party_model()]


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
