"""
Development mock seeders for CRM application.
"""

from __future__ import annotations

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_model,
    get_customer_phone_model,
)
from core.libraries.seeder import (
    BaseSeeder,
    FileBasedLoader,
    GetorCreateObject,
)
from core.setup.users.seeders import DevUserSeeder

Customer = get_customer_model()
CustomerPhone = get_customer_phone_model()
CustomerEmail = get_customer_email_model()
CustomerAddress = get_customer_address_model()


class DevCustomerPhoneSeeder(BaseSeeder):
    """Dev child seeder for customer phone numbers."""

    is_root: bool = False

    method = GetorCreateObject(
        model=CustomerPhone,
        lookup_fields=["customer", "phone"],
        default_fields=["phone_type", "is_primary"],
    )


class DevCustomerEmailSeeder(BaseSeeder):
    """Dev child seeder for customer email addresses."""

    is_root: bool = False

    method = GetorCreateObject(
        model=CustomerEmail,
        lookup_fields=["customer", "email"],
        default_fields=["email_type", "is_primary"],
    )


class DevCustomerAddressSeeder(BaseSeeder):
    """Dev child seeder for customer addresses."""

    is_root: bool = False

    method = GetorCreateObject(
        model=CustomerAddress,
        lookup_fields=["customer", "address_line_1", "city"],
        default_fields=[
            "state",
            "postal_code",
            "country",
            "address_type",
            "is_primary",
        ],
    )


class DevCustomerSeeder(BaseSeeder):
    """Dev root seeder for customers, coordinating nested attributes via related_seeder_map."""

    depends_on = [DevUserSeeder]
    execution_order: int = 2

    loader = FileBasedLoader(
        directory_name="setup/crm/dev_customer",
        load_method=FileBasedLoader.LOAD_INDIVIDUAL,
    )
    method = GetorCreateObject(
        model=Customer,
        related_seeder_map={
            "phones": DevCustomerPhoneSeeder,
            "emails": DevCustomerEmailSeeder,
            "addresses": DevCustomerAddressSeeder,
        },
        lookup_fields=["first_name", "last_name"],
        default_fields=[
            "business_name",
            "customer_type",
            "status",
            "user",
            "phones",
            "emails",
            "addresses",
        ],
    )
