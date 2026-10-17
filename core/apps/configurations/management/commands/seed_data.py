"""
Management command alias: `seed_data` (delegates to `dev_setup`).
"""

from core.apps.configurations.management.commands.dev_setup import (
    Command as DevSetupCommand,
)


class Command(DevSetupCommand):
    """Alias for dev_setup command to run development seeders."""

    help = "Alias for dev_setup command to run development seeders."
