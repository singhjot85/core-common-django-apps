from constance.admin import Config, ConstanceAdmin
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect


class PublicAdminSite(admin.AdminSite):
    site_header = "Public Administration"
    site_title = "Public Admin"
    index_title = "Public Portal"

    def login(self, request, extra_context=None):
        """
        If user is already logged in redirect to admin index, otherwise render standard login.
        """
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(f"{self.name}:index")

        return super().login(request, extra_context=extra_context)


public_admin_site = PublicAdminSite(name="public_admin")


class TenantAdminSite(admin.AdminSite):
    site_header = "Tenant Administration"
    site_title = "Tenant Admin"
    index_title = "Tenant Portal"

    def login(self, request, extra_context=None):
        """
        If user is already logged in redirect to admin index, otherwise render standard login.
        """
        if request.user.is_authenticated and request.user.is_staff:
            return redirect(f"{self.name}:index")

        return super().login(request, extra_context=extra_context)


private_admin_site = TenantAdminSite(name="private_admin")

# =============================
#   Register Core / Third Party Admins
# =============================

public_admin_site.register([Config], ConstanceAdmin)
private_admin_site.register([Config], ConstanceAdmin)

public_admin_site.register(User, UserAdmin)
public_admin_site.register(Group, GroupAdmin)
private_admin_site.register(User, UserAdmin)
private_admin_site.register(Group, GroupAdmin)

try:
    from django_celery_results.admin import GroupResultAdmin, TaskResultAdmin
    from django_celery_results.models import GroupResult, TaskResult

    public_admin_site.register(TaskResult, TaskResultAdmin)
    public_admin_site.register(GroupResult, GroupResultAdmin)
except (ImportError, Exception):
    pass
