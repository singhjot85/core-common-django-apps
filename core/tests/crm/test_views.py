from types import SimpleNamespace

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from core.apps.crm.api.views import (
    CustomerAddressViewSet,
    CustomerEmailViewSet,
    CustomerIdentificationViewSet,
    CustomerPhoneViewSet,
    CustomerPreferenceTypeViewSet,
    CustomerPreferenceViewSet,
    CustomerViewSet,
)


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
