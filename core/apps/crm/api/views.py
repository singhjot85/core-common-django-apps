from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.apps.crm.api.serializers import (
    CustomerAddressSerializer,
    CustomerEmailSerializer,
    CustomerIdentificationSerializer,
    CustomerPhoneSerializer,
    CustomerSerializer,
)
from core.apps.crm.models import (
    Customer,
    CustomerAddress,
    CustomerEmail,
    CustomerIdentification,
    CustomerPhone,
)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Customer records.
    """

    queryset = Customer.available_objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CustomerPhoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CustomerPhone records.
    """

    queryset = CustomerPhone.available_objects.all()
    serializer_class = CustomerPhoneSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this phone number as primary for its customer."""
        phone = self.get_object()
        CustomerPhone.objects.set_primary(phone)
        serializer = self.get_serializer(phone)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerEmailViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CustomerEmail records.
    """

    queryset = CustomerEmail.available_objects.all()
    serializer_class = CustomerEmailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this email address as primary for its customer."""
        email = self.get_object()
        CustomerEmail.objects.set_primary(email)
        serializer = self.get_serializer(email)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CustomerAddress records.
    """

    queryset = CustomerAddress.available_objects.all()
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this address as primary for its customer."""
        address = self.get_object()
        CustomerAddress.objects.set_primary(address)
        serializer = self.get_serializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerIdentificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing CustomerIdentification records.
    """

    queryset = CustomerIdentification.available_objects.all()
    serializer_class = CustomerIdentificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
