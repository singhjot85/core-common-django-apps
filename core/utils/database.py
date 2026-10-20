from contextlib import ContextDecorator

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connection, connections


def get_public_schema_name() -> str:
    """
    Get the public schema name from settings or default to 'public'.
    """
    return getattr(settings, "PUBLIC_SCHEMA_NAME", "public")


class core_schema_context(ContextDecorator):
    def __init__(self, *args, **kwargs):
        self.schema_name = args[0] or get_public_schema_name()
        self.database = kwargs.get(
            "database", getattr(settings, "TENANT_DB_ALIAS", DEFAULT_DB_ALIAS)
        )
        super().__init__()

    def __enter__(self):
        self.connection = connections[self.database]
        self.previous_tenant = connection.tenant
        self.connection.set_schema(self.schema_name)

    def __exit__(self, *exc):
        if self.previous_tenant is None:
            self.connection.set_schema_to_public()
        else:
            self.connection.set_tenant(self.previous_tenant)
