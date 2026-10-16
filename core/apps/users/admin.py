from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from core.apps.users import get_otp_log_model, get_social_account_model, get_user_model

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()


class SocialAccountInline(admin.TabularInline):
    """Inline view of linked social accounts for a user."""

    model = SocialAccount
    fk_name = "user"
    extra = 0
    fields = ("provider", "uid", "created")
    readonly_fields = ("created",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Admin configuration for the core User model with UUID, phone, and verification attributes.
    """

    inlines = [SocialAccountInline]
    list_display = (
        "username",
        "email",
        "phone_number",
        "full_name",
        "is_phone_verified",
        "is_email_verified",
        "is_staff",
        "is_removed",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_phone_verified",
        "is_email_verified",
        "is_removed",
    )
    search_fields = ("username", "first_name", "last_name", "email", "phone_number")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "phone_number")},
        ),
        (
            _("Verification status"),
            {"fields": ("is_phone_verified", "is_email_verified")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important dates"),
            {"fields": ("last_login", "date_joined", "created", "modified")},
        ),
        (
            _("Soft Delete Tracking"),
            {"fields": ("is_removed", "removed_by")},
        ),
    )
    readonly_fields = ("created", "modified", "date_joined", "last_login")


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """Admin configuration for third-party social account links."""

    list_display = ("id", "user", "provider", "uid", "created")
    list_filter = ("provider", "is_removed")
    search_fields = ("uid", "user__username", "user__email")
    readonly_fields = ("created", "modified")


@admin.register(OTPLog)
class OTPLogAdmin(admin.ModelAdmin):
    """Admin configuration for OTP audit logs."""

    list_display = ("id", "recipient", "channel", "purpose", "status", "created")
    list_filter = ("channel", "purpose", "status")
    search_fields = ("recipient",)
    readonly_fields = ("created", "modified", "status_changed")
