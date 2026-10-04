from core.config.settings.test import *  # noqa: F401

TENANT_SCHEMA_NAME = "test_core"
SAMPLE_PROJECT_DIR = os.path.join(BASE_DIR, PROJECT_NAME)
SAMPLE_PROJECT_TEMPLATES_DIR = os.path.join(SAMPLE_PROJECT_DIR, "templates")

TEMPLATES[0]["DIRS"] = [
    *TEMPLATES[0]["DIRS"],
    SAMPLE_PROJECT_TEMPLATES_DIR,
]

MIGRATION_MODULES = {
    app.rsplit(".", 1)[-1]: f'{PROJECT_MIGRATION_PATH}.{app.rsplit(".", 1)[-1]}'
    for app in PROJECT_APPS
}
