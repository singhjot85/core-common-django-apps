from rest_framework import serializers

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

# ----------------------------------------
# Organization Serializers
# ----------------------------------------


class OrganizationEmailSerializer(serializers.ModelSerializer):
    """Serializer for organization email addresses."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = OrganizationEmail
        fields = [
            "id",
            "organization",
            "email",
            "type",
            "type_display",
            "is_primary",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "type_display", "created", "modified"]


class OrganizationPhoneSerializer(serializers.ModelSerializer):
    """Serializer for organization phone numbers."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = OrganizationPhone
        fields = [
            "id",
            "organization",
            "phone",
            "type",
            "type_display",
            "is_primary",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "type_display", "created", "modified"]


class OrganizationFinancialsSerializer(serializers.ModelSerializer):
    """Serializer for statutory and tax details of a billing organization."""

    class Meta:
        model = OrganizationFinancials
        fields = [
            "id",
            "organization",
            "aadhar",
            "GSTIN",
            "PAN",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class OrganizationAssetsSerializer(serializers.ModelSerializer):
    """Serializer for organization branding assets (logos, signatures, etc.)."""

    asset_type_display = serializers.CharField(
        source="get_asset_type_display", read_only=True
    )

    class Meta:
        model = OrganizationAssets
        fields = [
            "id",
            "billing_org",
            "asset",
            "name",
            "asset_type",
            "asset_type_display",
            "description",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "asset_type_display", "created", "modified"]


class BillingOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for billing organization profiles with nested contact channels and assets."""

    emails = OrganizationEmailSerializer(many=True, read_only=True)
    phones = OrganizationPhoneSerializer(many=True, read_only=True)
    financial_data = OrganizationFinancialsSerializer(read_only=True)
    assets = OrganizationAssetsSerializer(many=True, read_only=True)

    class Meta:
        model = BillingOrganization
        fields = [
            "id",
            "organization_name",
            "billing_suffix",
            "billing_start_sequence",
            "billing_current_sequence",
            "emails",
            "phones",
            "financial_data",
            "assets",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "billing_current_sequence",
            "emails",
            "phones",
            "financial_data",
            "assets",
            "created",
            "modified",
        ]


# ----------------------------------------
# Party Serializers
# ----------------------------------------


class InvoicePartyCategorySerializer(serializers.ModelSerializer):
    """Serializer for invoice party categories."""

    class Meta:
        model = InvoicePartyCategory
        fields = ["id", "category_name", "description", "created", "modified"]
        read_only_fields = ["id", "created", "modified"]


class InvoicePartyEmailSerializer(serializers.ModelSerializer):
    """Serializer for invoice party email snapshots."""

    email_type_display = serializers.CharField(
        source="get_email_type_display", read_only=True
    )

    class Meta:
        model = InvoicePartyEmail
        fields = [
            "id",
            "invoice_party",
            "email",
            "email_type",
            "email_type_display",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "email_type_display", "created", "modified"]


class InvoicePartyPhoneSerializer(serializers.ModelSerializer):
    """Serializer for invoice party phone snapshots."""

    phone_type_display = serializers.CharField(
        source="get_phone_type_display", read_only=True
    )

    class Meta:
        model = InvoicePartyPhone
        fields = [
            "id",
            "invoice_party",
            "phone",
            "phone_type",
            "phone_type_display",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "phone_type_display", "created", "modified"]


class InvoicePartySerializer(serializers.ModelSerializer):
    """Serializer for invoiced party snapshots with nested contacts."""

    full_name = serializers.CharField(read_only=True)
    party_type_display = serializers.CharField(
        source="get_party_type_display", read_only=True
    )
    emails = InvoicePartyEmailSerializer(many=True, read_only=True)
    phones = InvoicePartyPhoneSerializer(many=True, read_only=True)

    class Meta:
        model = InvoiceParty
        fields = [
            "id",
            "suffix",
            "first_name",
            "middle_name",
            "last_name",
            "business_name",
            "full_name",
            "customer",
            "party_type",
            "party_type_display",
            "party_category",
            "pending_balance",
            "emails",
            "phones",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "full_name",
            "party_type_display",
            "emails",
            "phones",
            "created",
            "modified",
        ]


# ----------------------------------------
# Address & Template Serializers
# ----------------------------------------


class InvoiceAddressSerializer(serializers.ModelSerializer):
    """Serializer for invoice address snapshots."""

    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = InvoiceAddress
        fields = [
            "id",
            "address_line_1",
            "address_line_2",
            "landmark",
            "city",
            "state",
            "postal_code",
            "country",
            "full_address",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "full_address", "created", "modified"]


class InvoiceTemplateSerializer(serializers.ModelSerializer):
    """Serializer for invoice template definitions."""

    class Meta:
        model = InvoiceTemplate
        fields = [
            "id",
            "name",
            "html_template",
            "version_major",
            "version_minor",
            "version_patch",
            "version",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "version", "created", "modified"]


# ----------------------------------------
# Catalog & Item Entry Serializers
# ----------------------------------------


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for inventory-maintained item catalog."""

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "discount_options",
            "HSN_code",
            "current_stock",
            "is_active",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "created", "modified"]


class InvoiceItemFeeSerializer(serializers.ModelSerializer):
    """Serializer for line item fees and taxes."""

    fee_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = InvoiceItemFee
        fields = [
            "id",
            "item_entry",
            "rate",
            "description",
            "auto_applied",
            "fee_amount",
            "created",
            "modified",
        ]
        read_only_fields = ["id", "fee_amount", "created", "modified"]


class InvoiceItemEntrySerializer(serializers.ModelSerializer):
    """Serializer for invoice line item entries with nested fees/taxes."""

    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    total_fee_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    grand_total = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    fees = InvoiceItemFeeSerializer(many=True, read_only=True)

    class Meta:
        model = InvoiceItemEntry
        fields = [
            "id",
            "invoice",
            "item",
            "item_name",
            "item_description",
            "HSN_code",
            "price",
            "quantity",
            "total_price",
            "total_fee_amount",
            "grand_total",
            "fees",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "total_price",
            "total_fee_amount",
            "grand_total",
            "fees",
            "created",
            "modified",
        ]


# ----------------------------------------
# Root Invoice Serializers
# ----------------------------------------


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for root Invoice instances with calculated totals and line entries."""

    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_fees = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    grand_total = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    item_entries = InvoiceItemEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "invoice_date",
            "party",
            "biller",
            "billing_address",
            "shipping_address",
            "invoice_template",
            "subtotal",
            "total_fees",
            "grand_total",
            "item_entries",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "subtotal",
            "total_fees",
            "grand_total",
            "item_entries",
            "created",
            "modified",
        ]
