from core.apps.invoices.api.views import (
    BillingOrganizationViewSet,
    InvoiceAddressViewSet,
    InvoiceItemEntryViewSet,
    InvoiceItemFeeViewSet,
    InvoiceItemViewSet,
    InvoicePartyCategoryViewSet,
    InvoicePartyEmailViewSet,
    InvoicePartyPhoneViewSet,
    InvoicePartyViewSet,
    InvoiceTemplateViewSet,
    InvoiceViewSet,
    OrganizationAssetsViewSet,
    OrganizationEmailViewSet,
    OrganizationFinancialsViewSet,
    OrganizationPhoneViewSet,
)
from core.utils.routers import get_api_router_instance

invoices_router = get_api_router_instance()

invoices_router.register(r"invoices", InvoiceViewSet, basename="invoice")
invoices_router.register(
    r"invoice-addresses", InvoiceAddressViewSet, basename="invoice-address"
)
invoices_router.register(
    r"invoice-templates", InvoiceTemplateViewSet, basename="invoice-template"
)
invoices_router.register(
    r"billing-organizations",
    BillingOrganizationViewSet,
    basename="billing-organization",
)
invoices_router.register(
    r"organization-emails", OrganizationEmailViewSet, basename="organization-email"
)
invoices_router.register(
    r"organization-phones", OrganizationPhoneViewSet, basename="organization-phone"
)
invoices_router.register(
    r"organization-financials",
    OrganizationFinancialsViewSet,
    basename="organization-financials",
)
invoices_router.register(
    r"organization-assets", OrganizationAssetsViewSet, basename="organization-assets"
)
invoices_router.register(
    r"invoice-parties", InvoicePartyViewSet, basename="invoice-party"
)
invoices_router.register(
    r"invoice-party-categories",
    InvoicePartyCategoryViewSet,
    basename="invoice-party-category",
)
invoices_router.register(
    r"invoice-party-emails",
    InvoicePartyEmailViewSet,
    basename="invoice-party-email",
)
invoices_router.register(
    r"invoice-party-phones",
    InvoicePartyPhoneViewSet,
    basename="invoice-party-phone",
)
invoices_router.register(r"invoice-items", InvoiceItemViewSet, basename="invoice-item")
invoices_router.register(
    r"invoice-item-entries",
    InvoiceItemEntryViewSet,
    basename="invoice-item-entry",
)
invoices_router.register(
    r"invoice-item-fees", InvoiceItemFeeViewSet, basename="invoice-item-fee"
)

urlpatterns = invoices_router.urls
