from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_nested.viewsets import NestedViewSetMixin

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
    CustomerDetailsSerializer,
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


class BaseCustomerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Base ViewSet for customer entity endpoints.
    Disallows listing all records and deleting records via API.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put"]


class BaseCustomerEntityViewSet(
    NestedViewSetMixin,
    mixins.ListModelMixin,
    BaseCustomerViewSet,
):
    """ """

    # Mapping for NestedViewSetMixin
    parent_lookup_kwargs = {"customer_pk": "customer_id"}


class CustomerViewSet(BaseCustomerViewSet):
    """
    ViewSet for managing Customer records.
    """

    queryset = Customer.available_objects.all()
    serializer_class = CustomerSerializer

    def get_serializer_class(self):
        """ """
        if self.action in ["create", "update"]:
            return CustomerSerializer

        return CustomerDetailsSerializer


class CustomerPhoneViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerPhone records.
    """

    queryset = CustomerPhone.available_objects.select_related("customer").all()
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

    queryset = CustomerEmail.available_objects.select_related("customer").all()
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

    queryset = CustomerAddress.available_objects.select_related("customer").all()
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

    queryset = CustomerIdentification.available_objects.select_related("customer").all()
    serializer_class = CustomerIdentificationSerializer


class CustomerPreferenceTypeViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerPreferenceType definitions.
    """

    queryset = CustomerPreferenceType.available_objects.all()
    serializer_class = CustomerPreferenceTypeSerializer
    http_method_names = ["get", "post", "put"]


class CustomerPreferenceViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing CustomerPreference entries.
    """

    queryset = CustomerPreference.available_objects.all()
    serializer_class = CustomerPreferenceSerializer
