# Project Profile

The profile is a JSON file (`project.profile.json`) holding every project-specific value. Scripts read it;
SKILL.md never hard-codes anything. Missing keys fall back to plain-Django defaults.

## Schema

```json
{
  "project_name": "my-backend",
  "apps_root": "core/apps",
  "nested_container_dirs": ["features", "providers"],
  "swappable_models": true,
  "base_model": "core.utils.models.BaseModel",
  "app_settings": {
    "base_class": "core.utils.app_settings.BaseSettings",
    "types_module": "core.utils.app_settings.types",
    "tiers": ["Settings", "Constance", "Configuration"],
    "import_data_type": "SettingsType.IMPORT.value",
    "settings_key_prefix": "CORE"
  },
  "admin": {
    "private_site": "core.utils.admin.private_admin_site",
    "public_site": "core.utils.admin.public_admin_site"
  },
  "tenancy": "django-tenants",
  "migrations": { "mode": "external", "root": "sample_project/db_migrations" },
  "settings_registry_file": "core/config/settings/base_models.py",
  "registry_lists": { "all": "PROJECT_APPS", "tenant": "DJANGO_TENANT_PRIVATE_APPS", "public": "DJANGO_TENANT_PUBLIC_APPS" },
  "tests_root": "core/tests",
  "commands": {
    "makemigrations": "make mm APP_LABEL={app_label}",
    "test": "make t DIR={tests_dir}",
    "lint": "poetry run pre-commit run --all-files"
  }
}
```

| Key | Meaning | Plain-Django default |
| :-- | :-- | :-- |
| `apps_root` | Directory (relative to repo root) apps live in | `apps` |
| `swappable_models` | Abstract/concrete split + `get_<model>_model()` getters | `false` |
| `base_model` | Dotted path of the project's model base class | `django.db.models.Model` |
| `app_settings` | Per-app settings engine; `null` disables | `null` |
| `admin.*_site` | Dotted path to custom admin sites; `null` => `django.contrib.admin.site` | `null` |
| `tenancy` | `null` or `"django-tenants"`; enables `--public` | `null` |
| `migrations.mode` | `in_app` (normal) or `external` (routed via `MIGRATION_MODULES`) | `in_app` |
| `settings_registry_file` | Where apps/model strings are registered; used only for printed instructions | `null` |
| `tests_root` | Where to create smoke tests; `null` skips | `null` |
| `commands` | Shell commands; placeholders `{app_label}`, `{module_path}`, `{tests_dir}` | manage.py equivalents |

## Discovery checklist (when no profile exists)

Find an existing, representative, recently-touched app and copy what it does. Check, in order:

1. **Layout**: `ls <apps_root>/<existing_app>`; which files exist (`app_settings.py`, `models_abstract*`, `constants.py`, `api/`)?
2. **Swappable?** `grep -rn "swappable" --include=models.py .` and `grep -rn "def get_.*_model" --include=__init__.py .`
3. **Base model**: what do abstract models inherit from? `grep -rn "^class Abstract" --include=*.py . | head`
4. **Settings engine**: `grep -rn "class .*Settings(" --include=app_settings.py .`; note its import path and available descriptors.
5. **Admin**: custom admin sites? `grep -rn "admin.register\|AdminSite" --include=admin.py . | head`
6. **Migrations**: `grep -rn "MIGRATION_MODULES" .`; if set, mode is `external`; note the root.
7. **Registry**: where is `INSTALLED_APPS` / `PROJECT_APPS` assembled? Note lists and naming of model strings.
8. **Commands**: read `Makefile`, `pyproject.toml` scripts, `tox.ini`, CI config for migrate/test/lint commands.
9. **Tests**: where do tests for an existing app live and which framework (pytest vs unittest)?
10. **Tenancy**: `grep -rn "django_tenants\|TENANT_APPS" .`

Present the drafted profile to the user with any uncertain fields marked, get confirmation, then save it.
Prefer asking over guessing for: tenancy scope, migration mode, swappability.
