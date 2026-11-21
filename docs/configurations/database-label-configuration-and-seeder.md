# Analysis & Implementation Log: Database `<module>_template_label` Configuration, Multi-Language Fixtures & Fixture Seeder

## 1. Executive Summary & Goals
Template label management has been elevated from static code defaults to database-backed, multi-language `Configuration` records with automatic language extraction and robust static fallback:
1. **Multi-Language Fixtures**: Structured language-mapped labels file at `core/setup/users/fixtures/template_labels.json` (e.g. `"sign_in": {"en": "Sign In", "es": "Iniciar sesión", "fr": "Se connecter"}`).
2. **Database Configuration (`<module>_template_label`)**: Stored using the core `Configuration` model with `interface_type = "users_template_label"`, registered in `DefaultConfigurationInterfaceTypeChoices`.
3. **Project-Wide UI Language**: Configured at project level (`settings.UI_LANGUAGE`, `settings.DEFAULT_UI_LANGUAGE`, or `settings.LANGUAGE_CODE`).
4. **Fixture & Dev Seeders** (`core/setup/users/seeder.py`):
   - `UsersTemplateLabelFixtureSeeder`: Registered in `fixture_registry` (`is_fixture = True`).
   - `DevUsersTemplateLabelSeeder`: Registered in `seeder_registry` (`is_fixture = False`).
   - Persists using `Configuration.set_config(..., set_cache=False)` to prevent cache stampedes during migrations/seeding.
5. **Resilient Label Resolution**: Priority ladder:
   - **Priority 1**: Explicit backend view/context overrides (`view.labels` or `context["labels"]`).
   - **Priority 2**: Database/cached `Configuration` (`users_template_label`) extracting the project's current UI language.
   - **Priority 3**: Static centralized i18n template defaults (`DEFAULT_AUTH_LABELS`) if DB is unmigrated, empty, or unreachable.
   - **Priority 4**: Humanized title-case fallback for unregistered keys.

---

## 2. Architecture & File Layout

```
core/
├── apps/
│   └── configurations/
│       └── constants.py          # USERS_TEMPLATE_LABEL in DefaultConfigurationInterfaceTypeChoices
├── setup/
│   └── users/
│       ├── fixtures/
│       │   └── template_labels.json   # Multi-language label map
│       └── seeder.py                  # UsersTemplateLabelFixtureSeeder & DevUsersTemplateLabelSeeder
└── utils/
    ├── labels.py                 # Multi-language extraction, DB loading, static fallback
    └── views.py                  # BaseTemplateView injects template_label_interface_type
```

---

## 3. Decisions & Implementation Details

1. **Interface Type Naming**:
   - `USERS_TEMPLATE_LABEL = "users_template_label", _("Users Template Label")` registered directly in `DefaultConfigurationInterfaceTypeChoices` under `core/apps/configurations/constants.py`.
2. **Seeder Persistence**:
   - `set_cache=False` enforced when calling `Configuration.set_config()` to eliminate cache stampedes during bulk seeding.
3. **Seeder Structure**:
   - `UsersTemplateLabelFixtureSeeder` sets `Meta.is_fixture = True`.
   - `DevUsersTemplateLabelSeeder` inherits from it and sets `Meta.is_fixture = False`.
4. **Project-Wide Language**:
   - Resolved via `get_current_ui_language()` checking `UI_LANGUAGE`, `DEFAULT_UI_LANGUAGE`, and `LANGUAGE_CODE`.
5. **Context Injection**:
   - `BaseTemplateView.add_labels_context(context)` automatically passes `self.template_label_interface_type` (`"users_template_label"`) to `resolve_labels()`, injecting only the active language's labels into `context["labels"]`.

---

## 4. Test Verification
- `core/tests/utils/test_labels.py`:
  - `TestLabelsAndLabelDict`: 7 unit tests.
  - `TestDatabaseLabelConfigurationAndLanguageMapping`: 5 unit tests for language extraction, DB resolution, and static fallback.
  - `TestUsersTemplateLabelSeeders`: 5 unit tests for seeder registrations, `set_cache=False`, and JSON validity.
- Test Suite: **371 tests passed (100% pass rate in 22.49s)**.
