import importlib
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.seeder.runners import SeedData
from core.utils.checks import is_development

LOGGER = logging.getLogger(__name__)


def auto_discover_seeders():
    """Import all known and discoverable seeder modules to ensure registration."""
    known_modules = [
        "core.setup.crm.seeder",
        "core.setup.invoices.seeder",
        "core.setup.tenants.seeder",
    ]
    for mod_name in known_modules:
        try:
            importlib.import_module(mod_name)
        except (ImportError, ModuleNotFoundError) as exc:
            LOGGER.debug("Could not import %s: %s", mod_name, exc)

    # Dynamically scan core/apps and core/setup for additional seeder files
    core_dir = Path(__file__).resolve().parents[4]
    if core_dir.exists():
        for seeder_file in list(core_dir.glob("apps/*/fixtures/seeder.py")) + list(
            core_dir.glob("setup/*/seeder.py")
        ):
            rel_parts = seeder_file.relative_to(core_dir.parent).with_suffix("").parts
            mod_str = ".".join(rel_parts)
            if mod_str not in known_modules:
                try:
                    importlib.import_module(mod_str)
                except (ImportError, ModuleNotFoundError) as exc:
                    LOGGER.debug("Could not import %s: %s", mod_str, exc)


def load_seed_data() -> dict:
    """Load fixture and setup JSON files into a dictionary keyed by seeder labels."""
    seed_data: dict[str, list] = {}
    core_dir = Path(__file__).resolve().parents[4]
    if not core_dir.exists():
        return seed_data

    json_files = list(core_dir.glob("apps/*/fixtures/*/*.json")) + list(
        core_dir.glob("setup/*/*/*.json")
    )

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception as exc:
            LOGGER.warning("Could not load seed data from %s: %s", json_file, exc)
            continue

        dir_name = json_file.parent.name
        stem_name = json_file.stem

        keys_to_register = [
            dir_name,
            f"{dir_name}_seeder",
            stem_name,
            f"{stem_name}_seeder",
        ]
        for key in keys_to_register:
            if key not in seed_data:
                seed_data[key] = content

    return seed_data


class Command(BaseCommand):
    help = "Run development seeders to populate initial and development mock data."

    def handle(self, *args, **options):
        if not is_development():
            raise CommandError(
                "dev_setup can only be executed in a development environment."
            )

        self.stdout.write(self.style.NOTICE("Discovering and loading seeders..."))
        auto_discover_seeders()

        self.stdout.write(self.style.NOTICE("Loading seed fixture data..."))
        seed_data = load_seed_data()

        self.stdout.write(self.style.NOTICE("Executing SeedData runner..."))
        runner = SeedData(seed_data=seed_data)
        runner.run()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully completed development setup and seeded data."
            )
        )
