from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

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
    CustomerAddressSerializer,
    CustomerEmailSerializer,
    CustomerIdentificationSerializer,
    CustomerPhoneSerializer,
    CustomerPreferenceSerializer,
    CustomerPreferenceTypeSerializer,
    CustomerSerializer,
)

Customer = get_customer_model()
CustomerAddress = get_customer_address_model()
CustomerEmail = get_customer_email_model()
CustomerIdentification = get_customer_identification_model()
CustomerPhone = get_customer_phone_model()
CustomerPreference = get_customer_preference_model()
CustomerPreferenceType = get_customer_preference_type_model()


class BaseCustomerEntityViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for customer entity endpoints.
    Disallows listing all records and deleting records via API.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "put"]

    def list(self, request, *args, **kwargs):
        """Block list operation across customers."""
        raise MethodNotAllowed(
            method="GET", detail="List operation is not allowed on this endpoint."
        )

    def destroy(self, request, *args, **kwargs):
        """Block delete operation on customer records."""
        raise MethodNotAllowed(
            method="DELETE", detail="Delete operation is not allowed on this endpoint."
        )


class CustomerViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing Customer records.
    """

    queryset = Customer.available_objects.all()
    serializer_class = CustomerSerializer


class CustomerPhoneViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerPhone records.
    """

    queryset = CustomerPhone.available_objects.all()
    serializer_class = CustomerPhoneSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this phone number as primary for its customer."""
        phone = self.get_object()
        CustomerPhone.objects.set_primary(phone)
        serializer = self.get_serializer(phone)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerEmailViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerEmail records.
    """

    queryset = CustomerEmail.available_objects.all()
    serializer_class = CustomerEmailSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this email address as primary for its customer."""
        email = self.get_object()
        CustomerEmail.objects.set_primary(email)
        serializer = self.get_serializer(email)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerAddressViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerAddress records.
    """

    queryset = CustomerAddress.available_objects.all()
    serializer_class = CustomerAddressSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this address as primary for its customer."""
        address = self.get_object()
        CustomerAddress.objects.set_primary(address)
        serializer = self.get_serializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerIdentificationViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerIdentification records.
    """

    queryset = CustomerIdentification.available_objects.all()
    serializer_class = CustomerIdentificationSerializer


class CustomerPreferenceTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CustomerPreferenceType definitions.
    """

    queryset = CustomerPreferenceType.available_objects.all()
    serializer_class = CustomerPreferenceTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "put"]

    def destroy(self, request, *args, **kwargs):
        """Block delete operation on preference type definitions."""
        raise MethodNotAllowed(
            method="DELETE", detail="Delete operation is not allowed on this endpoint."
        )


class CustomerPreferenceViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerPreference entries.
    """

    queryset = CustomerPreference.available_objects.all()
    serializer_class = CustomerPreferenceSerializer
