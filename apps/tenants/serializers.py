from apps.tenants.models import TenantBranding, TenantContactInfo, Tenants
from utils.serializers import ReadOnlyModelSerializer


class TenantContactInfoSerializer(ReadOnlyModelSerializer):

    class Meta:
        model = TenantContactInfo
        fields = ["order", "contact_type", "tenant", "value"]


class TenantSerializer(ReadOnlyModelSerializer):

    tenant_contact = TenantContactInfoSerializer(
        many=True, read_only=True, required=False, source="contact_info"
    )

    class Meta:
        model = Tenants
        fields = ["label", "is_active", "public_id", "tenant_contact"]


class TenantBrandingSerializer(ReadOnlyModelSerializer):

    tenant = TenantSerializer(read_only=True, required=False)

    class Meta:
        model = TenantBranding
        fields = ["tenant", "details"]
