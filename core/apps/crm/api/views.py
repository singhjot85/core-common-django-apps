"""
API views and viewsets for the CRM application.

Provides:
- BaseCustomerViewSet: Base viewset restricting HTTP methods and enforcing authentication.
- BaseCustomerEntityViewSet: Nested viewset mixin binding child resources to parent customer URLs.
- CustomerViewSet: Top-level endpoints for customer profiles.
- CustomerPhoneViewSet: Customer phone management endpoints with primary toggling.
- CustomerEmailViewSet: Customer email management endpoints with primary toggling.
- CustomerAddressViewSet: Customer address management endpoints with primary toggling.
- CustomerIdentificationViewSet: Customer KYC and identity document records.
- CustomerPreferenceTypeViewSet: Catalog viewset for configuring customer preference schemas.
- CustomerPreferenceViewSet: Customer preference value endpoints nested under customers.
"""

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

    Restricts HTTP methods to GET, POST, and PUT. Explicitly excludes
    list and delete actions to prevent bulk data enumeration and accidental
    destructive removals via the API.
    """

    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put"]


class BaseCustomerEntityViewSet(
    NestedViewSetMixin,
    mixins.ListModelMixin,
    BaseCustomerViewSet,
):
    """
    Base ViewSet for nested customer sub-entities.

    Combines ``NestedViewSetMixin`` with customer scoping to filter all
    queries and validate mutations against the parent customer defined
    by ``customer_pk`` in the URL path.
    """

    # Mapping for NestedViewSetMixin
    parent_lookup_kwargs = {"customer_pk": "customer_id"}


class CustomerViewSet(BaseCustomerViewSet):
    """
    ViewSet for managing top-level Customer profiles.

    Provides endpoints for creating, retrieving, and updating customer profiles.
    Optimizes queries for detail retrievals by prefetching all associated contacts,
    identifications, and preferences.
    """

    queryset = Customer.available_objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        """
        Return queryset optimized with prefetched relations for detail views.

        Returns:
            models.QuerySet: Optimized Customer queryset.
        """
        queryset = super().get_queryset()
        if self.action == "retrieve":
            return queryset.prefetch_related(
                "phones",
                "emails",
                "addresses",
                "identifications",
                "preferences__preference_type",
            )
        return queryset

    def get_serializer_class(self):
        """
        Return the serializer class matching the requested action.

        Returns:
            type[serializers.Serializer]: CustomerSerializer for mutations,
            CustomerDetailsSerializer for detail representations.
        """
        if self.action in ["create", "update"]:
            return CustomerSerializer

        return CustomerDetailsSerializer


class CustomerPhoneViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing customer phone records.

    Scoped under ``/customers/{customer_pk}/phones/``. Supports primary phone toggling.
    """

    queryset = CustomerPhone.available_objects.select_related("customer").all()
    serializer_class = CustomerPhoneSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """
        Set this phone number as primary for its customer.

        Side effects:
            - Unsets primary flag on all other phone numbers of the customer.
            - Sets ``is_primary=True`` on this phone record.

        Args:
            request (Request): Active HTTP request.

        Returns:
            Response: Serialized updated phone object with HTTP 200 OK.
        """
        phone = self.get_object()
        CustomerPhone.objects.set_primary(phone)
        serializer = self.get_serializer(phone)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerEmailViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing customer email records.

    Scoped under ``/customers/{customer_pk}/emails/``. Supports primary email toggling.
    """

    queryset = CustomerEmail.available_objects.select_related("customer").all()
    serializer_class = CustomerEmailSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """
        Set this email address as primary for its customer.

        Side effects:
            - Unsets primary flag on all other email addresses of the customer.
            - Sets ``is_primary=True`` on this email record.

        Args:
            request (Request): Active HTTP request.

        Returns:
            Response: Serialized updated email object with HTTP 200 OK.
        """
        email = self.get_object()
        CustomerEmail.objects.set_primary(email)
        serializer = self.get_serializer(email)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerAddressViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing customer physical and mailing addresses.

    Scoped under ``/customers/{customer_pk}/addresses/``. Supports primary address toggling.
    """

    queryset = CustomerAddress.available_objects.select_related("customer").all()
    serializer_class = CustomerAddressSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """
        Set this address as primary for its customer.

        Side effects:
            - Unsets primary flag on all other addresses of the customer.
            - Sets ``is_primary=True`` on this address record.

        Args:
            request (Request): Active HTTP request.

        Returns:
            Response: Serialized updated address object with HTTP 200 OK.
        """
        address = self.get_object()
        CustomerAddress.objects.set_primary(address)
        serializer = self.get_serializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerIdentificationViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing customer KYC and identity documents.

    Scoped under ``/customers/{customer_pk}/identifications/``.
    """

    queryset = CustomerIdentification.available_objects.select_related("customer").all()
    serializer_class = CustomerIdentificationSerializer


class CustomerPreferenceTypeViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing customer preference type schemas and allowed values.

    Provides a standalone catalog of preference definitions (e.g. language, notification channels).
    """

    queryset = CustomerPreferenceType.available_objects.all()
    serializer_class = CustomerPreferenceTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put"]


class CustomerPreferenceViewSet(BaseCustomerEntityViewSet):
    """
    ViewSet for managing individual customer preference settings.

    Scoped under ``/customers/{customer_pk}/preferences/``.
    """

    queryset = CustomerPreference.available_objects.select_related(
        "customer", "preference_type"
    ).all()
    serializer_class = CustomerPreferenceSerializer
