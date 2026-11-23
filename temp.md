# Project Context Report: `core-apps-django`

## 1. IDENTITY

`core-apps-django` is a reusable, production-ready Django core framework designed to be consumed as a Git submodule or base package by multi-tenant SaaS backends. It provides domain-agnostic foundation modules—including PostgreSQL schema-based multi-tenancy, swappable authentication and user management, customer relationship management (CRM), invoicing, dynamic JSON configurations, and communications/payments integration adapters. Consuming projects (such as `sample_project/`) retain ownership over their host settings, concrete database migrations (`db_migrations/`), and custom model substitutions while inheriting core utilities, background tasks, seeders, and REST APIs.

**Evidence:**
- [Readme.md](file:///Users/<user-name>//Documents/core-apps-django/Readme.md#L3): *"The core is meant to be used as a sub-module in your project, just use the app as a submodule in you'r project and configure you'r project taking reference from sample_project."*
- [AGENTS.md](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L5-L7): *"This repository is a reusable, production-ready Django core framework, typically consumed as a submodule or base package. It emphasizes modularity, multi-tenant isolation, swappable model declarations, and decoupled configuration."*

**What it deliberately does NOT do:**
1. **Does not define fixed, non-swappable concrete entities:** All domain models in `core/apps/` inherit from abstract definitions with `swappable = "APP_MODEL_KEY"` to prevent binding consuming projects to rigid schemas ([models_abstract.py](file:///Users/<user-name>//Documents/core-apps-django/core/apps/crm/models_abstract/customer.py#L12)).
2. **Does not own or generate production database migrations in core apps:** Core apps provide model schemas; the host project maintains concrete migration files under its own `db_migrations/` via Django's `MIGRATION_MODULES` ([sample_project/config/settings/local.py](file:///Users/<user-name>//Documents/core-apps-django/sample_project/config/settings/local.py#L17-L26)).
3. **Does not run blocking external I/O or heavy operations on the HTTP request thread:** Tasks like schema provisioning, SMS/email dispatch, and OCR processing are offloaded to Celery background workers via `queue_task` ([core/utils/tasks.py](file:///Users/<user-name>//Documents/core-apps-django/core/utils/tasks.py#L40)).
4. **Does not enforce single-tenant-only assumptions:** Multi-tenancy is active by default at the database schema level using `django-tenants`, though a single-tenant override configuration is provided for projects that opt out ([single_tenant.py](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/single_tenant.py#L1-L22)).
5. **Does not hijack host directory paths:** Core paths anchor to `CORE_BASE_DIR` and `CORE_APP_DIR` to prevent collisions with host `BASE_DIR` overrides ([base.py](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base.py#L21-L26)).

---

## 2. STACK

All versions are extracted directly from [pyproject.toml](file:///Users/<user-name>//Documents/core-apps-django/pyproject.toml#L5-L31) and pinned versions from [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock):

| Component | Library / Tool | Specified Constraint | Locked Version | Evidence File |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | Python Runtime | `>=3.12,<4` | `3.12+` | [pyproject.toml#L5](file:///Users/<user-name>//Documents/core-apps-django/pyproject.toml#L5) |
| **Backend Framework** | `django` | `==5.2.16` | `5.2.16` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **REST API** | `djangorestframework` | `>=3.17.1,<4.0.0` | `3.18.3` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Multi-Tenancy** | `django-tenants` | `>=3.10.2,<4.0.0` | `3.14.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Worker / Queue** | `celery` | `>=5.6.3,<6.0.0` | `5.6.3` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Task Results** | `django-celery-results` | `>=2.6.0,<3.0.0` | `2.6.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Periodic Tasks** | `django-celery-beat` | `>=2.9.0,<3.0.0` | `2.9.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Message Broker** | `valkey` / `redis` | `valkey >=6.1.1` / `redis >=8.0.1` | `valkey 6.2.0` / `redis 8.1.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Database** | `psycopg2-binary` (PostgreSQL) | `>=2.9.12,<3.0.0` | `2.9.13` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Cache Client** | `django-redis` / `valkey` | `django-redis >=7.0.0` | `7.0.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Live Settings** | `django-constance` | `>=4.3.5,<5.0.0` | `4.3.5` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Template Engine** | `jinja2` | `>=3.1.5,<4.0.0` | `3.1.6` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Auth & JWT** | `djangorestframework-simplejwt` | `>=5.5.1,<6.0.0` | `5.5.1` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Auth Endpoints** | `dj-rest-auth` | `>=7.2.0,<8.0.0` | `7.2.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **API Schema/Docs** | `drf-spectacular` | `>=0.30.0,<0.31.0` | `0.30.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Testing** | `pytest` / `pytest-django` | `>=9.1.1` / `>=4.12.0` | `9.1.1` / `4.12.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Test Factories** | `factory-boy` | `>=3.3.3,<4.0.0` | `3.3.3` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Model Utilities** | `django-model-utils` | `>=5.0.0,<6.0.0` | `5.0.0` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Storage** | `django-storages` | `>=1.14.6,<2.0.0` | `1.14.6` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Phone Handling** | `django-phonenumber-field` / `phonenumbers` | `>=9.0.0` / `>=9.0.42` | `9.0.0` / `9.0.42` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |
| **Nested Routers** | `drf-nested-routers` | `>=0.95.3,<0.96.0` | `0.95.3` | [poetry.lock](file:///Users/<user-name>//Documents/core-apps-django/poetry.lock) |

---

## 3. EXECUTION ENVIRONMENT

### Container vs. Host Split
- **Host Machine Execution:** Only `pre-commit` is permitted to run on the host ([AGENTS.md#L208-L209](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L208-L209)).
- **Container Execution:** All Django commands, test executions, migrations, database operations, Celery workers, and poetry commands run inside Docker containers via `docker compose` abstractions defined in [scripts/common.mk](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L28-L36).

### Makefile Targets
Defined in [Makefile](file:///Users/<user-name>//Documents/core-apps-django/Makefile) and included from [scripts/common.mk](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk):

| Target | What It Does | When to Use | Evidence File |
| :--- | :--- | :--- | :--- |
| `start-app` / `docker-start-new-app` | Creates new modular app directory and runs `manage.py startapp` | Scaffolding a new core app (`APP_LABEL=<name>`) | [common.mk#L62-L66](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L62-L66) |
| `seed-tenants` | Runs `python manage.py add_dev_tenants` | Populating default dev public and org tenants | [common.mk#L68-L71](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L68-L71) |
| `seed-models` | Runs `python manage.py run_dev_seeders` | Running all dev seeders across tenant schemas | [common.mk#L73-L76](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L73-L76) |
| `setup` / `docker-dev-setup` | Runs `rund`, `m`, `seed-tenants`, `ms`, `seed-models` in sequence | Initial bootstrap of a clean local development environment | [common.mk#L78-L85](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L78-L85) |
| `clean-setup` | Destroys database volume (`db-destroy`) then runs `setup` | Total reset and re-seed of development database | [common.mk#L87-L91](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L87-L91) |
| `build` / `docker-build` | Executes `docker compose build` | Building or updating Docker container images | [common.mk#L99-L103](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L99-L103) |
| `rebuild` | Runs `down`, `build`, and `rund` | Rebuilding containers from scratch and restarting detached | [common.mk#L105-L110](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L105-L110) |
| `clean` | Runs `compose down --volumes --rmi all --remove-orphans` | Purging all project images, volumes, and containers | [common.mk#L112-L115](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L112-L115) |
| `cbr` | Runs `clean`, `build`, `m`, `run` | Complete clean build and foreground run | [common.mk#L117-L122](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L117-L122) |
| `run` / `docker-run` | Runs `docker compose up` attached | Starting containers in the foreground | [common.mk#L124-L127](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L124-L127) |
| `rund` / `docker-detached-run` | Runs `docker compose up -d` | Starting containers in detached background mode | [common.mk#L129-L132](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L129-L132) |
| `vscode-debug` | Runs containers attached with `debugpy` listening on port 5678 | Attaching VSCode Python debugger to Django container | [common.mk#L134-L137](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L134-L137) |
| `db-destroy` | Executes `docker compose down --volumes` | Dropping all Docker persistent DB volumes | [common.mk#L139-L141](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L139-L141) |
| `db-dump` / `pg-dump` | Runs ephemeral `pg_dump` container targeting database(s) | Exporting `.dump` (custom binary) or `all_databases.sql` | [common.mk#L150-L154](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L150-L154) |
| `db-restore` / `pg-restore` | Runs ephemeral `pg_restore` container from `BACKUP_FILE` | Restoring database schema and data from backup file | [common.mk#L156-L164](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L156-L164) |
| `db-delete` / `pg-delete` | Runs ephemeral container to drop single DB or user DBs | Dropping databases programmatically before clean restore | [common.mk#L166-L170](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L166-L170) |
| `db-volume-dump` | Stops Postgres container, archives volume to `.tar.gz`, restarts | Cold physical snapshot of Docker volume data | [common.mk#L172-L184](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L172-L184) |
| `db-volume-restore` | Stops Postgres container, extracts `BACKUP_FILE` into volume, restarts | Overwriting Docker volume from physical archive | [common.mk#L186-L202](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L186-L202) |
| `mm` | Runs `python manage.py makemigrations [APP_LABEL]` | Generating new Django migrations for an app | [common.mk#L210-L214](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L210-L214) |
| `m` | Runs `python manage.py migrate` | Applying public schema migrations | [common.mk#L216-L219](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L216-L219) |
| `ms` | Runs `python manage.py migrate_schemas` | Applying migrations across all tenant schemas | [common.mk#L221-L224](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L221-L224) |
| `mme` | Runs `python manage.py makemigrations --empty [APP_LABEL] --name [EMN]` | Creating an empty migration skeleton | [common.mk#L226-L230](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L226-L230) |
| `t` / `test` | Runs `pytest [TEST_DIR]` inside container | Running the test suite (defaults to `core/tests`) | [common.mk#L238-L242](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L238-L242) |
| `tf` | Runs `pytest -k [TEST_FILTER]` inside container | Running targeted tests matching keyword expression | [common.mk#L244-L247](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L244-L247) |
| `td` | Runs `pytest` inside debugpy container with port 5678 listener | Debugging test execution interactively | [common.mk#L249-L252](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L249-L252) |
| `bash` | Launches bash shell inside temporary Django container | Interactive command line inside container | [common.mk#L259-L262](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L259-L262) |
| `s` | Runs `python manage.py shell` inside container | Standard interactive Django Python shell | [common.mk#L264-L267](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L264-L267) |
| `sp` | Runs `python manage.py shell_plus --ipython` | Enhanced IPython Django shell with preloaded models | [common.mk#L269-L272](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L269-L272) |
| `ts` | Runs `manage.py tenant_command shell --schema=[SCHEMA]` | Interactive shell bound to specific tenant schema | [common.mk#L274-L277](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L274-L277) |
| `tsd` | Runs tenant shell with debugpy attached | Debugging tenant-scoped commands | [common.mk#L279-L282](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L279-L282) |
| `tsp` | Runs `tenant_command shell_plus` | Enhanced IPython shell in tenant schema | [common.mk#L284-L287](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L284-L287) |
| `tspd` | Runs `tenant_command shell_plus` with debugpy | Debugging tenant-scoped shell_plus | [common.mk#L289-L292](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L289-L292) |
| `cache-cli` | Runs `redis-cli -p [CACHE_PORT]` in cache container | Direct inspection of cache Valkey instance | [common.mk#L294-L297](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L294-L297) |
| `broker-cli` | Runs `redis-cli -p [BROKER_PORT]` in broker container | Direct inspection of Celery broker Valkey instance | [common.mk#L299-L302](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L299-L302) |
| `poetry` | Runs `poetry [CMD]` inside temporary Django container | Running Poetry dependency commands in container | [common.mk#L310-L313](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L310-L313) |
| `link-agents` / `link-skills` | Executes `scripts/link_agents.sh` | Symlinking submodule agents/skills into consuming host | [common.mk#L321-L325](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L321-L325) |
| `unlink-agents` / `unlink-skills` | Executes `scripts/unlink_agents.sh` | Removing symlinked agents/skills from consuming host | [common.mk#L327-L331](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L327-L331) |
| `list-agents` / `list-skills` | Executes `scripts/list_agents.sh` | Inspecting symlink status of agent skills | [common.mk#L333-L337](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L333-L337) |

### Docker Compose Services
Defined in [sample_project/compose/local/compose.local.yaml](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml) and supporting tool configs:
- `django`: Main application web server running Daphne/Uvicorn/WSGI on port 8000 ([compose.local.yaml#L6-L39](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L6-L39)).
- `postgres`: PostgreSQL 14/15/16 database server on port 5432 with health check ([compose.local.yaml#L40-L57](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L40-L57)).
- `cache`: Valkey in-memory cache server (`valkey/valkey:8.1.5-alpine`) on port 6379 ([compose.local.yaml#L58-L70](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L58-L70)).
- `broker`: Valkey Celery task broker (`valkey/valkey:8.1.5-alpine`) on port 6378 with AOF persistence enabled ([compose.local.yaml#L71-L84](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L71-L84)).
- `celeryworker`: Background task worker running `/scripts/worker-start.sh` ([compose.local.yaml#L85-L96](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L85-L96)).
- `celerybeat`: Periodic task scheduler (currently disabled/commented out; scheduled for implementation) ([compose.local.yaml#L97-L106](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/compose.local.yaml#L97-L106)).
- `pg_dump` / `pg_restore` / `pg_delete`: Ephemeral `postgres:14-alpine` utility containers for granular database backup/restore ([pg_tools_granular.yml](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/pg_tools_granular.yml#L1-L46)).
- `volume_dump` / `volume_restore`: Ephemeral `alpine` utility containers for raw Docker volume archiving ([pg_tools.yml](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/pg_tools.yml#L1-L23)).

### Scripts Directory Inventory (`scripts/`)
- [common.mk](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk): Reusable Makefile containing all Docker build, test, database dump, migration, shell, and agent management recipes.
- [link_agents.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/link_agents.sh): Relative-path symlinker linking `.agents/` assets from the submodule into the parent project.
- [link_skills.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/link_skills.sh): Convenience wrapper around `link_agents.sh` targeted specifically at `.agents/skills`.
- [list_agents.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/list_agents.sh): Status reporter checking whether `.agents/` assets are linked, missing, or unlinked.
- [list_skills.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/list_skills.sh): Convenience wrapper around `list_agents.sh` filtering for skills only.
- [unlink_agents.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/unlink_agents.sh): Cleaner script removing agent symlinks from the parent repository.
- [unlink_skills.sh](file:///Users/<user-name>//Documents/core-apps-django/scripts/unlink_skills.sh): Convenience wrapper around `unlink_agents.sh` targeting skills only.

---

## 4. TENANCY MODEL

### Schema Creation & Switching
- **Creation:** Multi-tenant schemas are created asynchronously. In [AbstractTenants.save()](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/models_abstract.py#L77-L97), `auto_create_schema = False` prevents blocking HTTP requests. On creation, `save()` enqueues the Celery task `provision_tenant_schema` via `queue_task(on_commit=True)`. The task executes `tenant.create_schema(check_if_exists=True, sync_schema=True)` and marks the tenant status as `READY` ([tasks.py#L38](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/tasks.py#L38)).
- **HTTP Schema Switching:** Handled by `django_tenants.middleware.main.TenantMainMiddleware` ([base.py#L221](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base.py#L221)), resolving the active tenant by domain and switching PostgreSQL `search_path`.
- **Code Schema Switching:** Invoked using `django_tenants.utils.schema_context(schema_name)` ([conftest.py#L11-L68](file:///Users/<user-name>//Documents/core-apps-django/core/tests/conftest.py#L11-L68)).

### Public vs. Tenant Schema Placement
Configured in [core/config/settings/base_models.py#L122-L145](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base_models.py#L122-L145):
- **Public Schema (`SHARED_APPS`):** `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `django_tenants`, `rest_framework`, `rest_framework_simplejwt`, `token_blacklist`, `dj_rest_auth`, `constance`, `drf_spectacular`, `storages`, `django_celery_results`, `core.apps.tenants`, `core.apps.users`.
- **Tenant Schemas (`TENANT_APPS`):** System apps, `core.apps.crm`, `core.apps.configurations`, `core.apps.invoices`, `core.apps.users`, `core.apps.integrations`, `core.apps.integrations.email`, `core.apps.integrations.sms`.
- *Note on Discrepancy:* `core.apps.users` is declared in **both** `DJANGO_TENANT_PUBLIC_APPS` and `DJANGO_TENANT_PRIVATE_APPS` ([base_models.py#L128](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base_models.py#L128), [base_models.py#L139](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base_models.py#L139)), permitting global user tables as well as tenant-specific user relations.

### Migration Routing Across Schemas
- Driven by `django_tenants.routers.TenantSyncRouter` in `DATABASE_ROUTERS` ([base.py#L103](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base.py#L103)).
- The host project specifies `MIGRATION_MODULES` ([sample_project/config/settings/local.py#L17-L26](file:///Users/<user-name>//Documents/core-apps-django/sample_project/config/settings/local.py#L17-L26)), routing migration state into the host's `db_migrations/` folder.
- Executed via `python manage.py migrate` (public schema) or `python manage.py migrate_schemas` (tenant schemas) ([common.mk#L216-L224](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L216-L224)).

### Schema Propagation in Celery Tasks
- Celery tasks subclass `TenantAwareTask` ([base.py#L14-L41](file:///Users/<user-name>//Documents/core-apps-django/core/config/celery/base.py#L14-L41)), which automatically captures `connection.schema_name` and injects `_schema_name` into Celery message headers.
- On the worker process, Celery signal `task_prerun` connects to `switch_schema_context` ([base.py#L44-L100](file:///Users/<user-name>//Documents/core-apps-django/core/config/celery/base.py#L44-L100)), extracting `_schema_name` and calling `connection.set_tenant(tenant)` or `connection.set_schema_to_public()`.
- After completion, `task_postrun` triggers `restore_schema_context` to revert the connection to its prior state ([base.py#L82-L102](file:///Users/<user-name>//Documents/core-apps-django/core/config/celery/base.py#L82-L102)).

### Tenant Provisioning Code Locations
- Model Hook: [AbstractTenants.save()](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/models_abstract.py#L77-L97)
- Celery Provisioning Task: [provision_tenant_schema()](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/tasks.py#L16-L53)
- CLI Dev Seeder Command: [add_dev_tenants.py](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/management/commands/add_dev_tenants.py#L21-L60)

---

## 5. APP INVENTORY

| Name | Purpose | Public or Tenant | Swappable Model Keys | Tasks / Crons | API Endpoints (Prefixes) | Depends On (Core Apps) | Has Readme? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tenants` | Multi-tenant schema management, domain routing, branding, contact info | Public | `TENANTS_TENANT_MODEL`, `TENANTS_DOMAIN_MODEL`, `TENANTS_CONTACT_INFO_MODEL`, `TENANTS_BRANDING_MODEL` | `provision_tenant_schema` | `/branding/` | `configurations` (in seeder fixture) | Yes ([tenants/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/Readme.md)) |
| `users` | User accounts, credentials, OTP generation/verification, lockout protection, social login | Public & Tenant | `AUTH_USER_MODEL`, `USERS_USER_MODEL`, `USERS_SOCIAL_ACCOUNT_MODEL`, `USERS_OTP_LOG_MODEL` | `send_otp_task`, `create_otp_log_task`, `send_account_unlock_email_task` | `/auth/password/`, `/auth/otp/email/`, `/auth/otp/sms/`, `/auth/unlock/`, `/auth/user/`, `/auth/token/refresh/`, `/auth/logout/`, `/auth/social/google/`, `/auth/password/change/`, `/auth/password/reset/`, `/auth/password/reset/confirm/` | `crm` (in serializer linking) | Yes ([users/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/users/Readme.md)) |
| `configurations` | Runtime configuration storage, JSONSchemas, versioned settings per tenant | Tenant | `CONFIGURATIONS_CONFIGURATION_MODEL`, `CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL`, `CONFIGURATIONS_TENANT_CONFIGURATION_MODEL` | None | None (managed via admin and seeders) | `tenants` | Yes ([configurations/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/Readme.md)) |
| `crm` | Customer accounts, contact channels, addresses, KYC verification, OCR pipeline, preferences | Tenant | `CRM_CUSTOMER_MODEL`, `CRM_CUSTOMER_PHONE_MODEL`, `CRM_CUSTOMER_EMAIL_MODEL`, `CRM_CUSTOMER_ADDRESS_MODEL`, `CRM_CUSTOMER_IDENTIFICATION_MODEL`, `CRM_CUSTOMER_PREFERENCE_TYPE_MODEL`, `CRM_CUSTOMER_PREFERENCE_MODEL` | `process_customer_identification_ocr`, `process_unverified_identifications_cron` (Celery Beat) | `/customers/`, `/customer-preference-types/`, nested: `/customers/{lookup}/phones/`, `/emails/`, `/addresses/`, `/identifications/`, `/preferences/` | `users`, `configurations` | Yes ([crm/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/crm/Readme.md)) |
| `invoices` | Billing organizations, financials, assets, invoice parties, documents, line items, entries, fees, templates | Tenant | `INVOICES_INVOICE_MODEL`, `INVOICES_INVOICE_ADDRESS_MODEL`, `INVOICES_INVOICE_TEMPLATE_MODEL`, `INVOICES_BILLING_ORGANIZATION_MODEL`, `INVOICES_ORGANIZATION_EMAIL_MODEL`, `INVOICES_ORGANIZATION_PHONE_MODEL`, `INVOICES_ORGANIZATION_FINANCIALS_MODEL`, `INVOICES_ORGANIZATION_ASSETS_MODEL`, `INVOICES_INVOICE_PARTY_MODEL`, `INVOICES_INVOICE_PARTY_CATEGORY_MODEL`, `INVOICES_INVOICE_PARTY_EMAIL_MODEL`, `INVOICES_INVOICE_PARTY_PHONE_MODEL`, `INVOICES_INVOICE_ITEM_MODEL`, `INVOICES_INVOICE_ITEM_ENTRY_MODEL`, `INVOICES_INVOICE_ITEM_FEE_MODEL` | None | `/invoices/`, `/invoice-addresses/`, `/invoice-templates/`, `/billing-organizations/`, `/organization-emails/`, `/organization-phones/`, `/organization-financials/`, `/organization-assets/`, `/invoice-parties/`, `/invoice-party-categories/`, `/invoice-party-emails/`, `/invoice-party-phones/`, `/invoice-items/`, `/invoice-item-entries/`, `/invoice-item-fees/` | `crm`, `users` | Yes ([invoices/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/invoices/Readme.md)) |
| `integrations` | External provider integrations & credentials manager; subapps for email, SMS, payments | Tenant | `INTEGRATIONS_INTEGRATION_MODEL`, `INTEGRATIONS_CREDENTIALS_MANAGER_MODEL`, `INTEGRATIONS_EMAIL_EMAIL_LOG_MODEL`, `INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL`, `INTEGRATIONS_SMS_SMS_LOG_MODEL`, `INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL`, `INTEGRATIONS_PAYMENTS_PAYMENT_LOG_MODEL` | `log_email_dispatch`, `log_sms_dispatch`, `log_payment_dispatch` | None (internal service layer) | None | Yes ([integrations/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/integrations/Readme.md)) |

### Inter-App Dependency Order
1. `core.utils` / `core.libraries` (foundation primitives, base models, registries)
2. `core.apps.tenants` & `core.apps.integrations` (base multi-tenancy and credential storage)
3. `core.apps.configurations` (depends on `tenants` for `TenantConfiguration`)
4. `core.apps.users` (depends on `tenants`, soft-links to `crm`)
5. `core.apps.crm` (depends on `users` for `AUTH_USER_MODEL`, `configurations`)
6. `core.apps.invoices` (depends on `crm` for customer/party links, `users`)

---

## 6. CORE MECHANISMS

### Swappable Models and Dynamic Getters
Models are declared as abstract classes in `models_abstract.py`, defining fields, managers, and lifecycle logic. Concrete models subclass them in `models.py` without adding fields and declare `swappable = "APP_MODEL_KEY"`. Dynamic getters are exported in the app root `__init__.py` using `apps.get_model(settings.APP_MODEL_KEY, require_ready=False)`. Serializers, views, and services resolve concrete models once at module top level (`User = get_user_model()`) to avoid premature model resolution cycles.
*Entry points:* [base_models.py#L9-L74](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base_models.py#L9-L74), [core/apps/users/\_\_init\_\_.py#L15-L23](file:///Users/<user-name>//Documents/core-apps-django/core/apps/users/__init__.py#L15-L23), [core/apps/crm/models.py#L10-L15](file:///Users/<user-name>//Documents/core-apps-django/core/apps/crm/models.py#L10-L15).

### App Settings Descriptors (`Settings`, `Constance`, `Configuration`)
App configuration is declared on a `BaseSettings` subclass within `app_settings.py` and instantiated as a singleton in the app's `__init__.py`. Descriptors encapsulate three configuration tiers: `Settings` (static settings with type checking and deferred imports), `Constance` (live Redis/cache-backed admin-editable flags via `django-constance`), and `Configuration` (dynamic, versioned database JSON configurations resolved per tenant schema).
*Entry points:* [base.py](file:///Users/<user-name>//Documents/core-apps-django/core/utils/app_settings/base.py#L125), [types.py](file:///Users/<user-name>//Documents/core-apps-django/core/utils/app_settings/types.py#L22), [core/apps/configurations/app_settings.py#L7-L18](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/app_settings.py#L7-L18).

### `queue_task` Dispatch Wrapper
Wraps Celery's `.delay()` and `.apply_async()` into a standardized dispatch function. It supports `on_commit=True` via Celery's `task.apply_async_on_commit`, prefixes `idempotency_key` with the active schema name (`f"{connection.schema_name}:{task.__name__}-{idempotency_key}"`), suppresses result backend storage when `ignore_result=True`, and pairs with `TenantAwareTask` to guarantee that schema context is preserved across worker processes.
*Entry points:* [tasks.py#L39-L97](file:///Users/<user-name>//Documents/core-apps-django/core/utils/tasks.py#L39-L97), [celery/base.py#L14-L41](file:///Users/<user-name>//Documents/core-apps-django/core/config/celery/base.py#L14-L41).

### Base Model Hierarchy and Soft Delete
All domain models subclass `BaseModel`, which combines `UUIDModel` (UUIDv4 primary keys), `TimeStampedModel` (`created`, `modified`), and `DeletionTrackingModel`. Soft deletion is the default behavior: calling `.delete()` sets `is_removed=True` and records `removed_by`. Hard deletion requires explicit `.delete(soft=False)`. Active records must be queried via `.available_objects` or `BaseModel.get_object(**filters)`. Configuration models subclass `BaseSemanticVersionModel` to support `bump_version(bump_type)`.
*Entry points:* [base.py#L7-L37](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/base_models/base.py#L7-L37), [soft_delete.py#L15-L87](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/soft_delete.py#L15-L87), [version.py#L35-L160](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/version.py#L35-L160).

### `LazyDynamicChoiceTypes`
A lazy choice registry that wraps Django's `LazyObject` and `DynamicChoiceType`. It allows apps to declare dynamic choice registries that accept runtime choice contributions via `.contribute(choices)` from dictionaries, Python `Enum`, or Django `TextChoices`. This enables decoupled modular apps to extend shared choice sets without cyclic imports.
*Entry points:* [lazy_objects.py#L50-L86](file:///Users/<user-name>//Documents/core-apps-django/core/utils/lazy_objects.py#L50-L86).

### Seeders, Fixtures, and `AutoDiscovery`
The seeder system in `core.libraries.seeder` provides declarative, dependency-ordered data population. Seeders subclass `BaseSeeder` with class-level attributes (`method`, `loader`, `related_seeder_map`, `depends_on`). Class instantiation registers seeders into `seeder_registry` (all seeders) and `fixture_registry` (only `is_fixture=True`). `SeederRunner` builds an instance DAG via topological sort and runs seeders isolated per schema. Modules are discovered using `AutoDiscovery` scanning file paths.
*Entry points:* [seeder.py](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/seeder.py#L19), [runner.py](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/runner.py#L35), [registry.py](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/registry.py#L7), [autodiscovery.py#L16-L115](file:///Users/<user-name>//Documents/core-apps-django/core/utils/autodiscovery.py#L16-L115).

### Error Handling & `ContentMaskingUtils`
Centralized error handling and sensitive data masking. `ContentMaskingUtils` matches dictionaries, iterables, and raw strings against regex patterns and phrase baselines (`DEFAULT_SENSITIVE_CONTENT_PHRASES`, e.g., `password`, `token`, `secret`, `ssn`, `pan`) to mask values as `***MASKED***`. Custom logging formatters and domain exceptions inherit from this utility to prevent PII and credentials from leaking into log files.
*Entry points:* [content_masking.py#L6-L135](file:///Users/<user-name>//Documents/core-apps-django/core/utils/error_handling/content_masking.py#L6-L135), [exceptions.py](file:///Users/<user-name>//Documents/core-apps-django/core/exceptions.py#L1-L100).

### Router Selection by Environment
Environment-aware REST API routing utility. `get_api_router_instance()` and `get_nested_api_router_instance()` inspect `settings.DEBUG`: when `DEBUG=True`, they instantiate DRF's `DefaultRouter` / `NestedDefaultRouter` (providing the browsable API and schema roots); in production (`DEBUG=False`), they return `SimpleRouter` / `NestedSimpleRouter` for deterministic, low-overhead routing.
*Entry points:* [routers.py#L8-L46](file:///Users/<user-name>//Documents/core-apps-django/core/utils/routers.py#L8-L46).

---

## 7. OPERATIONAL PROCEDURES THAT ALREADY EXIST

| Procedure | Location | How Invoked | What It Protects Against |
| :--- | :--- | :--- | :--- |
| **Granular Database Dump** | [sample_project/compose/local/database/scripts/pg_dump.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/pg_dump.sh) | `make db-dump [DB_NAME=<name>]` | Exports single DB (`.dump` via `pg_dump -Fc`) or all DBs (`pg_dumpall`). Protects against data loss during schema migrations or development experiments. |
| **Granular Database Restore** | [sample_project/compose/local/database/scripts/pg_restore.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/pg_restore.sh) | `make db-restore BACKUP_FILE=<file> [DB_NAME=<name>]` | Restores database schema and records from archive into target database. Protects against failed deployments and bad migrations. |
| **Database Deletion** | [sample_project/compose/local/database/scripts/pg_delete.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/pg_delete.sh) | `make db-delete [DB_NAME=<name>]` | Terminates active backend client connections and drops database(s). Prepares clean slate before restores. |
| **Volume Snapshot Archive** | [sample_project/compose/local/database/scripts/volume_dump.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/volume_dump.sh) | `make db-volume-dump` | Automatically stops Postgres container to prevent WAL inconsistency, archives raw `postgres_data` volume to `.tar.gz`, and restarts container. Protects against volume corruption. |
| **Volume Snapshot Restore** | [sample_project/compose/local/database/scripts/volume_restore.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/volume_restore.sh) | `make db-volume-restore BACKUP_FILE=<tar_gz>` | Stops Postgres container, extracts archive into volume, and restarts container. Fast all-or-nothing recovery. |
| **Dev Tenant Seeding** | [add_dev_tenants.py](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/management/commands/add_dev_tenants.py) | `make seed-tenants` | Creates default public and dev tenant schemas and maps domains from `tenants.json`. Prevents missing-tenant crashes in local development. |
| **Dev Model Seeding** | [run_dev_seeders.py](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/management/commands/run_dev_seeders.py) | `make seed-models` | Autodiscovers dev seeders and fixtures, builds dependency DAG, and seeds models across schemas. Bootstraps consistent dev state. |
| **Tenant Migration Runner** | [common.mk#L221-L224](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L221-L224) | `make ms` | Executes `python manage.py migrate_schemas`. Ensures schema-isolated models are migrated uniformly across all tenant schemas. |
| **Celery Cron OCR Batch** | [core/apps/crm/tasks.py#L131](file:///Users/<user-name>//Documents/core-apps-crm/core/apps/crm/tasks.py#L131) | Designed for Celery Beat (`process_unverified_identifications_cron`) | Scans unverified KYC documents in batches (default 50). Prevents queue overload from concurrent manual OCR tasks. |
| **Data Migration Scripts** | `sample_project/db_migrations/` | Via `make m` / `make ms` | **NOT FOUND** as a separate arbitrary data migration runner outside Django standard migrations. |
| **Tenant Cloning** | N/A | N/A | **NOT FOUND** in codebase. |
| **CI Configuration** | N/A | N/A | **NOT FOUND**. `.github/workflows` does not exist in repository. |
| **Release / Versioning Process** | [version.py](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/version.py#L35) | `bump_version()` on records | **NOT FOUND** for automated package publishing. Record-level semantic versioning exists. |

---

## 8. TESTING SETUP

### Test Database Handling
- Test database settings are declared in [core/config/settings/test.py#L17-L30](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/test.py#L17-L30):
  ```python
  DATABASES = {
      "default": {
          "ENGINE": "django_tenants.postgresql_backend",
          "NAME": "pytest_db",
          "TEST": {"NAME": "pytest_db", "TEMPLATE": "template1"},
      }
  }
  ```
- Fast execution optimizations:
  - Password hashing uses MD5: `PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]` ([test.py#L72](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/test.py#L72)).
  - Cache uses memory backend: `LocMemCache` ([test.py#L59](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/test.py#L59)).
  - Constance uses memory backend: `constance.backends.memory.MemoryBackend` ([test.py#L63](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/test.py#L63)).
  - Runner flag `--reuse-db` is configured in `pyproject.toml` ([pyproject.toml#L81](file:///Users/<user-name>//Documents/core-apps-django/pyproject.toml#L81)).

### Factory Conventions: Documented vs. Observed
- **Documented:** [AGENTS.md#L182-L183](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L182-L183) mandates: *"Never mock database objects. Create real instances with factories (`factories.py`). If no factory exists, create one."*
- **Observed:** `factory-boy` (v3.3.3) is locked in `poetry.lock`, but **no `factories.py` files exist for domain models in `core/apps/`**. Tests directly invoke Django ORM methods (`Model.objects.create(...)`) or seed fixtures. `factory` is only referenced as a type hint in [core/libraries/seeder/loaders/static.py#L18](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/loaders/static.py#L18).

### Tenant Isolation Testing: Documented vs. Observed
- **Documented:** [AGENTS.md#L185](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L185) requires validating that data created in tenant A is not visible in tenant B.
- **Observed:** [core/tests/conftest.py#L20-L72](file:///Users/<user-name>//Documents/core-apps-django/core/tests/conftest.py#L20-L72) provides session fixture `django_db_setup` which provisions tenant schema `test_schema` (or `test_core`) once per session outside per-test transaction boundaries, avoiding deadlocks on `tenants_tenants_schema_name_key`. An autouse fixture `tenant_schema` switches context to `test_schema`. However, **no dedicated multi-tenant isolation assertions (verifying tenant cross-leakage) exist**; tenant switching is only tested with mocks in [test_celery_tasks.py#L46-L70](file:///Users/<user-name>//Documents/core-apps-django/core/tests/test_celery_tasks.py#L46-L70).

### Celery Eager Configuration
- Configured in [core/config/settings/test.py#L49-L50](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/test.py#L49-L50):
  ```python
  CELERY_TASK_ALWAYS_EAGER = True
  CELERY_TASK_EAGER_PROPAGATES = True
  ```
  Tasks execute synchronously on the caller process during test runs, and exceptions surface immediately.

### On-Commit Capture Helper: Documented vs. Observed
- **Documented:** [AGENTS.md#L186-L187](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L186-L187) instructs: *"Use your test framework's on-commit capture helper, because plain test transactions never commit."*
- **Observed:** **NOT FOUND**. Neither `django_capture_on_commit_callbacks` nor `captureOnCommitCallbacks` is used in any test file. Tasks are either executed synchronously or mocked via `unittest.mock`.

### Coverage & Flaky Areas
- **Coverage Configuration:** **NOT FOUND**. No `.coveragerc` or `tool.coverage` block exists in `pyproject.toml`.
- **Markers & Flakiness:** Markers `slow`, `integration`, `unit`, and `celery` are defined in [pyproject.toml#L86-L91](file:///Users/<user-name>//Documents/core-apps-django/pyproject.toml#L86-L91), but are not applied across tests. Only `@pytest.mark.django_db` and `@pytest.mark.parametrize` are used.

---

## 9. GOTCHAS AND DEBT

### TODO / FIXME / HACK / Workaround Inventory (Grouped by App)

```
config (3):
  core/config/settings/test.py:84: # TODO: Not sure about this setting, need to revisit this
  core/config/settings/base.py:269: # TODO: Encrypt and put these in database (GOOGLE_AUTH_CLIENT_ID)
  core/config/settings/base.py:305: # django-mail TODO: Work on email backends

configurations (2):
  core/apps/configurations/models_abstract.py:142: # TODO: Implement JSONSchema Validators and avoid this pattern going forward.
  core/apps/configurations/Readme.md:67: Executable via make target: `make dev-setup`

crm (4):
  core/apps/crm/tasks.py:4: # TODO: Document scanning is a Celery Beat cron-scheduled batch task
  core/apps/crm/tasks.py:114: # TODO: This task should not be manually queued per upload; once Celery Beat is configured...
  core/apps/crm/models_abstract/customer_identification.py:61: # TODO: In Documents app create regulatory models like: Aadhar, SocialSecurity, PAN, etc.
  core/apps/crm/Readme.md:107: > **TODO:** Document scanning is a periodic Celery Beat cron-scheduled batch task...

integrations (3):
  core/apps/integrations/email/Readme.md:3: TODO: purpose, models, settings, public API.
  core/apps/integrations/sms/Readme.md:3: TODO: purpose, models, settings, public API.
  core/apps/integrations/payments/Readme.md:3: TODO: purpose, models, settings, public API.

seeder / libraries (3):
  core/libraries/seeder/methods/base.py:182: temporary probe instance with non-relation fields
  core/seeder/constants.py:86: # TODO: allow_null here needs better handling, we might need to delay creation
  core/seeder/runners.py:147: # TODO: Time Coplexity for this comaprison can be imporved by pre-builing a dict/map

templates (1):
  core/templates/core/layout/navbar.jinja:6: {# TODO: figure out a better way to implement, mobile view #}

users (5):
  core/apps/users/tasks.py:32: # TODO: Implement custom LocalMemCache backend for tests, and then avoid this nullcontext(...)
  core/apps/users/tasks.py:63: # TODO: Implement custom LocalMemCache backend for tests, and then avoid this nullcontext(...)
  core/apps/users/services/otp/email.py:29: # TODO: Build out email service, that sends email's from template's and effectively.
  core/apps/users/services/otp/sms.py:35: # TODO: Build out sms service, that sends email's from template's and effectively
  core/apps/users/services/social/google.py:25: # TODO: Use encrypted credentials from database instead of plain creds from django-settings.

utils (8):
  core/utils/app_settings/base.py:50: # TODO: later will be used in django-admin
  core/utils/app_settings/base.py:238: # TODO: Implement autodiscovery of ErrorCodes Loading from error files
  core/utils/models/soft_delete.py:17: # TODO: Handle bulk_delete, after some-stability prevent soft-delete without user.
  core/utils/models/model_bases.py:7: # TODO: Design a better versioning model and then deperecate this file
  core/utils/models/model_bases.py:56: # TODO: Don't like this method, this could be better
  core/utils/models/abstracts.py:21: # TODO: Implement dynamic properties loader for django models
  core/utils/models/helpers.py:13: # TODO: write an automated tests for this method
  core/utils/models/versioning.py:10: # TODO: Need to work on this, and write tests for this method
```

### Hard Rule Violations in Code

1. **Direct Concrete Model Imports:**
   - [core/apps/tenants/api/views.py#L6](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/api/views.py#L6): `from core.apps.tenants.models import TenantBranding` *(Violates rule: Never import concrete models directly; use `get_tenant_branding_model()`)*.
   - [core/tests/invoices/test_views.py#L12](file:///Users/<user-name>//Documents/core-apps-django/core/tests/invoices/test_views.py#L12): `from core.apps.invoices.models import InvoiceAddress, InvoiceItemEntry`.
   - [core/apps/tenants/tasks.py#L11](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/tasks.py#L11): `from .models import Tenants` (guarded under `if typing.TYPE_CHECKING:`).

2. **Direct `.delay()` or `.apply_async()`:**
   - 0 occurrences in domain apps. All task dispatching uses `queue_task` or internal wrappers.

3. **Inline Imports Inside Methods (violating PLC0415 / 4.1):**
   - 27 occurrences in core framework code, including [core/config/celery/base.py#L46](file:///Users/<user-name>//Documents/core-apps-django/core/config/celery/base.py#L46), [core/config/logging/\_\_init\_\_.py#L86-L92](file:///Users/<user-name>//Documents/core-apps-django/core/config/logging/__init__.py#L86-L92), [core/backends/email/sendgrid.py#L94](file:///Users/<user-name>//Documents/core-apps-django/core/backends/email/sendgrid.py#L94), [core/utils/models/base_models/base.py#L35](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/base_models/base.py#L35), and [core/utils/app_settings/base.py#L65](file:///Users/<user-name>//Documents/core-apps-django/core/utils/app_settings/base.py#L65). Most are used to avoid circular dependencies during app population.

4. **Getattr Fallback Ladders:**
   - 0 occurrences of nested `getattr(a, x, getattr(b, y))` chains found.

5. **Inline JS in Templates:**
   - [core/templates/core/base.jinja#L28](file:///Users/<user-name>//Documents/core-apps-django/core/templates/core/base.jinja#L28)
   - [core/templates/core/views/authenticated_view.jinja#L39](file:///Users/<user-name>//Documents/core-apps-django/core/templates/core/views/authenticated_view.jinja#L39)
   - [core/templates/core/views/authenticated_view.jinja#L55](file:///Users/<user-name>//Documents/core-apps-django/core/templates/core/views/authenticated_view.jinja#L55)

6. **Hardcoded Colors in Templates:**
   - [core/templates/core/views/auth/username_login.jinja#L71-L94](file:///Users/<user-name>//Documents/core-apps-django/core/templates/core/views/auth/username_login.jinja#L71-L94): Hardcoded hex color fills on SVG icons (`#EA4335`, `#4285F4`, `#FBBC05`, `#34A853`, `#1877F2`).

---

## 10. DOCS INVENTORY

### Readme.md Files (21)
1. [./Readme.md](file:///Users/<user-name>//Documents/core-apps-django/Readme.md): High-level architectural overview and local docker quickstart; slightly stale (references non-existent `.github/`).
2. [./docs/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/docs/Readme.md): Explains agent context rules and memory guidelines for `docs/`; current.
3. [./core/templates/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/templates/Readme.md): Architecture guide for Jinja2 templates, CSRF handling, and frontend design tokens; current.
4. [./core/seeder/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/seeder/Readme.md): Documents the legacy `core.seeder` implementation; explicitly marked legacy as codebase migrates to `core.libraries.seeder`.
5. [./core/libraries/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/Readme.md): High-level index of decoupled framework libraries; current.
6. [./core/libraries/seeder/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/Readme.md): Complete modern seeder documentation covering DAG builder, loaders, and runners; current.
7. [./core/utils/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/Readme.md): Quick reference index for all utilities under `core.utils`; current.
8. [./core/utils/app_settings/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/app_settings/Readme.md): Low-level design for `BaseSettings`, descriptors, and type safety; current.
9. [./core/utils/datatypes/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/datatypes/Readme.md): Detailed documentation for pointer-based `Queue` and `DirectedGraph` topological sort; current.
10. [./core/utils/models/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/models/Readme.md): Overview of `BaseModel`, soft-delete, versioning, and abstract models; current.
11. [./core/utils/error_handling/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/error_handling/Readme.md): Content masking and exception hierarchy documentation; current.
12. [./core/utils/serializers/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/serializers/Readme.md): Dynamic read-only serializers and utility classes; current.
13. [./core/apps/configurations/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/configurations/Readme.md): Architectural spec for runtime configurations and JSONSchema storage; current.
14. [./core/apps/crm/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/crm/Readme.md): Complete CRM domain documentation covering models, nested routers, and OCR pipeline; current.
15. [./core/apps/invoices/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/invoices/Readme.md): Invoicing data model, party relations, calculations, and endpoints; current.
16. [./core/apps/tenants/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/tenants/Readme.md): Schema lifecycle, async provisioning, domain mapping, and branding; current.
17. [./core/apps/users/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/users/Readme.md): Detailed auth guide covering OTP state machine, lockout policies, and Google auth; current.
18. [./core/apps/integrations/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/integrations/Readme.md): Framework guide for third-party service credential adapters; current.
19. [./core/apps/integrations/email/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/integrations/email/Readme.md): Email subapp stub; **stale** (contains only `TODO`).
20. [./core/apps/integrations/sms/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/integrations/sms/Readme.md): SMS subapp stub; **stale** (contains only `TODO`).
21. [./core/apps/integrations/payments/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/apps/integrations/payments/Readme.md): Payments subapp stub; **stale** (contains only `TODO`).

### Documentation Under `docs/` (11 Files)
1. [docs/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/docs/Readme.md): Memory architecture and maintenance rules for AI agent logs; current.
2. [docs/configurations/database-label-configuration-and-seeder.md](file:///Users/<user-name>//Documents/core-apps-django/docs/configurations/database-label-configuration-and-seeder.md): Plan and execution log for multi-language database labels and fixture seeders; current.
3. [docs/database/postgres-pg-dump-reference.md](file:///Users/<user-name>//Documents/core-apps-django/docs/database/postgres-pg-dump-reference.md): Technical reference guide for PostgreSQL logical dumps and volume snapshots; current.
4. [docs/integrations/analysis.md](file:///Users/<user-name>//Documents/core-apps-django/docs/integrations/analysis.md): Architectural spec for integrations framework and backend adapters; current.
5. [docs/seeder/migrate-seeder-to-libraries.md](file:///Users/<user-name>//Documents/core-apps-django/docs/seeder/migrate-seeder-to-libraries.md): Migration tracking log moving seeder engine from `core/seeder` to `core/libraries/seeder`; current.
6. [docs/templates/login-page-and-form-templates.md](file:///Users/<user-name>//Documents/core-apps-django/docs/templates/login-page-and-form-templates.md): Architecture analysis for lean server-side Jinja2 login forms; current.
7. [docs/templates/template-fixes.md](file:///Users/<user-name>//Documents/core-apps-django/docs/templates/template-fixes.md): Quality audit and security refactoring log for template assets; current.
8. [docs/users_and_auth/api-urls-and-template-views.md](file:///Users/<user-name>//Documents/core-apps-django/docs/users_and_auth/api-urls-and-template-views.md): Routing analysis for user authentication templates and endpoints; current.
9. [docs/users_and_auth/authenticated-view-and-modular-login.md](file:///Users/<user-name>//Documents/core-apps-django/docs/users_and_auth/authenticated-view-and-modular-login.md): Refactoring log for authenticated views and account lockout; current.
10. [docs/users_and_auth/landing-page-routing-post-login.md](file:///Users/<user-name>//Documents/core-apps-django/docs/users_and_auth/landing-page-routing-post-login.md): Session redirect handling post-login; current.
11. [docs/users_and_auth/otp-signup-flow-corrections.md](file:///Users/<user-name>//Documents/core-apps-django/docs/users_and_auth/otp-signup-flow-corrections.md): Edge cases and fixes for OTP registration flow; current.

---

## 11. USER-SPECIFIED WORKFLOW REQUIREMENTS

| Requirement | Status | Evidence Paths & Details |
| :--- | :--- | :--- |
| **Take a DB backup before executing a feature or running migrations** | **Exists in code & tools; NOT FOUND as an enforced workflow step** | The backup tooling is fully implemented in [scripts/common.mk#L150-L202](file:///Users/<user-name>//Documents/core-apps-django/scripts/common.mk#L150-L202) (`make db-dump`, `make db-volume-dump`), [pg_dump.sh](file:///Users/<user-name>//Documents/core-apps-django/sample_project/compose/local/database/scripts/pg_dump.sh), and documented in [docs/database/postgres-pg-dump-reference.md](file:///Users/<user-name>//Documents/core-apps-django/docs/database/postgres-pg-dump-reference.md). However, making this a mandatory pre-condition before migrations or feature execution is **NOT mentioned** in [AGENTS.md](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md). |
| **Data from a feature goes in fixtures for production, seed JSONs for local testing** | **Exists in code & Mentioned in docs** | Explicitly codified in [.agents/skills/add-seeder/SKILL.md#L30-L53](file:///Users/<user-name>//Documents/core-apps-django/.agents/skills/add-seeder/SKILL.md#L30-L53) and [core/libraries/seeder/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/Readme.md). Production fixtures use `is_fixture=True` in `core/apps/<app>/fixtures/` run via `SeedFixtures`; dev mock data uses `is_fixture=False` in `core/setup/<app>/` run via `make seed-models` (`run_dev_seeders`). |
| **Settings / Dynamic values come from `app_settings` (app-specific in `app_settings`, project-wide only in `settings.py`)** | **Exists in code & Mentioned in docs** | Codified in [AGENTS.md#L254-L285](file:///Users/<user-name>//Documents/core-apps-django/AGENTS.md#L254-L285) and [core/utils/app_settings/Readme.md](file:///Users/<user-name>//Documents/core-apps-django/core/utils/app_settings/Readme.md). App-specific settings live in `core/apps/<app>/app_settings.py` via `BaseSettings` descriptors. Documented in [core/config/settings/base.py#L317-L318](file:///Users/<user-name>//Documents/core-apps-django/core/config/settings/base.py#L317-L318): *"Avoid adding anything to these set them in app_settings. If the setting is to be made app_wide then only add it here."* |
| **Use registries to provide decoupled extension to logic (`utils/registries`)** | **Exists in code & Mentioned in docs** | Implemented as `ClassRegistry` and `UnorderedClassRegistry` in [core/utils/registry/class_registry.py#L8-L167](file:///Users/<user-name>//Documents/core-apps-django/core/utils/registry/class_registry.py#L8-L167). Also implemented as runtime dynamic choices in [core/utils/lazy_objects.py#L50](file:///Users/<user-name>//Documents/core-apps-django/core/utils/lazy_objects.py#L50) (`LazyDynamicChoiceTypes`) and seeder registries in [core/libraries/seeder/registry.py](file:///Users/<user-name>//Documents/core-apps-django/core/libraries/seeder/registry.py#L1-L15) (`seeder_registry`, `fixture_registry`). |

---

12. QUESTIONS FOR ME
  1. Should templates live in this repo, I am not statisfied with current state of templates.
  2. PR template for this repo.

---

FINAL LINE:
I did not run tests, migrations, docker compose commands, or touch the database (strictly read-only inspection as requested). The section with the lowest confidence is Section 8 regarding flaky tests, because no test executions or CI run logs were observed to measure runtime duration or failure frequency directly.
