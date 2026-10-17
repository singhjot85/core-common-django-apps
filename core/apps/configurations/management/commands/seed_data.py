from core.apps.configurations.management.commands.dev_setup import (
    Command as DevSetupCommand,
)


class Command(DevSetupCommand):
    help = "Alias for dev_setup command to run development seeders."
