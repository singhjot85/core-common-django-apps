"""
Development mock seeders for CRM application.
"""

import os

from django.conf import settings

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_model,
    get_customer_phone_model,
)
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class DevCustomerSeeder(BaseSeeder):
    """Dev seeder for mock customers."""

    class Meta(BaseMeta):
        model = get_customer_model()
        fields = [
            "first_name",
            "last_name",
            "business_name",
            "customer_type",
            "status",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        schema_name = "private"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer/customers.json"
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {}


class DevCustomerPhoneSeeder(BaseSeeder):
    """Dev seeder for mock customer phone numbers."""

    class Meta(BaseMeta):
        model = get_customer_phone_model()
        fields = ["customer", "phone", "phone_type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        schema_name = "private"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer_phone/phones.json"
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"customer": DevCustomerSeeder}


class DevCustomerEmailSeeder(BaseSeeder):
    """Dev seeder for mock customer email addresses."""

    class Meta(BaseMeta):
        model = get_customer_email_model()
        fields = ["customer", "email", "email_type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        schema_name = "private"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer_email/emails.json"
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"customer": DevCustomerSeeder}


class DevCustomerAddressSeeder(BaseSeeder):
    """Dev seeder for mock customer addresses."""

    class Meta(BaseMeta):
        model = get_customer_address_model()
        fields = [
            "customer",
            "address_line_1",
            "city",
            "state",
            "postal_code",
            "country",
            "address_type",
            "is_primary",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        schema_name = "private"
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/crm/dev_customer_address/addresses.json",
            )
        )
        depends_on = []
        is_fixture = False
        related_seeders = {"customer": DevCustomerSeeder}
