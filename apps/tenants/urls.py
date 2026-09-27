from tenants.views import TenantBrandingViewSet

from utils.routers import get_api_router_instance

tenants_router = get_api_router_instance()

tenants_router.register(r"branding", TenantBrandingViewSet, "branding")
