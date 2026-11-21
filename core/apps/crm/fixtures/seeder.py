"""
Fixture seeders for CRM application.
"""

from __future__ import annotations

import os

from django.conf import settings

from core.apps.crm import get_customer_preference_type_model
from core.libraries.seeder import BaseSeeder, FileBasedLoader, GetorCreateObject

PreferenceType = get_customer_preference_type_model()


class CustomerPreferenceTypeSeeder(BaseSeeder):
    """Production seeder for customer preference type definitions."""

    is_fixture: bool = True
    tenant_type: str = getattr(settings, "TENANT_TYPE_ORGANIZATION", "organization")

    loader = FileBasedLoader(
        directory_name=os.path.join(
            settings.CORE_APP_DIR,
            "crm/fixtures/customer_preference_type",
        ),
        load_method=FileBasedLoader.LOAD_INDIVIDUAL,
    )
    method = GetorCreateObject(
        model=PreferenceType,
        lookup_fields=["code"],
        default_fields=["label", "data_type", "default_value", "values"],
    )
