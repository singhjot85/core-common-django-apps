from core.apps.tenants.views import TenantBrandingViewSet
from core.utils.routers import get_api_router_instance

tenants_router = get_api_router_instance()

tenants_router.register(r"branding", TenantBrandingViewSet, "branding")
