from core.apps.crm.api.views import (
    CustomerAddressViewSet,
    CustomerEmailViewSet,
    CustomerIdentificationViewSet,
    CustomerPhoneViewSet,
    CustomerViewSet,
)
from core.utils.routers import get_api_router_instance

crm_router = get_api_router_instance()

crm_router.register(r"customers", CustomerViewSet, basename="customer")
crm_router.register(r"customer-phones", CustomerPhoneViewSet, basename="customer-phone")
crm_router.register(r"customer-emails", CustomerEmailViewSet, basename="customer-email")
crm_router.register(
    r"customer-addresses", CustomerAddressViewSet, basename="customer-address"
)
crm_router.register(
    r"customer-identifications",
    CustomerIdentificationViewSet,
    basename="customer-identification",
)

urlpatterns = crm_router.urls
