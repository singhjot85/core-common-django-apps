from core.config.settings.base import *  # noqa: F401

PROJECT_NAME = "sample_project"
PROJECT_LABEL = "Sample Project"

WSGI_APPLICATION = "sample_project.config.wsgi.application"

SAMPLE_PROJECT_DIR = os.path.join(BASE_DIR.parent, PROJECT_NAME)
SAMPLE_PROJECT_TEMPLATES_DIR = os.path.join(SAMPLE_PROJECT_DIR, "templates")

TEMPLATES[0]["DIRS"] = [
    *TEMPLATES[0]["DIRS"],
    SAMPLE_PROJECT_TEMPLATES_DIR,
]

PROJECT_MIGRATION_PATH = "db_migrations"
MIGRATION_MODULES = {
    "configurations": f"{PROJECT_MIGRATION_PATH}.configurations",
    "crm": f"{PROJECT_MIGRATION_PATH}.crm",
    "integrations": f"{PROJECT_MIGRATION_PATH}.integrations",
    "integrations_email": f"{PROJECT_MIGRATION_PATH}.integrations_email",
    "integrations_sms": f"{PROJECT_MIGRATION_PATH}.integrations_sms",
    "invoices": f"{PROJECT_MIGRATION_PATH}.invoices",
    "tenants": f"{PROJECT_MIGRATION_PATH}.tenants",
    "users": f"{PROJECT_MIGRATION_PATH}.users",
}
