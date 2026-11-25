# AGENTS.md

Context for AI agents and developers. Workflows live in skills (section 7). Module detail lives in each `Readme.md`.

## 1. What this is

`core-apps-django` is a reusable Django core framework, consumed as a git submodule by multi-tenant SaaS backends. It provides: schema-per-tenant multi-tenancy, swappable users/auth (OTP, JWT, Google), CRM, invoicing, versioned JSON configuration, integration adapters (email/SMS/payments), seeders, and Celery plumbing.

- **Core owns:** abstract models, libraries, utils, tasks, seeders, REST APIs.
- **Host project owns:** settings, concrete migrations (`db_migrations/` via `MIGRATION_MODULES`), model substitutions. `sample_project/` is the reference host.
- **Deliberately not done here:** fixed concrete entities, migrations in core, blocking I/O on the request thread, touching the host's `BASE_DIR`.

## 2. Mental model (read before touching code)

1. **Models:** abstract class in `models_abstract.py` holds all fields and logic. `models.py` has a thin concrete subclass with `swappable = "APP_MODEL_KEY"`. The app's `__init__.py` exports `get_<model>_model()`. A host overrides `settings.APP_MODEL_KEY` to substitute its own model.
2. **Settings:** each app declares descriptors (`Settings`, `Constance`, `Configuration`) on a `BaseSettings` subclass in `app_settings.py`. The singleton is created in the app's `__init__.py`.
3. **Async:** `queue_task()` wraps Celery. It prefixes idempotency keys with the schema name and defers dispatch to commit. `TenantAwareTask` carries `_schema_name` in message headers, and a `task_prerun` signal switches the worker to that schema.
4. **Tenancy:** `django-tenants`. `SHARED_APPS` live in `public`, `TENANT_APPS` in each tenant schema. `core.apps.users` is deliberately in both. Tenant schemas are created asynchronously (`provision_tenant_schema`), never on the request thread.
5. **Extension:** apps extend each other through registries (`core/utils/registry`, `LazyDynamicChoiceTypes`, seeder registries), not through imports.

## 3. Stack

Python 3.12+, Django 5.2, DRF, django-tenants, Celery + django-celery-beat/results, Valkey (cache + broker), PostgreSQL, Jinja2 (app UI) + DTL (admin only), django-constance, simplejwt + dj-rest-auth, drf-spectacular, pytest + pytest-django, factory-boy. Exact versions: `pyproject.toml` / `poetry.lock`.

## 4. Commands

Everything runs in Docker via `make`. Only `pre-commit` runs on the host. Targets are defined in `scripts/common.mk`.

| Need | Command |
| --- | --- |
| Tests (all / dir / filter) | `make t` / `make t TEST_DIR=<path>` / `make tf TEST_FILTER=<expr>` |
| Make / apply migrations | `make mm APP_LABEL=<app>` / `make m` (public) / `make ms` (tenants) |
| Backup DB before changes | `make db-dump` (logical) / `make db-volume-dump` (cold snapshot) |
| Seed dev data | `make seed-tenants`, `make seed-models` |
| Shells | `make s`, `make sp`, `make ts SCHEMA=<name>` |
| Lint/format | `poetry run pre-commit run --all-files` (host) |
| Link submodule skills into host | `make link-skills` |

**Destructive, never run without explicit approval:** `db-destroy`, `clean`, `clean-setup`, `cbr`, `db-delete`, `db-restore`, `db-volume-restore`.

## 5. Repo map

```
core/libraries/   NEW HOME for core libraries (seeder today; app_settings is moving here from core/utils/)
core/utils/       small cross-cutting helpers: error_handling, generators, models, serializers, registry, tasks.py (queue_task), routers.py
core/seeder/      LEGACY seeder, being migrated to core/libraries/seeder. Do not extend.
core/config/      settings, celery (TenantAwareTask), logging
core/apps/        tenants, users, configurations, crm, invoices, integrations (+email/sms/payments)
core/templates/   Jinja2 UI
sample_project/   reference host (compose, settings, db_migrations)
docs/             agent-only working logs (docs/<feature>/analysis.md)
.agents/skills/   skills
```

- **Libraries vs utils:** new reusable, self-contained building blocks go in `core/libraries/`. `core/utils/` is for small helpers. When unsure, ask.
- **Migration in progress:** `app_settings` may exist in both `core/utils/` and `core/libraries/`. Import from the `core.libraries` location if it exists, and never edit the old copy once the new one exists. Use `graphify query` to see where it currently lives.

App order (each depends only on those above it): `tenants`/`integrations` → `configurations` → `users` → `crm` → `invoices`.

| App | Schema | Role |
| --- | --- | --- |
| tenants | public | tenant, domain, branding, contact info, async provisioning |
| users | both | accounts, OTP, lockout, Google login |
| configurations | tenant | versioned JSON config + JSONSchema |
| crm | tenant | customers, contacts, KYC, OCR pipeline |
| invoices | tenant | billing orgs, parties, invoices, items, fees |
| integrations | tenant | provider credentials; email/SMS/payment logs |

## 6. Rules (each has a reason; if the reason doesn't apply, ask)

1. **Resolve models via getters, once, at module level** (`User = get_user_model()`). FKs use settings strings (`settings.CRM_CUSTOMER_MODEL`). Import abstract classes under `TYPE_CHECKING` for annotations. *Why:* concrete imports bind at load time and break host overrides.
2. **Dispatch tasks only via `queue_task()`**, with an `idempotency_key`, passing IDs (not instances) and the schema name. *Why:* commit-safety, dedupe, schema propagation.
3. **No network I/O on the request thread.** Queue it; return `202`. If queuing fails, log; never fall back to a blocking call.
4. **Settings:** app-specific in `app_settings.py`, project-wide only in `settings.py`. Never instantiate the settings class in `app_settings.py`. Never override `CORE_BASE_DIR`/`CORE_APP_DIR`. *Why:* a host overriding `BASE_DIR` must not break core fixtures.
5. **Data from a feature:** production data goes in fixtures (`is_fixture=True`, `core/apps/<app>/fixtures/`). Dev-only data goes in seed JSON (`core/setup/<app>/`). Load `add-seeder`.
6. **No multi-table inheritance.** Use discriminator fields + abstract mixins. *Why:* joins and migration complexity.
7. **No unnecessary fallbacks.** Use one definitive config key (`settings.LANGUAGE_CODE`), not `getattr(a, "x", getattr(b, "y", ...))` chains. Do not `getattr(self, "attr", default)` for attributes the class declares. Do not add silent default values or `try/except` that hides misconfiguration. Fail fast and raise. *Why:* fallbacks make wrong host configuration look like it works. A fallback at a real trust boundary needs a one-line comment saying why.
8. **No `unittest.mock` or `if testing:` in production code.** Fix the test, not the production validation.
9. **Backup first:** run `make db-dump` before `make m`, `make ms`, or any seeder/data command that mutates a database you care about. Record the dump filename in your report.
10. **Stale migration or test DB: stop and report** (which migration/table, the error, suggested fix). Never fix, delete, or recreate it. *Why:* `--reuse-db` is on and the user owns DB state.
11. **Never log secrets or PII.** Route PII-bearing data through `ContentMaskingUtils`.
12. **Never bypass pre-commit** (`--no-verify`, disabling rules). Fix the cause.
13. **Documentation stays clear and crisp.** Update the module `Readme.md` in the same change that alters documented behavior. No code dumps, no `TODO` stubs, no stale claims. Agent working notes go in `docs/<feature>/analysis.md`, never in Readmes. Load `backend-docs`.
14. **Templates:** read `core/templates/Readme.md` first. No inline JS, no hardcoded colors (use `variables.css` tokens).
15. **Use model factories for test objects and fixtures.** Always use `factory_boy` factories from `core.apps.<app>.factories` (e.g. `UserFactory`, `CustomerFactory`) in tests. Never use raw `Model.objects.create(...)` or `User.objects.create_user(...)`. When new models are introduced, create their factory in `core/apps/<app>/factories.py` using dynamic model getters (`get_<model>_model()`). *Why:* factories keep tests resilient to schema changes and enforce swappable model support.

**Precedence:** these rules > the workflow skill > `ponytail`. Ponytail decides how little code to write. It never skips the analysis gate, the backup, tests, pre-commit, or documentation.

## 7. Skills

Skills live in `.agents/skills/`. **Load only what the task needs.** Do not load a skill "to be safe". Each one costs context.

**Always load at session start:** `vcs-workflow`, `graphify`.

**Load for any code change** (pick exactly one workflow):

| Skill | Use for |
| --- | --- |
| `backend-bugfix` | existing behavior is wrong, fix fits current models/tasks/interfaces |
| `backend-feature-lifecycle` | new feature, model/task/cron/setting change, behavior change, refactor |
| `ponytail` | keep the change minimal (smallest complete diff) |

Do not edit code without a workflow skill loaded. Not sure which track? Pick `backend-feature-lifecycle` and say why.

**Load only when the step needs it:**

| Skill | Load when |
| --- | --- |
| `backend-pytest` | writing, extending or running tests |
| `backend-doc-string` | adding or changing docstrings |
| `backend-docs` | a Readme or `docs/` file must change, or a new app/module is added |
| `create-django-app` | creating a new app |
| `add-seeder` | adding fixtures or dev seed data |

**Only when the user asks** (never load on your own): `ponytail-review`, `ponytail-audit`, `ponytail-debt`.

Graphify fallback: if `graphify-out/graph.json` does not exist, read the module `Readme.md`, then targeted files.

## 8. Where to look

Module `Readme.md` first (every app and util has one; the `integrations/{email,sms,payments}` ones are empty stubs). Then `app_settings.py` → `models_abstract.py` → `tasks.py` → `api/`. Agent working logs: `docs/<feature>/analysis.md`.

## 9. Known gaps (do not assume these exist)

- No tenant-isolation tests exist yet. Add one when touching tenant-scoped code.
- No on-commit capture helper is used in tests yet.
- No CI and no coverage config. `celerybeat` is disabled in compose.
- Existing violations (do not copy): concrete imports in `tenants/api/views.py` and `tests/invoices/test_views.py`; inline JS in `core/templates/core/base.jinja` and `authenticated_view.jinja`; hardcoded SVG colors in `username_login.jinja`.
