from core.config.settings.base import *  # noqa: F401

PROJECT_NAME = "sample_project"
PROJECT_LABEL = "Sample Project"

WSGI_APPLICATION = "sample_project.config.wsgi.application"

ROOT_URLCONF = "sample_project.config.urls"
PUBLIC_SCHEMA_URLCONF = "sample_project.config.public_urls"

SAMPLE_PROJECT_DIR = os.path.join(BASE_DIR.parent, PROJECT_NAME)
SAMPLE_PROJECT_TEMPLATES_DIR = os.path.join(SAMPLE_PROJECT_DIR, "templates")

TEMPLATES[0]["DIRS"] = [
    *TEMPLATES[0]["DIRS"],
    SAMPLE_PROJECT_TEMPLATES_DIR,
]
