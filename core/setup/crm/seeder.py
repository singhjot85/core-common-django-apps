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
from core.apps.users import get_user_model
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
            "user__email",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer/customers.json"
            )
        )
        depends_on = [get_user_model()]


class DevCustomerPhoneSeeder(BaseSeeder):
    """Dev seeder for mock customer phone numbers."""

    class Meta(BaseMeta):
        model = get_customer_phone_model()
        fields = ["customer__first_name", "phone", "phone_type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer_phone/phones.json"
            )
        )
        depends_on = [get_customer_model()]


class DevCustomerEmailSeeder(BaseSeeder):
    """Dev seeder for mock customer email addresses."""

    class Meta(BaseMeta):
        model = get_customer_email_model()
        fields = ["customer__first_name", "email", "email_type", "is_primary"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer_email/emails.json"
            )
        )
        depends_on = [get_customer_model()]


class DevCustomerAddressSeeder(BaseSeeder):
    """Dev seeder for mock customer addresses."""

    class Meta(BaseMeta):
        model = get_customer_address_model()
        fields = [
            "customer__first_name",
            "address_line_1",
            "city",
            "state",
            "postal_code",
            "country",
            "address_type",
            "is_primary",
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR,
                "setup/crm/dev_customer_address/addresses.json",
            )
        )
        depends_on = [get_customer_model()]
