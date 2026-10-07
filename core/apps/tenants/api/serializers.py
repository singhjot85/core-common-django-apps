from rest_framework import serializers

from core.apps.tenants import (
    get_domain_model,
    get_tenant_branding_model,
    get_tenant_contact_info_model,
    get_tenant_model,
)
from core.utils.serializers import ReadOnlyModelSerializer

Tenant = get_tenant_model()
Domain = get_domain_model()
TenantContactInfo = get_tenant_contact_info_model()
TenantBranding = get_tenant_branding_model()


class TenantContactInfoSerializer(ReadOnlyModelSerializer):

    class Meta:
        model = TenantContactInfo
        fields = ["order", "contact_type", "tenant", "contact_info"]


class TenantDomainSerializer(ReadOnlyModelSerializer):

    class Meta:
        model = Domain
        fields = ("label", "domain", "is_primary")


class TenantSerializer(ReadOnlyModelSerializer):

    tenant_contact = TenantContactInfoSerializer(
        many=True, read_only=True, required=False, source="contact_info"
    )
    primary_domain = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ["label", "is_active", "public_id", "tenant_contact", "primary_domain"]

    def get_primary_domain(self, instance):
        """
        Get primary domain
        """
        domain = instance.domains.filter(is_primary=True).first()
        if domain:
            return TenantDomainSerializer(domain).data
        return None


class TenantBrandingSerializer(ReadOnlyModelSerializer):

    tenant = TenantSerializer(read_only=True, required=False)

    class Meta:
        model = TenantBranding
        fields = ["tenant", "details"]
