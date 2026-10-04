from django.contrib import admin

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


class OrganizationEmailInline(admin.TabularInline):
    """Inline admin for organization emails."""

    model = OrganizationEmail
    extra = 1
    fields = ("email", "type", "is_primary", "is_removed")


class OrganizationPhoneInline(admin.TabularInline):
    """Inline admin for organization phones."""

    model = OrganizationPhone
    extra = 1
    fields = ("phone", "type", "is_primary", "is_removed")


class OrganizationFinancialsInline(admin.StackedInline):
    """Inline admin for organization financials."""

    model = OrganizationFinancials
    extra = 0
    fields = ("aadhar", "GSTIN", "PAN", "is_removed")


class OrganizationAssetsInline(admin.TabularInline):
    """Inline admin for organization assets."""

    model = OrganizationAssets
    extra = 1
    fields = ("name", "asset_type", "asset", "description", "is_removed")


@admin.register(BillingOrganization)
class BillingOrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for BillingOrganization."""

    list_display = (
        "organization_name",
        "billing_suffix",
        "billing_start_sequence",
        "billing_current_sequence",
        "created",
        "is_removed",
    )
    search_fields = ("organization_name", "billing_suffix")
    list_filter = ("is_removed", "created")
    inlines = [
        OrganizationEmailInline,
        OrganizationPhoneInline,
        OrganizationFinancialsInline,
        OrganizationAssetsInline,
    ]


class InvoicePartyEmailInline(admin.TabularInline):
    """Inline admin for invoice party email snapshots."""

    model = InvoicePartyEmail
    extra = 1
    fields = ("email", "email_type", "is_removed")


class InvoicePartyPhoneInline(admin.TabularInline):
    """Inline admin for invoice party phone snapshots."""

    model = InvoicePartyPhone
    extra = 1
    fields = ("phone", "phone_type", "is_removed")


@admin.register(InvoiceParty)
class InvoicePartyAdmin(admin.ModelAdmin):
    """Admin configuration for InvoiceParty."""

    list_display = (
        "full_name",
        "business_name",
        "party_type",
        "party_category",
        "pending_balance",
        "created",
        "is_removed",
    )
    search_fields = ("first_name", "last_name", "business_name")
    list_filter = ("party_type", "party_category", "is_removed", "created")
    inlines = [InvoicePartyEmailInline, InvoicePartyPhoneInline]


@admin.register(InvoicePartyCategory)
class InvoicePartyCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for InvoicePartyCategory."""

    list_display = ("category_name", "description", "created", "is_removed")
    search_fields = ("category_name",)
    list_filter = ("is_removed",)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Admin configuration for InvoiceItem catalog."""

    list_display = (
        "name",
        "price",
        "HSN_code",
        "current_stock",
        "is_active",
        "is_removed",
    )
    search_fields = ("name", "HSN_code")
    list_filter = ("is_active", "is_removed")


class InvoiceItemFeeInline(admin.TabularInline):
    """Inline admin for fee/tax entries on line items."""

    model = InvoiceItemFee
    extra = 1
    fields = ("rate", "description", "auto_applied", "is_removed")


class InvoiceItemEntryInline(admin.StackedInline):
    """Inline admin for line item entries on an invoice."""

    model = InvoiceItemEntry
    extra = 1
    fields = (
        "item",
        "item_name",
        "HSN_code",
        "price",
        "quantity",
        "is_removed",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin configuration for Invoice."""

    list_display = (
        "invoice_number",
        "invoice_date",
        "party",
        "biller",
        "subtotal",
        "total_fees",
        "grand_total",
        "created",
        "is_removed",
    )
    search_fields = (
        "invoice_number",
        "party__business_name",
        "party__first_name",
        "party__last_name",
    )
    list_filter = ("invoice_date", "biller", "is_removed", "created")
    inlines = [InvoiceItemEntryInline]


@admin.register(InvoiceAddress)
class InvoiceAddressAdmin(admin.ModelAdmin):
    """Admin configuration for InvoiceAddress snapshots."""

    list_display = (
        "full_address",
        "city",
        "state",
        "postal_code",
        "country",
        "is_removed",
    )
    search_fields = ("address_line_1", "city", "state", "postal_code")
    list_filter = ("country", "state", "is_removed")


@admin.register(InvoiceTemplate)
class InvoiceTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for InvoiceTemplate."""

    list_display = ("name", "version", "created", "modified")
    search_fields = ("name", "version")
