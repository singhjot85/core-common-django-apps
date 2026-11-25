"""
Model factories for the CRM application.
"""

import factory

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_identification_model,
    get_customer_model,
    get_customer_phone_model,
    get_customer_preference_model,
    get_customer_preference_type_model,
)
from core.apps.crm.constants import (
    AddressTypeChoices,
    ContactTypeChoices,
    CustomerStatusChoices,
    CustomerTypeChoices,
    IdentityStatusChoices,
    IdentityTypeChoices,
    PreferenceDataTypeChoices,
)

Customer = get_customer_model()
CustomerPhone = get_customer_phone_model()
CustomerEmail = get_customer_email_model()
CustomerAddress = get_customer_address_model()
CustomerIdentification = get_customer_identification_model()
CustomerPreferenceType = get_customer_preference_type_model()
CustomerPreference = get_customer_preference_model()


class CustomerFactory(factory.django.DjangoModelFactory):
    """Factory for generating Customer records."""

    class Meta:
        model = Customer

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    customer_type = CustomerTypeChoices.INDIVIDUAL
    status = CustomerStatusChoices.ONBOARDING
    is_active = True


class CustomerPhoneFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerPhone records."""

    class Meta:
        model = CustomerPhone

    customer = factory.SubFactory(CustomerFactory)
    phone = factory.Sequence(lambda n: f"+1555111{n:04d}")
    phone_type = ContactTypeChoices.PERSONAL
    is_primary = False
    is_verified = False


class CustomerEmailFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerEmail records."""

    class Meta:
        model = CustomerEmail

    customer = factory.SubFactory(CustomerFactory)
    email = factory.Sequence(lambda n: f"customer_{n}@example.com")
    email_type = ContactTypeChoices.PERSONAL
    is_primary = False
    is_verified = False


class CustomerAddressFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerAddress records."""

    class Meta:
        model = CustomerAddress

    customer = factory.SubFactory(CustomerFactory)
    address_line_1 = factory.Faker("street_address")
    city = factory.Faker("city")
    postal_code = "10001"
    country = "US"
    address_type = AddressTypeChoices.CURRENT
    is_primary = False


class CustomerIdentificationFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerIdentification records."""

    class Meta:
        model = CustomerIdentification

    customer = factory.SubFactory(CustomerFactory)
    type = IdentityTypeChoices.AADHAAR
    status = IdentityStatusChoices.UNVERIFIED.value
    is_verified = False


class CustomerPreferenceTypeFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerPreferenceType records."""

    class Meta:
        model = CustomerPreferenceType

    code = factory.Sequence(lambda n: f"pref_{n}")
    label = factory.Sequence(lambda n: f"Preference {n}")
    data_type = PreferenceDataTypeChoices.BOOLEAN


class CustomerPreferenceFactory(factory.django.DjangoModelFactory):
    """Factory for generating CustomerPreference records."""

    class Meta:
        model = CustomerPreference

    customer = factory.SubFactory(CustomerFactory)
    preference_type = factory.SubFactory(CustomerPreferenceTypeFactory)
    value = True
