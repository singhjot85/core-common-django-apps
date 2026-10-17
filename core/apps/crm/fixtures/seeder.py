"""
Fixture seeders for CRM application.
"""

import os

from django.conf import settings

from core.apps.crm import get_customer_preference_type_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class CustomerPreferenceTypeSeeder(BaseSeeder):
    """Production seeder for customer preference type definitions."""

    class Meta(BaseMeta):
        model = get_customer_preference_type_model()
        fields = ["code", "label", "data_type", "default_value", "values"]
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_APP_DIR,
                "crm/fixtures/customer_preference_type/preference_types.json",
            )
        )
        depends_on = []
        is_fixture = True
        related_seeders = {}
