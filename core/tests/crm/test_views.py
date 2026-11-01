from types import SimpleNamespace

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from core.apps.crm import (
    get_customer_address_model,
    get_customer_email_model,
    get_customer_identification_model,
    get_customer_model,
    get_customer_phone_model,
    get_customer_preference_model,
    get_customer_preference_type_model,
)
from core.apps.crm.api.views import (
    CustomerAddressViewSet,
    CustomerEmailViewSet,
    CustomerIdentificationViewSet,
    CustomerPhoneViewSet,
    CustomerPreferenceTypeViewSet,
    CustomerPreferenceViewSet,
    CustomerViewSet,
)
from core.apps.crm.constants import (
    AddressTypeChoices,
    ContactTypeChoices,
    CustomerTypeChoices,
    IdentityTypeChoices,
    PreferenceDataTypeChoices,
)
from core.apps.users import get_user_model

User = get_user_model()
Customer = get_customer_model()
CustomerAddress = get_customer_address_model()
CustomerEmail = get_customer_email_model()
CustomerIdentification = get_customer_identification_model()
CustomerPhone = get_customer_phone_model()
CustomerPreference = get_customer_preference_model()
CustomerPreferenceType = get_customer_preference_type_model()


class TestCRMViewSetRestrictions:
    """Unit tests ensuring unsupported actions and delete methods are blocked on customer viewsets."""

    def _get_auth_user(self):
        return SimpleNamespace(is_authenticated=True)

    def test_customer_viewset_list_and_delete_blocked(self):
        assert not hasattr(CustomerViewSet, "list")
        assert not hasattr(CustomerViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerViewSet.as_view({"get": "retrieve", "put": "update"})

        delete_request = factory.delete("/customers/123/")
        force_authenticate(delete_request, user=user)
        response = view(delete_request, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_phone_viewset_delete_blocked(self):
        assert not hasattr(CustomerPhoneViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPhoneViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customers/123/phones/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, customer_pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_email_viewset_delete_blocked(self):
        assert not hasattr(CustomerEmailViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerEmailViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customers/123/emails/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, customer_pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_address_viewset_delete_blocked(self):
        assert not hasattr(CustomerAddressViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerAddressViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customers/123/addresses/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, customer_pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_identification_viewset_delete_blocked(self):
        assert not hasattr(CustomerIdentificationViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerIdentificationViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customers/123/identifications/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, customer_pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_preference_viewset_delete_blocked(self):
        assert not hasattr(CustomerPreferenceViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPreferenceViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customers/123/preferences/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, customer_pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_preference_type_viewset_delete_blocked(self):
        assert not hasattr(CustomerPreferenceTypeViewSet, "destroy")

        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPreferenceTypeViewSet.as_view({"get": "list"})

        delete_req = factory.delete("/customer-preference-types/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestCustomerViewSetAPI:
    """Integration tests for CustomerViewSet CRUD and detail representations."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="crm_tester",
            email="tester@example.com",
            first_name="Jane",
            last_name="Tester",
        )

    def test_customer_retrieve_returns_detailed_embedded_relations(self):
        """Retrieve customer endpoint returns prefetched phones, emails, addresses, identifications, preferences."""
        customer = Customer.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            customer_type=CustomerTypeChoices.INDIVIDUAL,
        )
        CustomerPhone.objects.create(
            customer=customer,
            phone="+919876543210",
            phone_type=ContactTypeChoices.PERSONAL,
            is_primary=True,
            is_verified=True,
        )
        CustomerEmail.objects.create(
            customer=customer,
            email="ada@example.com",
            email_type=ContactTypeChoices.WORK,
            is_primary=True,
            is_verified=True,
        )
        CustomerAddress.objects.create(
            customer=customer,
            address_line_1="10 Babbage Way",
            city="London",
            country="GB",
            address_type=AddressTypeChoices.PERMANENT,
            is_primary=True,
        )
        CustomerIdentification.objects.create(
            customer=customer,
            identity_type=IdentityTypeChoices.PASSPORT,
            identity_number="P12345678",
            is_verified=True,
        )
        pref_type = CustomerPreferenceType.objects.create(
            code="lang",
            label="Language",
            data_type=PreferenceDataTypeChoices.CHOICES,
            values=["en", "es", "fr"],
            default_value="en",
        )
        CustomerPreference.objects.create(
            customer=customer,
            preference_type=pref_type,
            value="en",
        )

        view = CustomerViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/customers/{customer.id}/")
        force_authenticate(request, user=self.user)
        response = view(request, pk=str(customer.id))

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["id"] == str(customer.id)
        assert data["full_name"] == "Ada Lovelace"
        assert len(data["phones"]) == 1
        assert data["phones"][0]["phone"] == "+919876543210"
        assert len(data["emails"]) == 1
        assert data["emails"][0]["email"] == "ada@example.com"
        assert len(data["addresses"]) == 1
        assert "10 Babbage Way" in data["addresses"][0]["full_address"]
        assert len(data["identifications"]) == 1
        assert data["identifications"][0]["identity_type_display"] == "Passport"
        assert len(data["preferences"]) == 1
        assert data["preferences"][0]["preference_code"] == "lang"

    def test_customer_create_endpoint(self):
        """Create customer endpoint accepts CustomerSerializer payload and inserts record."""
        view = CustomerViewSet.as_view({"post": "create"})
        payload = {
            "first_name": "Katherine",
            "last_name": "Johnson",
            "customer_type": CustomerTypeChoices.INDIVIDUAL.value,
        }
        request = self.factory.post("/customers/", payload, format="json")
        force_authenticate(request, user=self.user)
        response = view(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Katherine"
        assert response.data["last_name"] == "Johnson"
        assert Customer.objects.filter(first_name="Katherine").exists()

    def test_customer_update_endpoint(self):
        """Update customer endpoint modifies profile fields."""
        customer = Customer.objects.create(first_name="Alan", last_name="Turing")
        view = CustomerViewSet.as_view({"put": "update"})
        payload = {
            "first_name": "Alan",
            "last_name": "Mathison-Turing",
            "customer_type": CustomerTypeChoices.INDIVIDUAL.value,
        }
        request = self.factory.put(f"/customers/{customer.id}/", payload, format="json")
        force_authenticate(request, user=self.user)
        response = view(request, pk=str(customer.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == "Mathison-Turing"
        customer.refresh_from_db()
        assert customer.last_name == "Mathison-Turing"


@pytest.mark.django_db
class TestNestedCustomerEntitiesAPI:
    """Integration tests for nested customer viewsets and set-primary actions."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="nested_tester",
            email="nested@example.com",
        )
        self.customer1 = Customer.objects.create(first_name="Cust1")
        self.customer2 = Customer.objects.create(first_name="Cust2")

    def test_nested_phones_list_isolated_per_customer(self):
        """GET /customers/{customer_pk}/phones/ lists only phones belonging to specified customer."""
        phone1 = CustomerPhone.objects.create(
            customer=self.customer1,
            phone="+919876543210",
            is_primary=True,
        )
        CustomerPhone.objects.create(
            customer=self.customer2,
            phone="+919123456789",
            is_primary=True,
        )

        view = CustomerPhoneViewSet.as_view({"get": "list"})
        request = self.factory.get(f"/customers/{self.customer1.id}/phones/")
        force_authenticate(request, user=self.user)
        response = view(request, customer_pk=str(self.customer1.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(phone1.id)

    def test_phone_set_primary_action(self):
        """POST /customers/{customer_pk}/phones/{pk}/set-primary/ toggles primary phone."""
        phone1 = CustomerPhone.objects.create(
            customer=self.customer1,
            phone="+919876543210",
            is_primary=True,
        )
        phone2 = CustomerPhone.objects.create(
            customer=self.customer1,
            phone="+919123456780",
            is_primary=False,
        )

        view = CustomerPhoneViewSet.as_view({"post": "set_primary"})
        request = self.factory.post(
            f"/customers/{self.customer1.id}/phones/{phone2.id}/set-primary/"
        )
        force_authenticate(request, user=self.user)
        response = view(request, customer_pk=str(self.customer1.id), pk=str(phone2.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_primary"] is True
        phone1.refresh_from_db()
        phone2.refresh_from_db()
        assert phone2.is_primary is True
        assert phone1.is_primary is False

    def test_email_set_primary_action(self):
        """POST /customers/{customer_pk}/emails/{pk}/set-primary/ toggles primary email."""
        email1 = CustomerEmail.objects.create(
            customer=self.customer1,
            email="primary@example.com",
            is_primary=True,
        )
        email2 = CustomerEmail.objects.create(
            customer=self.customer1,
            email="secondary@example.com",
            is_primary=False,
        )

        view = CustomerEmailViewSet.as_view({"post": "set_primary"})
        request = self.factory.post(
            f"/customers/{self.customer1.id}/emails/{email2.id}/set-primary/"
        )
        force_authenticate(request, user=self.user)
        response = view(request, customer_pk=str(self.customer1.id), pk=str(email2.id))

        assert response.status_code == status.HTTP_200_OK
        email1.refresh_from_db()
        email2.refresh_from_db()
        assert email2.is_primary is True
        assert email1.is_primary is False

    def test_address_set_primary_action(self):
        """POST /customers/{customer_pk}/addresses/{pk}/set-primary/ toggles primary address."""
        addr1 = CustomerAddress.objects.create(
            customer=self.customer1,
            address_line_1="Home",
            is_primary=True,
        )
        addr2 = CustomerAddress.objects.create(
            customer=self.customer1,
            address_line_1="Work",
            is_primary=False,
        )

        view = CustomerAddressViewSet.as_view({"post": "set_primary"})
        request = self.factory.post(
            f"/customers/{self.customer1.id}/addresses/{addr2.id}/set-primary/"
        )
        force_authenticate(request, user=self.user)
        response = view(request, customer_pk=str(self.customer1.id), pk=str(addr2.id))

        assert response.status_code == status.HTTP_200_OK
        addr1.refresh_from_db()
        addr2.refresh_from_db()
        assert addr2.is_primary is True
        assert addr1.is_primary is False


@pytest.mark.django_db
class TestCustomerPreferenceTypeViewSetAPI:
    """Integration tests for standalone preference types catalog endpoints."""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="pref_type_tester",
            email="pref_type@example.com",
        )

    def test_list_preference_types(self):
        """Preference types can be listed via top-level catalog endpoint and create is disallowed."""
        assert not hasattr(CustomerPreferenceTypeViewSet, "create")

        CustomerPreferenceType.objects.create(
            code="theme_mode",
            label="Theme Mode",
            data_type=PreferenceDataTypeChoices.CHOICES.value,
            values=["light", "dark"],
            default_value="light",
        )

        view_list = CustomerPreferenceTypeViewSet.as_view({"get": "list"})
        request_list = self.factory.get("/customer-preference-types/")
        force_authenticate(request_list, user=self.user)
        response_list = view_list(request_list)

        assert response_list.status_code == status.HTTP_200_OK
        assert len(response_list.data) >= 1
        assert response_list.data[0]["code"] == "theme_mode"
