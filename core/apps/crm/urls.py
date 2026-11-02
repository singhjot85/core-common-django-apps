"""
URL configuration for the CRM application.

Registers top-level customer and customer-preference-type endpoints, as well as
nested resources for customer contact details, addresses, KYC identifications, and preferences.
"""

from core.apps.crm.api.views import (
    CustomerAddressViewSet,
    CustomerEmailViewSet,
    CustomerIdentificationViewSet,
    CustomerPhoneViewSet,
    CustomerPreferenceTypeViewSet,
    CustomerPreferenceViewSet,
    CustomerViewSet,
)
from core.utils.routers import get_api_router_instance, get_nested_api_router_instance

base_crm_router = get_api_router_instance()
base_crm_router.register(r"customers", CustomerViewSet, basename="customer")
base_crm_router.register(
    r"customer-preference-types",
    CustomerPreferenceTypeViewSet,
    basename="customer-preference-type",
)

crm_router = get_nested_api_router_instance(
    base_crm_router, r"customers", lookup="customer"
)
crm_router.register(r"phones", CustomerPhoneViewSet, basename="phones")
crm_router.register(r"emails", CustomerEmailViewSet, basename="emails")
crm_router.register(r"addresses", CustomerAddressViewSet, basename="addresses")
crm_router.register(
    r"identifications", CustomerIdentificationViewSet, basename="identifications"
)
crm_router.register(r"preferences", CustomerPreferenceViewSet, basename="preferences")

urlpatterns = [*base_crm_router.urls, *crm_router.urls]
