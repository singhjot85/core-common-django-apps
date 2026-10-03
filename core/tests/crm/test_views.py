from unittest.mock import MagicMock

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
    """Unit tests ensuring list and delete methods are blocked on customer viewsets."""

    def _get_auth_user(self):
        user = MagicMock()
        user.is_authenticated = True
        return user

    def test_customer_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerViewSet.as_view({"get": "list", "delete": "destroy"})

        list_request = factory.get("/customers/")
        response = view(list_request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_request = factory.delete("/customers/123/")
        force_authenticate(delete_request, user=user)
        response = view(delete_request, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_phone_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPhoneViewSet.as_view({"get": "list", "delete": "destroy"})

        response = view(factory.get("/customer-phones/"))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_req = factory.delete("/customer-phones/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_email_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerEmailViewSet.as_view({"get": "list", "delete": "destroy"})

        response = view(factory.get("/customer-emails/"))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_req = factory.delete("/customer-emails/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_address_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerAddressViewSet.as_view({"get": "list", "delete": "destroy"})

        response = view(factory.get("/customer-addresses/"))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_req = factory.delete("/customer-addresses/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_identification_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerIdentificationViewSet.as_view(
            {"get": "list", "delete": "destroy"}
        )

        response = view(factory.get("/customer-identifications/"))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_req = factory.delete("/customer-identifications/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_customer_preference_viewset_list_and_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPreferenceViewSet.as_view({"get": "list", "delete": "destroy"})

        response = view(factory.get("/customer-preferences/"))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        delete_req = factory.delete("/customer-preferences/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_preference_type_viewset_delete_blocked(self):
        factory = APIRequestFactory()
        user = self._get_auth_user()
        view = CustomerPreferenceTypeViewSet.as_view({"delete": "destroy"})

        delete_req = factory.delete("/customer-preference-types/123/")
        force_authenticate(delete_req, user=user)
        response = view(delete_req, pk="123")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
