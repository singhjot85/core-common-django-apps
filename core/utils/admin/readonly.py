from django.contrib import admin


class ReadOnlyAdmin(admin.ModelAdmin):
    """Read Only Admin Class, a reusable admin utility that converts a admin in readonly, ex: LogModels"""

    def get_readonly_fields(self, request, obj=...):
        """Declare all the Admin fields as readonly"""
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        """Restrict Object creation from list view"""
        return False

    def has_change_permission(self, request, obj=None):
        """Restrict Object change from object view"""
        return False
