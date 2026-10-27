from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.apps.users"
    label = "users"
    verbose_name = "User Management & Authentication"

    def ready(self):
        from core.apps.users.signals import create_system_user_callback  # noqa: PLC0415

        post_migrate.connect(create_system_user_callback, sender=self)
