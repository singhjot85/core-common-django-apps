from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from core.apps.invoices.api.serializers import (
    BillingOrganizationSerializer,
    InvoiceAddressSerializer,
    InvoiceItemEntrySerializer,
    InvoiceItemFeeSerializer,
    InvoiceItemSerializer,
    InvoicePartyCategorySerializer,
    InvoicePartyEmailSerializer,
    InvoicePartyPhoneSerializer,
    InvoicePartySerializer,
    InvoiceSerializer,
    InvoiceTemplateSerializer,
    OrganizationAssetsSerializer,
    OrganizationEmailSerializer,
    OrganizationFinancialsSerializer,
    OrganizationPhoneSerializer,
)
from core.apps.invoices.models import (
    BillingOrganization,
    Invoice,
    InvoiceAddress,
    InvoiceItem,
    InvoiceItemEntry,
    InvoiceItemFee,
    InvoiceParty,
    InvoicePartyCategory,
    InvoicePartyEmail,
    InvoicePartyPhone,
    InvoiceTemplate,
    OrganizationAssets,
    OrganizationEmail,
    OrganizationFinancials,
    OrganizationPhone,
)


class BaseInvoiceResourceViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for invoice configuration and resource endpoints.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "put", "patch"]

    def destroy(self, request, *args, **kwargs):
        """Disallow hard delete via API, requiring soft-deletion management."""
        raise MethodNotAllowed(
            method="DELETE", detail="Delete operation is not allowed on this endpoint."
        )


class BillingOrganizationViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing Billing Organizations issuing bills.
    """

    queryset = BillingOrganization.available_objects.all()
    serializer_class = BillingOrganizationSerializer

    @action(detail=True, methods=["post"], url_path="generate-next-number")
    def generate_next_number(self, request, *args, **kwargs):
        """Generate the next sequence number for this billing organization."""
        org = self.get_object()
        invoice_number = org.generate_next_invoice_number()
        return Response(
            {
                "invoice_number": invoice_number,
                "current_sequence": org.billing_current_sequence,
            },
            status=status.HTTP_200_OK,
        )


class OrganizationEmailViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing Billing Organization emails.
    """

    queryset = OrganizationEmail.available_objects.all()
    serializer_class = OrganizationEmailSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this email as primary for the organization."""
        email_obj = self.get_object()
        email_obj.is_primary = True
        email_obj.save()
        serializer = self.get_serializer(email_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationPhoneViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing Billing Organization phone numbers.
    """

    queryset = OrganizationPhone.available_objects.all()
    serializer_class = OrganizationPhoneSerializer

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, *args, **kwargs):
        """Set this phone number as primary for the organization."""
        phone_obj = self.get_object()
        phone_obj.is_primary = True
        phone_obj.save()
        serializer = self.get_serializer(phone_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationFinancialsViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing statutory and tax data of a Billing Organization.
    """

    queryset = OrganizationFinancials.available_objects.all()
    serializer_class = OrganizationFinancialsSerializer


class OrganizationAssetsViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing logos and branding assets of a Billing Organization.
    """

    queryset = OrganizationAssets.available_objects.all()
    serializer_class = OrganizationAssetsSerializer


class InvoicePartyCategoryViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing customer classification categories.
    """

    queryset = InvoicePartyCategory.available_objects.all()
    serializer_class = InvoicePartyCategorySerializer


class InvoicePartyViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing snapshot customer/party records.
    """

    queryset = InvoiceParty.available_objects.all()
    serializer_class = InvoicePartySerializer


class InvoicePartyEmailViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing snapshotted party emails.
    """

    queryset = InvoicePartyEmail.available_objects.all()
    serializer_class = InvoicePartyEmailSerializer


class InvoicePartyPhoneViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing snapshotted party phones.
    """

    queryset = InvoicePartyPhone.available_objects.all()
    serializer_class = InvoicePartyPhoneSerializer


class InvoiceAddressViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing snapshot invoice billing and shipping addresses.
    """

    queryset = InvoiceAddress.available_objects.all()
    serializer_class = InvoiceAddressSerializer


class InvoiceTemplateViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing semantic versioned invoice HTML templates.
    """

    queryset = InvoiceTemplate.objects.all()
    serializer_class = InvoiceTemplateSerializer


class InvoiceItemViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing inventory item catalog.
    """

    queryset = InvoiceItem.available_objects.all()
    serializer_class = InvoiceItemSerializer


class InvoiceItemEntryViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing invoice line item entries.
    """

    queryset = InvoiceItemEntry.available_objects.all()
    serializer_class = InvoiceItemEntrySerializer


class InvoiceItemFeeViewSet(BaseInvoiceResourceViewSet):
    """
    ViewSet for managing taxes and fees attached to line items.
    """

    queryset = InvoiceItemFee.available_objects.all()
    serializer_class = InvoiceItemFeeSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing issued Invoices.
    Invoices are immutable snapshot records (create and read only; updates/deletions disallowed).
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post"]
    queryset = (
        Invoice.available_objects.select_related(
            "biller",
            "party",
            "billing_address",
            "shipping_address",
            "invoice_template",
        )
        .prefetch_related("item_entries__fees")
        .all()
    )
    serializer_class = InvoiceSerializer

    def destroy(self, request, *args, **kwargs):
        """Block deletion of issued invoices."""
        raise MethodNotAllowed(
            method="DELETE",
            detail="Issued invoices are immutable and cannot be deleted.",
        )
