from django.contrib import admin

from core.apps.crm.models import (
    Customer,
    CustomerAddress,
    CustomerEmail,
    CustomerIdentification,
    CustomerPhone,
    CustomerPreference,
    CustomerPreferenceType,
)


class CustomerPhoneInline(admin.TabularInline):
    """Inline admin for customer phone numbers."""

    model = CustomerPhone
    extra = 1
    fields = ("phone", "phone_type", "is_primary", "is_verified", "is_removed")


class CustomerEmailInline(admin.TabularInline):
    """Inline admin for customer email addresses."""

    model = CustomerEmail
    extra = 1
    fields = ("email", "email_type", "is_primary", "is_verified", "is_removed")


class CustomerAddressInline(admin.StackedInline):
    """Inline admin for customer addresses."""

    model = CustomerAddress
    extra = 1
    fields = (
        "address_type",
        "is_primary",
        "address_line_1",
        "address_line_2",
        "landmark",
        "city",
        "state",
        "postal_code",
        "country",
        "latitude",
        "longitude",
        "is_removed",
    )


class CustomerIdentificationInline(admin.TabularInline):
    """Inline admin for customer KYC/identification documents."""

    model = CustomerIdentification
    extra = 1
    fields = (
        "identity_type",
        "identity_number",
        "content_type",
        "object_id",
        "issue_date",
        "expiry_date",
        "issuing_authority",
        "is_verified",
        "is_removed",
    )


class CustomerPreferenceInline(admin.TabularInline):
    """Inline admin for customer preferences."""

    model = CustomerPreference
    extra = 1
    fields = ("preference_type", "value", "is_removed")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin configuration for Customer profiles."""

    list_display = (
        "id",
        "full_name",
        "customer_type",
        "status",
        "created",
        "is_removed",
    )
    list_filter = ("customer_type", "status", "is_removed")
    search_fields = (
        "first_name",
        "middle_name",
        "last_name",
        "business_name",
        "id",
    )
    inlines = [
        CustomerPhoneInline,
        CustomerEmailInline,
        CustomerAddressInline,
        CustomerIdentificationInline,
        CustomerPreferenceInline,
    ]


@admin.register(CustomerPhone)
class CustomerPhoneAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerPhone records."""

    list_display = (
        "phone",
        "customer",
        "phone_type",
        "is_primary",
        "is_verified",
        "is_removed",
    )
    list_filter = ("phone_type", "is_primary", "is_verified", "is_removed")
    search_fields = (
        "phone",
        "customer__first_name",
        "customer__last_name",
        "customer__business_name",
    )


@admin.register(CustomerEmail)
class CustomerEmailAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerEmail records."""

    list_display = (
        "email",
        "customer",
        "email_type",
        "is_primary",
        "is_verified",
        "is_removed",
    )
    list_filter = ("email_type", "is_primary", "is_verified", "is_removed")
    search_fields = (
        "email",
        "customer__first_name",
        "customer__last_name",
        "customer__business_name",
    )


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerAddress records."""

    list_display = (
        "full_address",
        "customer",
        "address_type",
        "is_primary",
        "is_removed",
    )
    list_filter = (
        "address_type",
        "is_primary",
        "city",
        "state",
        "country",
        "is_removed",
    )
    search_fields = (
        "address_line_1",
        "city",
        "postal_code",
        "customer__first_name",
        "customer__last_name",
        "customer__business_name",
    )


@admin.register(CustomerIdentification)
class CustomerIdentificationAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerIdentification records."""

    list_display = (
        "identity_type",
        "identity_number",
        "customer",
        "is_verified",
        "is_removed",
    )
    list_filter = ("identity_type", "is_verified", "is_removed")
    search_fields = (
        "identity_number",
        "customer__first_name",
        "customer__last_name",
        "customer__business_name",
    )


@admin.register(CustomerPreferenceType)
class CustomerPreferenceTypeAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerPreferenceType definitions."""

    list_display = ("code", "label", "data_type", "default_value", "is_removed")
    list_filter = ("data_type", "is_removed")
    search_fields = ("code", "label")


@admin.register(CustomerPreference)
class CustomerPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerPreference entries."""

    list_display = ("customer", "preference_type", "value", "is_removed")
    list_filter = ("preference_type", "is_removed")
    search_fields = (
        "customer__first_name",
        "customer__last_name",
        "customer__business_name",
        "preference_type__code",
        "preference_type__label",
    )
