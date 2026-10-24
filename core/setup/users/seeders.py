"""
Development mock seeders for Users app.
"""

import os

from django.conf import settings

from core.apps.users import get_user_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class DevUserSeeder(BaseSeeder):
    class Meta(BaseMeta):
        model = get_user_model()
        object_create_method = get_user_model().objects.get_or_create_user
        fields = [
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "create_superuser",  # custom field
        ]
        execution_order = 1
        data_source = FileDataSource(
            os.path.join(settings.CORE_BASE_DIR, "setup/users/dev_users/users.json")
        )

    def to_internal_values(self, data):
        self.context.update({"create_superuser": data.pop("create_superuser", False)})
        return super().to_internal_values(data)

    def create(self, data):
        # For superusers override the original create_user
        if self.context.get("create_superuser", False):
            self.creation_method = get_user_model().objects.get_or_create_superuser

        instance = super().create(data)

        # Before exiting restore original method, as one seeder object is shared by mutiple runs
        self.creation_method = getattr(self._meta, "object_create_method")
        return instance
