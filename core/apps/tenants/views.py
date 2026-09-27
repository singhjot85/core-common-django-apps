from rest_framework import viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from core.apps.tenants.models import TenantBranding
from core.apps.tenants.serializers import TenantBrandingSerializer


class TenantBrandingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset for managing TenantBranding objects.
    """

    queryset = TenantBranding.available_objects.all()
    serializer_class = TenantBrandingSerializer

    permission_classes = [IsAuthenticatedOrReadOnly]

    lookup_field = "tenant__label"
    lookup_url_kwarg = "tenant_name"

    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed("list not allowed on endpoint.")
