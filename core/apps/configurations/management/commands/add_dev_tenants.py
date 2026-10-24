"""
Management command alias: `seed_data` (delegates to `dev_setup`).
"""

import json
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.apps.configurations import app_settings
from core.apps.tenants import get_domain_model, get_tenant_model
from core.utils.checks import is_development, is_multi_tenant
from core.utils.database import get_public_schema_name

LOGGER = logging.getLogger(__name__)


def _create_tenant(schema_name: str, domain: str, **kwargs):
    if not is_multi_tenant():
        return

    Tenants = get_tenant_model()
    Domain = get_domain_model()

    tenant_label = " ".join(schema_name.split("_")).title()
    tenant, created = Tenants.objects.get_or_create(
        schema_name=schema_name,
        is_active=True,
        defaults={"label": tenant_label, **kwargs},
    )
    domain, _ = Domain.objects.get_or_create(
        tenant=tenant, defaults={"domain": domain, "label": tenant_label, **kwargs}
    )
    if created:
        return tenant


def _seed_dev_tenants():
    """
    Add tenants for local development
    """
    tenants = []

    publicdomain = getattr(settings, "BASE_URL", "localhost")
    tenant = _create_tenant(get_public_schema_name(), publicdomain)
    if tenant:
        tenants.append(tenant.label)

    # Seed multiple tenants from a given file
    setup_path = app_settings.DEV_SEEDER_SETUP_PATH
    file_path = os.path.join(settings.BASE_DIR, setup_path, "tenants", "tenants.json")
    data = None

    with open(file_path, "r") as f:
        data = json.load(f)

    if data:
        for tenant_data in data:
            tenant = _create_tenant(
                tenant_data.pop("schema_name"), tenant_data.pop("domain"), **tenant_data
            )
            if tenant:
                tenants.append(tenant.label)

    return tenants


class Command(BaseCommand):
    """Alias for dev_setup command to run development seeders."""

    help = "Alias for dev_setup command to run development seeders."

    def handle(self, *args, **options):
        if not is_development():
            raise CommandError(
                "dev_setup can only be executed in a development environment."
            )

        self.stdout.write(self.style.NOTICE("Adding tenants..."))
        try:
            tenants = None
            with transaction.atomic():
                tenants = _seed_dev_tenants()

            if not tenants:
                self.stdout.write(self.style.WARNING("No tenants were seeded !!"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully seeded tenants: {tenants}")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed Seeding tenants: {e}"))
