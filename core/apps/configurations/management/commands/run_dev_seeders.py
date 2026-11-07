"""
Management command to run development seeders and bootstrap local setup.
"""

from __future__ import annotations

import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.apps.configurations import app_settings
from core.seeder.runners import SeedDevelopmentData
from core.utils.autodiscovery import AutoDiscovery
from core.utils.checks import is_development

LOGGER = logging.getLogger(__name__)


def _autodiscover(setup_path) -> list:
    """
    Discover and import all seeder modules across development setup and core apps.

    Uses `app_settings.DEV_SEEDER_SETUP_PATH` (anchored to `settings.CORE_BASE_DIR`)
    for development seeders, and `settings.CORE_APP_DIR` for production app fixtures.

    Returns:
        list: List of discovered and imported module objects.
    """
    discovered = []

    dev_discovery = AutoDiscovery(
        root_path=setup_path,
        scan_all=True,
        scan_depth=4,
        file_name=["seeder.py", "seeders.py"],
    )
    discovered.extend(dev_discovery.autodiscover())

    # 2. Discover production fixture seeders under CORE_APP_DIR
    fixtures_discovery = AutoDiscovery(
        root_path=settings.CORE_APP_DIR,
        scan_all=True,
        scan_depth=2,
        file_name=["seeder.py", "seeders.py"],
    )
    discovered.extend(fixtures_discovery.autodiscover())

    return discovered


def auto_discover_seeders():
    # 1. Discover development seeders from configured setup path
    setup_path = os.path.join(settings.BASE_DIR, app_settings.DEV_SEEDER_SETUP_PATH)
    discovered = _autodiscover(setup_path)

    if not discovered:
        # 2. If nothing found, load from core setup
        setup_path = os.path.join(
            settings.CORE_BASE_DIR, app_settings.DEV_SEEDER_SETUP_PATH
        )
        discovered = _autodiscover(setup_path)

    return discovered


class Command(BaseCommand):
    """
    Django management command: `dev_setup` (alias: `seed_data`).

    Discovers all registered seeders and triggers the SeedData runner
    to populate development environments with initial and mock records.
    """

    help = "Run development seeders to populate initial and development mock data."

    def handle(self, *args, **options):
        if not is_development():
            raise CommandError(
                "dev_setup can only be executed in a development environment."
            )

        self.stdout.write(self.style.NOTICE("Discovering and loading seeders..."))
        discovered = auto_discover_seeders()
        self.stdout.write(
            self.style.NOTICE(f"Discovered {len(discovered)} seeder file...")
        )

        self.stdout.write(self.style.NOTICE("Executing SeedDevelopmentData runner..."))
        runner = SeedDevelopmentData()
        instances = runner.run()

        if not instances:
            self.stdout.write(
                self.style.WARNING("Succesfull seeder run but no data seeded !!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully completed development setup and seeded data..."
                )
            )
