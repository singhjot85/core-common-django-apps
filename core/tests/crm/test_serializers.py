"""
Unit and integration tests for CRM API serializers.
"""

import pytest

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_identification_model,
    get_customer_model,
    get_customer_phone_model,
    get_customer_preference_model,
    get_customer_preference_type_model,
)
from core.apps.crm.api.serializers import (
    CustomerDetailsSerializer,
    CustomerPreferenceSerializer,
    CustomerPreferenceTypeSerializer,
    CustomerSerializer,
)
from core.apps.crm.constants import (
    AddressTypeChoices,
    ContactTypeChoices,
    CustomerStatusChoices,
    CustomerTypeChoices,
    IdentityTypeChoices,
    PreferenceDataTypeChoices,
)

Customer = get_customer_model()
CustomerAddress = get_customer_address_model()
CustomerEmail = get_customer_email_model()
CustomerIdentification = get_customer_identification_model()
CustomerPhone = get_customer_phone_model()
CustomerPreference = get_customer_preference_model()
CustomerPreferenceType = get_customer_preference_type_model()


@pytest.mark.django_db
class TestCRMSerializers:
    """Tests covering serialization and validation of CRM entities."""

    def test_customer_serializer_create_and_validation(self):
        """CustomerSerializer validates payload and creates customer record."""
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "customer_type": CustomerTypeChoices.INDIVIDUAL.value,
            "status": CustomerStatusChoices.ONBOARDING.value,
        }
        serializer = CustomerSerializer(data=payload)
        assert serializer.is_valid(), serializer.errors
        customer = serializer.save()

        assert customer.first_name == "Ada"
        assert customer.last_name == "Lovelace"
        assert customer.is_active is True

    def test_customer_details_serializer_read_only_embedding(self):
        """CustomerDetailsSerializer embeds nested contact collections and computed properties."""
        customer = Customer.objects.create(
            first_name="Charles",
            last_name="Babbage",
            suffix="Esq.",
            customer_type=CustomerTypeChoices.INDIVIDUAL,
        )
        CustomerPhone.objects.create(
            customer=customer,
            phone="+919876543210",
            phone_type=ContactTypeChoices.PERSONAL,
            is_primary=True,
        )
        CustomerEmail.objects.create(
            customer=customer,
            email="babbage@example.com",
            email_type=ContactTypeChoices.WORK,
            is_primary=True,
        )
        CustomerAddress.objects.create(
            customer=customer,
            address_line_1="1 Computer Way",
            city="London",
            country="GB",
            address_type=AddressTypeChoices.OFFICE,
            is_primary=True,
        )
        CustomerIdentification.objects.create(
            customer=customer,
            identity_type=IdentityTypeChoices.PASSPORT,
            identity_number="P9876543",
        )
        pref_type = CustomerPreferenceType.objects.create(
            code="notifications",
            label="Email Notifications",
            data_type=PreferenceDataTypeChoices.BOOLEAN,
            default_value=True,
        )
        CustomerPreference.objects.create(
            customer=customer,
            preference_type=pref_type,
            value=True,
        )

        serializer = CustomerDetailsSerializer(instance=customer)
        data = serializer.data

        assert data["id"] == str(customer.id)
        assert data["full_name"] == "Charles Babbage Esq."
        assert len(data["phones"]) == 1
        assert data["phones"][0]["phone"] == "+919876543210"
        assert len(data["emails"]) == 1
        assert data["emails"][0]["email"] == "babbage@example.com"
        assert len(data["addresses"]) == 1
        assert "1 Computer Way" in data["addresses"][0]["full_address"]
        assert len(data["identifications"]) == 1
        assert data["identifications"][0]["identity_type_display"] == "Passport"
        assert len(data["preferences"]) == 1
        assert data["preferences"][0]["preference_code"] == "notifications"

    def test_customer_preference_serializer_resolves_type_code_and_label(self):
        """CustomerPreferenceSerializer resolves preference_code and preference_label from foreign key."""
        customer = Customer.objects.create(first_name="Margaret", last_name="Hamilton")
        pref_type = CustomerPreferenceType.objects.create(
            code="theme",
            label="UI Theme",
            data_type=PreferenceDataTypeChoices.CHOICES,
            values=["light", "dark"],
            default_value="dark",
        )
        pref = CustomerPreference.objects.create(
            customer=customer,
            preference_type=pref_type,
            value="dark",
        )

        serializer = CustomerPreferenceSerializer(instance=pref)
        data = serializer.data

        assert data["preference_code"] == "theme"
        assert data["preference_label"] == "UI Theme"
        assert data["value"] == "dark"

    def test_customer_preference_type_serializer_data_type_display(self):
        """CustomerPreferenceTypeSerializer exposes human-readable data_type_display."""
        pref_type = CustomerPreferenceType.objects.create(
            code="multi_channel",
            label="Notification Channels",
            data_type=PreferenceDataTypeChoices.MULTI_SELECT,
            values=["sms", "email", "push"],
            default_value=["sms", "email"],
        )

        serializer = CustomerPreferenceTypeSerializer(instance=pref_type)
        data = serializer.data

        assert data["code"] == "multi_channel"
        assert data["data_type"] == PreferenceDataTypeChoices.MULTI_SELECT.value
        assert data["data_type_display"] == "Multi-Select"
