from core.config.settings.base import *  # noqa: F401

WSGI_APPLICATION = "sample_project.config.wsgi.application"

ROOT_URLCONF = "sample_project.config.urls"
PUBLIC_SCHEMA_URLCONF = "sample_project.config.public_urls"

MIGRATION_MODULES = {
    app.rsplit(".", 1)[-1]: f'{PROJECT_MIGRATION_PATH}.{app.rsplit(".", 1)[-1]}'
    for app in PROJECT_APPS
}
