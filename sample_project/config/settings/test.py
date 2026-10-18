from core.config.settings.test import *  # noqa: F401

TENANT_SCHEMA_NAME = "test_core"

MIGRATION_MODULES = {
    app.rsplit(".", 1)[-1]: f'{PROJECT_MIGRATION_PATH}.{app.rsplit(".", 1)[-1]}'
    for app in PROJECT_APPS
}
