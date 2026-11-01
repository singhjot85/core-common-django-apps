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

crm_router = get_nested_api_router_instance(base_crm_router)
crm_router.register(r"phones", CustomerPhoneViewSet, basename="phones")
crm_router.register(r"emails", CustomerEmailViewSet, basename="emails")
crm_router.register(r"addresses", CustomerAddressViewSet, basename="addresses")
crm_router.register(
    r"identifications", CustomerIdentificationViewSet, basename="identifications"
)
crm_router.register(
    r"preference-types", CustomerPreferenceTypeViewSet, basename="preference-types"
)
crm_router.register(r"preferences", CustomerPreferenceViewSet, basename="preferences")

urlpatterns = [*base_crm_router, *crm_router.urls]
