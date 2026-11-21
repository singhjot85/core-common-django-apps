"""
Development mock seeders for Users app.
"""

from __future__ import annotations

from core.apps.users import get_user_model
from core.libraries.seeder import BaseSeeder, FileBasedLoader, GetorCreateObject

User = get_user_model()


class UserCreationMethod(GetorCreateObject):
    """Custom method selecting get_or_create_user vs get_or_create_superuser."""

    def perform_seed(self, prepared_fields, seeder):
        lookups, defaults, related_fields = self.split_fields(prepared_fields, seeder)
        is_superuser = defaults.pop("create_superuser", False)

        manager = self.model._default_manager
        create_fn = (
            manager.get_or_create_superuser
            if is_superuser
            else manager.get_or_create_user
        )
        instance, created = create_fn(defaults=defaults, **lookups)
        self._link_related_instances(instance, related_fields)
        return instance


class DevUserSeeder(BaseSeeder):
    """Development mock seeder for Users app."""

    execution_order: int = 1
    loader = FileBasedLoader(
        directory_name="setup/users/dev_users/users.json",
        load_method=FileBasedLoader.LOAD_COMPILED,
    )
    method = UserCreationMethod(
        model=User,
        lookup_fields=["username"],
        default_fields=[
            "password",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "create_superuser",
        ],
    )
