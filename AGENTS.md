# AGENTS.md — Developer & AI Agent Context Guide

Architectural patterns, coding standards, and workflows for AI agents and developers working on this codebase.

## 1. Overview & Hard Rules

This repository is a reusable, production-ready Django core framework, typically consumed as a submodule or base package. It emphasizes modularity, multi-tenant isolation, swappable model declarations, and decoupled configuration.

### Directory Structure

```
├── core/
│   ├── utils/                   # Reusable cross-app framework utilities
│   │   ├── app_settings/        # Descriptor-based settings & configuration engine
│   │   ├── error_handling/      # Sensitive data masking & domain exceptions
│   │   ├── generators/          # Algorithmic strategy generators (username, tokens)
│   │   ├── models/              # Abstract base models, soft-delete, versioning mixins
│   │   ├── serializers/         # Base read-only and permission-based DRF serializers
│   │   ├── checks.py            # Runtime environment & multi-tenant checks
│   │   ├── file_handling.py     # Dynamic module loading & introspection
│   │   ├── lazy_objects.py      # Runtime lazy choice registries
│   │   ├── routers.py           # Environment-aware API routing
│   │   └── tasks.py             # Standardized Celery task queueing wrapper (queue_task)
│   └── apps/                    # Modular, swappable core apps
│       └── <app_name>/          # Structured domain modules
├── sample_project/              # Reference host project and integration templates
└── scripts/                     # Operational and development utilities
```

### Hard Rules (never violate)

Each rule is explained in the section named in brackets.

- **Never** import concrete models directly. Use the model getters. [4.2]
- **Never** call `.delay()` / `.apply_async()` directly. Use `queue_task()`. [4.7]
- **Never** run external calls or network I/O on the HTTP request thread. [4.4]
- **Never** instantiate a settings class inside `app_settings.py`. [4.3]
- **Never** override core settings (`CORE_BASE_DIR` etc.) to suit a host project. [4.3]
- **Never** hardcode colors/spacing in templates or write inline JS. [4.8]
- **Never** put `unittest.mock` imports or `if testing:` branches in production code. [3, Phase 4]
- **Never** fix a stale migration or the test DB yourself, and never delete or re-create the test DB. Report it and wait. [3, Phase 4]
- **Never** run plain `poetry`, `pytest`, or `docker` commands for tests. Use the `make` targets. [3, Phase 4]
- **Never** bypass pre-commit hooks. [3, Phase 4]
- **Never** log secrets or PII. Route PII-bearing data through `ContentMaskingUtils`. [3, Phase 2]

### Precedence

If instructions conflict: Hard Rules > the Phase workflow in section 3 > section 4 design norms > section 7 (Ponytail). Ponytail decides _how little code to write_ inside the workflow. It never skips the analysis, review gate, tests, or pre-commit steps.

## 2. Codebase Navigation Guide

Explore in this order and stop as soon as you have enough context:

1. **graphify**: for a module overview, use graphify instead of scanning files (see section 6).
2. **Module docs (`Readme.md`)**: most subpackages have a concise `Readme.md` covering architectural role, key models, and usage. Read it if it exists.
3. **App settings (`app_settings.py`)**: declared settings, type validation, default strategies, `Constance` flags, `Configuration` bindings.
4. **Constants & registries (`constants.py` / `interfaces/`)**: enumerations, status choices, and choices registered into `LazyDynamicChoiceTypes`.
5. **Abstract models (`models_abstract.py`)**: the actual business logic, managers, `clean` methods, lifecycle hooks.
6. **Concrete models (`models.py`)**: swappability (`swappable = "APP_MODEL_KEY"`).
7. **Tasks (`tasks.py`)**: background jobs, schema migration tasks, Celery routines.
8. **API surface (`api/serializers.py`, `api/views.py`, `urls.py`)**: endpoints, serializers, viewsets, permissions.
9. **Templates & frontend (`core/templates/`, `<app>/templates/`)**: read `core/templates/Readme.md` before any template or frontend change (see 4.8).

## 3. Four-Phase Development Lifecycle

Plan all non-trivial logic additions and refactors across these phases, in order. Do not start a phase before the previous one is done.

### Phase 1: Analysis (the `What` phase)

**Use:** the first phase for every new requirement, including plan mode and `/plan`.
**Goal:** identify what needs to be built and which restrictions or blockers affect it.
**Do not write implementation code in this phase.** Reading existing code is fine.

**Workflow**

1. Create a log at `docs/analysis/<feature-slug>.md` before analyzing.
2. Iterate as needed. After each iteration, edit the log in place: improve it, compact it, and remove superseded notes instead of appending.
3. After each iteration, present a short plan summary and the open points that need discussion, each with your recommendation. Then **stop and wait for user feedback.**
4. After the final iteration, use the log to build the task and document it (docstrings or `Readme.md`).

**1. System analysis**

- Before deciding "existing vs new", run `graphify query` to find existing models, tasks, crons, and patterns (see section 6). Do not guess from memory.
- Input data (structure, type), input source (API call, cron job, async task), and output contract (database, API response).
- Does the task need any of the following?
  - Caching (frequently accessed data)
  - Async tasks (long-running or external-I/O-dependent work)
  - Database changes
  - Cron scheduling (periodic or event-based runs)
- Database: can existing models be used, or do we need new ones? When planning new models, consider the expected queries and the volume of data going into each table.
- Async tasks and crons: do suitable ones already exist, or do we need new ones?
- Architecture: can an existing pattern be used, or does this need something new? If new, justify why.

**2. Data analysis**

- Missing or invalid data: raise an exception, roll back the transaction, or only log the failure?
- Retries: is active retry logic needed? If so, define the mechanism, max attempts, backoff, and what happens when retries are exhausted.
- Errors: what is logged, at what level, and with what context?
- Exceptions: reuse existing ones first (`core/utils/error_handling/exceptions.py`, then Django/DRF built-ins). Propose a new exception only if none fit.

**3. Thread & process state awareness**

- **Main request thread:** HTTP lifecycle. Must stay lightweight. Never run blocking I/O, heavy computation, or schema migrations here.
- **Worker threads:** Celery tasks handle background processing, heavy migrations, and external API integration.
- **Schema context:** multi-tenant schema switching uses `schema_context(schema_name)`. Celery tasks do not inherit the request's schema, so pass the schema name explicitly.
- **Transaction boundaries:** plan `transaction.atomic()` blocks. Dispatch side effects (tasks, emails, webhooks) through `queue_task` (4.7) so they fire only after commit.

**Done when:** every item above is answered (or marked N/A with a reason) and the user has approved the plan.

### Phase 2: Logical Writing (the `How` phase)

Start only after the Phase 1 plan is approved. If a requirement is missing or unclear, go back to Phase 1 instead of guessing. Write clean, self-contained logic for the approved plan and add no scope beyond it.

- **Scaffolding:** use `make start-app` to create a new app. See 4.1 for file layout.
- **Fail fast:** validate parameters and data types at the top of each function and raise early, using the exceptions chosen in Phase 1. Do not let bad input travel deep into the logic.
- **Order of execution:** handle cheap, frequent paths first (early returns, simple field checks, cached lookups) before expensive branches such as M2M or reverse relations. Do not run extra queries for data the common path never uses.
- **Query discipline:** avoid N+1 queries. Use `select_related` / `prefetch_related` for reads and `bulk_create` / `bulk_update` for batch writes.
- **Side effects:** dispatch tasks, emails, and webhooks through `queue_task` (4.7). Pass IDs or serialized data to tasks, never model instances.
- **Logging:** log failures with enough context to debug (IDs, schema name). Never log secrets or PII. Route data expected to contain PII through `ContentMaskingUtils`.

**Done when:** the logic satisfies the approved plan, handles the failure cases decided in Phase 1, and runs without errors. Polish belongs to Phase 3.

### Phase 3: Refactor

Refactor only after the logic works. Behavior must not change: run the existing tests before and after, and add tests first if the code has none.

- Follow section 7 (Ponytail): make the smallest complete change, and before touching shared code, find every caller (use `graphify path` / `graphify explain` first, then grep) and fix the root cause once.
- Break monolithic logic into single-responsibility helper functions or service classes. Rule of thumb: if a function needs "and" to describe it, split it.
- Apply DRY and OO principles. Encapsulate specialized field handling (password hashing, file uploads) in one place (model method, service, or custom field) so every caller gets the same behavior.
- Keep functions pure where practical: separate validation (no side effects, returns or raises) from mutation (DB writes, external calls).
- Do not abstract early. Extract a helper when duplication is real (about the third occurrence) or it isolates a distinct responsibility. Do not build a framework for a single use.
- Keep the public interface (signatures, API contracts) stable unless the approved plan says otherwise.

**Done when:** tests pass, no logic is duplicated, each function has one responsibility, and docstrings reflect final behavior.

### Phase 4: Testing & Quality

Start only after Phase 3. Tests describe the behavior in the approved Phase 1 plan, including its failure cases.

**Test design**

- Run the full workflow end to end. Mock/patch only external APIs and I/O boundaries (HTTP calls, file storage, email/SMS gateways). Never mock internal services, helpers, or the ORM.
- Never mock database objects. Create real instances with factories (`factories.py`). If no factory exists, create one.
- Celery tasks: run them eagerly when verifying the workflow (e.g. `CELERY_TASK_ALWAYS_EAGER`; confirm against this project's test settings). Mock a task only when it calls an external API or I/O boundary.
- Multi-tenant code: validate schema isolation (data created in tenant A must not be visible from tenant B).
- Cover the Phase 1 paths: happy path, each missing/invalid-data case (assert the exact exception), retry behavior, and post-commit side effects (fire only after commit, never on rollback). Use your test framework's on-commit capture helper, because plain test transactions never commit.
- Group related tests under classes. Name tests for behavior (`test_raises_when_schema_missing`), not for the function.

**Running tests** (always the make targets, never plain `poetry`, `pytest`, or `docker`)

| Command                                      | Runs           |
| -------------------------------------------- | -------------- |
| `make t` / `make test`                       | all tests      |
| `make t DIR=<path>` / `make test DIR=<path>` | one directory  |
| `make tf TEST_FILTER=<expr>`                 | filtered tests |

Use the narrowest target while iterating, then the full suite before finishing.

**Migrations & test database (hard rules)**

- Never fix a stale migration or database yourself. Never delete or re-create the test DB.
- If tests fail from a stale migration or table, **stop and report**: which migration or table is stale, the evidence (error message, missing column), and the suggested fix. Then wait for the user to apply it.

**No `Mock` in production logic (anti-pattern)**

- Production framework code (`BaseMeta`, `BaseSeeder`, descriptors, managers) must never import `unittest.mock` or check `isinstance(..., Mock)`.
- Production validation must enforce genuine domain types, e.g. `isinstance(model, type) and issubclass(model, models.Model)`.
- If a test cannot satisfy that validation, fix the test with a real model or factory. Do not loosen production code, and do not add `if testing:` or settings-based branches.

**Pre-commit verification**

- `pre-commit` is the only command allowed to run on the host machine, outside the container.
- After changes, run `poetry run pre-commit run --all-files`.
- All hooks (Black, isort, flake8, whitespace, YAML check) must pass with zero errors. If a hook auto-fixes files, rerun until clean.
- Never bypass hooks (`--no-verify`, skipping hooks, disabling a lint rule). Fix the cause, or ask the user if a rule genuinely needs an exception.

**Done when:**
- all tests pass via the make targets, no mocks are used outside external API/I/O boundaries, pre-commit is clean, and the final report states what was tested, what was not, and any stale migration/DB issue waiting on the user.
- `graphify update .` has been run after code changes (see section 6).

## 4. Key Design Norms & Architectural Rules

### 4.1 App Structure & File Conventions

- App-wide settings go in `app_settings.py`.
- Models are built as abstracts in `models_abstract.py`. If an app has many models, split into `models_abstract/<model_name>.py`. Only swappable concretes go in `models.py`.
- Factories go in `factories.py` and admin classes in `admin.py`.
  - Public apps register admin on `public_admin_site`.
  - Tenant apps register admin on `private_admin_site`.
- Keep imports at module level. Use inline imports only to break an unavoidable circular dependency.

### 4.2 Models (`models_abstract.py` & `models.py`)

> Abstract models define all fields, managers, clean methods, and business logic. Concrete models subclass them, add no new fields, and declare swappability (`swappable = "APP_MODEL_KEY"`).

- **Never import concrete models directly** (`from core.apps.users.models import User`, `from .models import Invoice`). Direct imports bind logic to a concrete class at load time, bypass Django's swappable mechanism, and break overrides in consuming projects.
- **Use dynamic model getters.** Every modular app exports getters from its root `__init__.py` (`get_user_model()`, `get_customer_model()`, `get_invoice_model()`), backed by `django.apps.apps.get_model(settings.<APP>_<MODEL>_MODEL, require_ready=False)`. Serializers, viewsets, admin, tasks, managers, and services must resolve models through them.
- **Resolve once, at module level:** `User = get_user_model()`. Never call a getter repeatedly inside `validate_*()`, `save()`, view actions, or loops.

  ```python
  from core.apps.users import get_user_model

  User = get_user_model()
  ```

- **Type annotations:** import abstract classes under `typing.TYPE_CHECKING` and use quoted annotations. This gives IDE support without premature imports or cycles.

  ```python
  import typing

  if typing.TYPE_CHECKING:
      from core.apps.users.models_abstract import AbstractUser

  def process_user(user: "AbstractUser") -> None: ...
  ```

- **Foreign keys:** reference models by settings string (`to=settings.AUTH_USER_MODEL`, `to=settings.CRM_CUSTOMER_MODEL`). Never pass a concrete class to `models.ForeignKey()`.
- **No multi-table inheritance.** `class Child(ParentModel)` adds joins and migration complexity. Use one concrete table per entity with discriminator fields (`type`, `sub_type`, `status`) and abstract mixins for shared behavior.
- **Base model hierarchy (`core.utils.models`):**
  - `BaseModel`: standard entities (UUID PK, timestamps, soft delete via `is_removed`, `removed_by`).
  - `BaseVersioningModel`: configuration/schema entities (`version_major/minor/patch`, `bump_version()`).
  - `BaseLogModel`: event/audit records (UUID PK, timestamps, choice-based `status`, `status_changed`).
  - `.delete()` soft-deletes by default (`is_removed=True`). Hard deletion requires explicit `soft=False`.

### 4.3 App Settings (`app_settings.py` & `__init__.py`)

> Declarative descriptors (`Settings`, `Constance`, `Configuration`) live on an app-specific `BaseSettings` subclass, instantiated as a shared singleton in the app's root `__init__.py`.

- **Define vs. instantiate:**
  - Only define `class <App>Settings(BaseSettings):` in `app_settings.py`. **Never** instantiate it there.
  - Instantiate the singleton in the app root `__init__.py`, so imports are always `from core.apps.<app> import app_settings`:

    ```python
    # core/apps/<app>/__init__.py
    from core.apps.<app>.app_settings import <App>Settings

    app_settings: <App>Settings = <App>Settings()
    ```

- **Descriptor lifecycle (PEP 487):** descriptor `__init__` runs _during_ class body execution, but `__set_name__(owner, name)` runs only _after_ the class body finishes.
  - Initialize defaults (`self.name = None`, `self.app_settings_key = None`) in `__init__`.
  - Never assume `self.app_settings_key` exists in exception handling during early `self.validate(self.default)` calls. Use `getattr(self, "app_settings_key", None)`.
- **Deferred model imports:** Django imports installed apps in `apps.populate()` before `apps.ready = True`. Descriptors using `SettingsType.DEFFERED_IMPORT` must handle `AppRegistryNotReady` gracefully so eager validation never crashes startup.
- **Descriptor types:**
  - `Settings`: static code configuration, lazy dotted imports (`SettingsType.IMPORT`, `SettingsType.DEFFERED_IMPORT`), model strings (`SettingsType.MODEL_IMPORT`), and primitives (`int`, `str`, `bool`).
  - `Constance`: live admin-editable flags backed by `django-constance`, with automatic fieldset registration.
  - `Configuration`: database-stored, versioned JSON settings resolved per `interface_type` and cached per schema context.
- **No heavy network dependencies:** adapters and descriptors must not require optional heavy packages. Prefer the standard library (`http.client` / `_http_client`) over `requests` for token verification.
- **Core directory isolation (`CORE_BASE_DIR`, `CORE_APP_DIR`, `CORE_SETUP_DIR`):**
  - Host projects define their own `BASE_DIR` and `APP_DIR`. Never override or hijack core settings to accommodate them.
  - Core-internal paths (fixtures, dev seeders, autodiscovery) must anchor to the core constants.
  - `FileDataSource` and `AutoDiscovery` must receive complete anchored paths, e.g. `FileDataSource(os.path.join(settings.CORE_APP_DIR, "crm/fixtures/..."))` or `AutoDiscovery(root_path=settings.CORE_APP_DIR)`, so a host project overriding `BASE_DIR` never breaks core fixtures, seeders, or module resolution.

### 4.4 Views & API (`api/views.py`, `api/serializers.py`)

> Views are thin HTTP dispatchers that delegate business logic to managers and services. Serializers validate request schemas and format output using dynamically resolved models.

- **Models and imports:** follow 4.1 and 4.2 (module-level getters, `TYPE_CHECKING` annotations, no inline imports).
- **Serializers:**
  - Always declare explicit `fields`. Never use `fields = "__all__"` on mutable entities.
  - Declare `read_only_fields = ["id", "created", "modified", ...]`.
  - Render choices with `serializers.CharField(source="get_<field>_display", read_only=True)`.
  - Expose model properties (`full_name`, totals) as read-only fields.
- **Views:**
  - Restrict `http_method_names` to what the domain needs.
  - Query `.available_objects` for soft-deletable models, with `select_related()` / `prefetch_related()` to prevent N+1.
  - For asynchronous state changes (e.g. OTP dispatch), return `status.HTTP_202_ACCEPTED` immediately. This avoids leaking entity existence and keeps request threads free.
  - **No synchronous external calls or network I/O on the request thread** (SMS, email, etc.). Queue them with `queue_task()`. If queuing fails, log the error only. Never fall back to a blocking external call in the request-response cycle.

### 4.5 URLs & Routers (`urls.py`)

- Register ViewSets on routers from `get_api_router_instance()` (`SimpleRouter` in production, `DefaultRouter` in development for browsable docs).
- Use kebab-case, pluralized resource paths with an explicit `basename`, e.g. `router.register("users", UserViewSet, basename="users")`.

### 4.6 Generators (`core/utils/generators/`)

> Cross-cutting generation strategies (usernames, tokens, codes) live in dedicated generator classes.

- Encapsulate generation state, fallback ladders, and normalization inside the class (e.g. `UsernameGenerator`).
- Provide an explicit `.generate(user_model=..., max_attempts=...)` method plus a functional helper (e.g. `generate_unique_username(...)`).
- Write thorough docstrings covering argument priority, normalization rules, and collision escalation.

### 4.7 Async Task Queuing (`core/utils/tasks.py`)

> Background jobs and external I/O dispatch go through Celery workers, wrapped by `queue_task()`.

- Always use `queue_task()`. Never call `.delay()` or `.apply_async()` directly.
- Keep `on_commit=True` (the default) so tasks run only after the database transaction commits.
- Pass a unique `idempotency_key` to prevent duplicate processing on worker retries or concurrent dispatches.
- Pass IDs or serialized data to tasks, never model instances, and pass the schema name explicitly in multi-tenant contexts.

### 4.8 Template-Driven Frontend (`core/templates/`)

- **Mandatory context:** read [`core/templates/Readme.md`](core/templates/Readme.md) before creating or modifying templates, macros, or static assets.
- **Engine:** Jinja2 (`.jinja`) for all application and domain UI views. Keep Django's default DTL only for Django Admin and the DRF browsable API.
- **Components:** build UI elements as reusable `{% macro %}`s with explicit default arguments, `extra_classes`, and `caller()` slots.
- **Namespacing:** core layout/components live in `core/templates/core/`. Domain templates live in `core/apps/<app>/templates/<app>/`. Never create un-namespaced root templates.
- **Design tokens:** never hardcode colors, spacing, or typography. Use tokens from `variables.css` (`var(--color-primary)`, `var(--spacing-md)`) to preserve multi-tenant white-labeling.
- **Interactivity:** use the centralized `Core` helpers in `core.js` and declarative data attributes (`data-sidebar-toggle`, `data-sidebar-mobile-toggle`, `data-modal-target`, `data-alert-dismiss`). Never write inline JavaScript (`onclick="..."`, ad-hoc DOM queries) in templates or macros.

## 5. Documentation Maintenance

Keep app-level `Readme.md` files in sync with code changes.

- **New features:** when adding models, settings, managers, or endpoints, update the app's `Readme.md`.
- **Fixes and refactors:** if the docs are outdated, update them in the same change.
- **Style:**
  - No large code dumps. Do not paste full class definitions or boilerplate.
  - Short and crisp: model relationships, architectural role, manager helpers, endpoints.
  - Minimal snippets, only for non-obvious integration or usage patterns.

## 6. graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:

- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## 7. Ponytail, lazy senior dev mode

You are a lazy senior developer. The best code is the code never written. You solve the whole problem with the least new code. End your reply with one or two lines: what you skipped or did not check, and any risk the user must know.

### Before you write

Read the task and the code it touches. List every place your change must reach: callers, tests, fixtures, config, exports. Check what your change could break for users: data it would destroy or expose, callers that stop working. That is scope. Extra features are not.

### The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line. A vague request ("build me X") gets the smallest version that does the core job.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change itself: finish every part the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config, boilerplate or "for later" code nobody asked for. Keep values in the form the platform already gives you. Deletion beats addition. Keep the structure the codebase already has: its layers, interfaces and conventions.
- The shortest working diff wins, once you know everything it must touch. A one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a loop, a parser, money or security, or a whole new script or app) leaves one small test or an assert-based self-check. Trivial changes need none.
- A shortcut with a known limit gets a code comment in this form: `shortcut: <the limit>, <when to upgrade>`.

Never cut: validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs, anything the user asked for.

(Yes, this file also applies to agents working on the ponytail repo itself. Especially to them.)
