# AGENTS.md — Developer & AI Agent Context Guide

This document defines the architectural patterns, coding standards, design strategies, and exploration workflows for AI agents and developers working on this codebase.

## 1. Repository Topology & Architectural Overview

The repository is designed as a reusable, production-ready Django core framework (typically consumed as a submodule or base package). It emphasizes modularity, multi-tenant isolation, swappable model declarations, and decoupled configuration.

### Directory Structure Pattern

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
│   │   └── tasks.py             # Standardized Celery task queueing wrapper
│   └── apps/                    # Modular, swappable core apps
│       └── <app_name>/          # Structured domain modules
├── sample_project/              # Reference host project and integration templates
└── scripts/                     # Operational and development utilities
```

## 2. File Scanning & Codebase Navigation Guide

When exploring or modifying modules across this repository, follow this systematic order:

1. **Check Module Documentation (`Readme.md`)**: Each subpackage maintains a concise `Readme.md` explaining its architectural role, key models, and usage patterns.
2. **Inspect App Settings (`app_settings.py`)**: Identifies declared settings, type validations, default strategies, runtime `Constance` flags, and dynamic `Configuration` bindings.
3. **Inspect Constants & Registries (`constants.py` / `interfaces/`)**: Review enumerations, status choices, and runtime choices registered into `LazyDynamicChoiceTypes`.
4. **Inspect Abstract Models (`models_abstract.py`)**: Abstract base classes contain the actual business logic, managers, clean methods, and lifecycle hooks.
5. **Inspect Concrete Models (`models.py`)**: Checks swappability settings (`swappable = "APP_MODEL_KEY"`).
6. **Inspect Tasks & Asynchronous Workers (`tasks.py`)**: Checks background jobs, schema migration tasks, and Celery worker routines.
7. **Inspect API Surface (`api/serializers.py`, `api/views.py`, `urls.py`)**: Identifies endpoints, serializers, viewsets, and permissions.
8. **Inspect Templates & Frontend Layer (`core/templates/`, `<app>/templates/`)**: Review `core/templates/Readme.md` before making any template or frontend changes to understand component macro conventions, Jinja2 environment bindings, and CSS variable styling rules.

## 3. Four-Phase Development Lifecycle

All non-trivial logic additions and refactors should be planned across four distinct phases:

### Phase 1: Analysis Phase

- **Input & Output Contracts**:
  - Define explicit data types. Use `typing.TYPE_CHECKING` for type-only model/class imports to avoid circular dependencies and premature app loading.
- **Missing Data & Validation Strategy**:
  - Raise domain exceptions ([`ObjectNotFound`](core/utils/error_handling/exceptions.py), [`InvalidTypeError`](core/utils/error_handling/exceptions.py)) or resolve pre-configured defaults from `constants.py` / dynamic database configurations.
- **Thread & Process State Awareness**:
  - **Main Request Thread**: HTTP lifecycle (must stay lightweight; never execute blocking I/O, heavy computation, or schema migrations here).
  - **Delegated Worker Threads**: Celery tasks for background processing, heavy migrations, or external API integration.
  - **Schema Context**: Multi-tenant database schema switching (`schema_context(schema_name)`).
  - **Transaction Boundaries**: Plan database transactions (`transaction.atomic()`) and defer side effects to transaction commits (`on_commit=True`).

### Phase 2: Logical Writing Phase

- Write clean, self-contained logic addressing functional requirements.
- **Fail Fast**: Check for missing parameters and unexpected data types at the beginning of functions.
- **Order of Execution**: Handle trivial, frequent execution paths first to minimize unnecessary CPU cycles before processing complex branch logic (e.g., M2M relations, reverse relations).

### Phase 3: Refactor Phase

- Break monolithic logic into modular, single-responsibility helper functions or service classes.
- Apply DRY and Object-Oriented Principles (encapsulate specialized field setters, e.g. passwords, files).
- Keep functions pure where practical, separating validation logic from mutation logic.

### Phase 4: Testing & Quality Phase

- Mock external APIs, I/O boundaries, and Celery tasks.
- **Never Accommodate `Mock` in Production Logic (Anti-Pattern)**:
  Production framework code (such as `BaseMeta`, `BaseSeeder`, descriptors, managers) must never import `unittest.mock` or check `isinstance(..., Mock)`. Production validation must enforce genuine domain types (`isinstance(model, type) and issubclass(model, models.Model)`). If needed, use real models or factories in tests instead of forcing production code to accept mock types.
- Validate multi-tenant schema isolation where applicable.
- **Pre-Commit Hooks Verification**:
  - Always run `poetry run pre-commit run --all-files` post changes.
  - Ensure all hooks (Black formatting, isort import sorting, flake8 linting, whitespace, YAML check) pass successfully with zero errors before considering any task complete.

## 4. Key Design Norms & Architectural Rules

### 1. Models (`models_abstract.py` & `models.py`)

> **Architecture in 1–2 Lines**:
> Abstract models (`models_abstract.py`) define all fields, managers, clean methods, and business logic. Concrete models (`models.py`) subclass abstract models, add no new fields, and declare swappability (`swappable = "APP_MODEL_KEY"`).

#### How to Work with Models

- **NEVER Import Concrete Models Directly**:
  - **Forbidden**: `from core.apps.users.models import User` or `from .models import Invoice`.
  - **Why?** Direct imports bind logic to specific concrete implementations at module load time, bypassing Django's swappable model mechanism (`swappable = "APP_MODEL_KEY"`) and breaking custom model overrides provided by consuming projects.
- **Dynamic Model Getters**:
  - Every modular app must define and export model getter functions in its root `__init__.py` (e.g., `get_user_model()`, `get_customer_model()`, `get_invoice_model()`) backed by `django.apps.apps.get_model(settings.<APP>_<MODEL>_MODEL, require_ready=False)`.
  - Serializers, ViewSets, admin classes, tasks, managers, and services must always resolve their models using these getter functions:
    ```python
    from core.apps.users import get_user_model

    User = get_user_model()
    ```
  - **Resolve at Module Level**: Assign `User = get_user_model()` once at module level in serializers, views, and services. Avoid calling `get_user_model()` repeatedly inside method bodies or loops.
- **Static Typing with `typing.TYPE_CHECKING`**:
  - Always use `if typing.TYPE_CHECKING:` to import abstract classes (e.g. `from core.apps.users.models_abstract import AbstractUser`) for type annotations. This guarantees full IDE auto-complete and static analysis without triggering premature runtime imports or circular dependencies:
    ```python
    import typing

    if typing.TYPE_CHECKING:
        from core.apps.users.models_abstract import AbstractUser

    def process_user(user: "AbstractUser") -> None: ...
    ```
- **Foreign Key Declarations**:
  - Always reference foreign models via settings strings (e.g., `to=settings.AUTH_USER_MODEL`, `to=settings.CRM_CUSTOMER_MODEL`). Never pass concrete classes directly to `models.ForeignKey()`.
- **No Multi-Table Inheritance (MTI)**:
  - Multi-table inheritance (`class Child(ParentModel)`) creates unnecessary joins and migration complexity.
  - Use a single concrete table per entity with discriminator fields (`type`, `sub_type`, `status`) and abstract mixins for shared behavior.
- **Base Model Hierarchy (`core.utils.models`)**:
  - Standard entities inherit from `BaseModel` (UUID PK, timestamps, soft delete: `is_removed`, `removed_by`).
  - Configuration/schema entities inherit from `BaseVersioningModel` (semantic versions `version_major/minor/patch`, `bump_version()`).
  - Event/audit records inherit from `BaseLogModel` (UUID PK, timestamps, choice-based `status`, `status_changed`).
  - `.delete()` soft-deletes rows by default (`is_removed=True`). Hard deletion requires explicit `soft=False`.

---

### 2. App Settings (`app_settings.py` & `__init__.py`)

> **Architecture in 1–2 Lines**:
> App settings define declarative descriptors (`Settings`, `Constance`, `Configuration`) on an app-specific `BaseSettings` class, instantiated as a shared singleton in the app's root `__init__.py`.

#### Rules & Descriptor Lifecycle Constraints

- **Class Definition vs. Initialization**:
  - **NEVER** instantiate the settings class inside `app_settings.py`. Only define the class `class <App>Settings(BaseSettings):` inside `app_settings.py`.
  - Instantiate the shared singleton inside the app root `__init__.py`:
    ```python
    # core/apps/<app>/__init__.py
    from core.apps.<app>.app_settings import <App>Settings

    app_settings: <App>Settings = <App>Settings()
    ```
  - This ensures a single shared instance with unambiguous import paths: `from core.apps.<app> import app_settings`.
- **Descriptor Lifecycle & Python Protocol (PEP 487)**:
  - In Python, descriptor `__init__` runs **during** the class body execution, whereas `__set_name__(owner, name)` is called by the metaclass **only after** the entire class body has finished executing.
  - Descriptors must initialize default attributes (`self.name = None`, `self.app_settings_key = None`) in `__init__`, and must **never** assume `self.app_settings_key` exists when handling exceptions in early `self.validate(self.default)` calls. Use `getattr(self, "app_settings_key", None)` safely.
- **Deferred Model Imports During App Population**:
  - When Django boots, `apps.populate()` imports installed apps before `apps.ready = True`.
  - Descriptors using `SettingsType.DEFFERED_IMPORT` must handle `AppRegistryNotReady` gracefully so eager validation does not crash startup when importing models or model mixins.
- **Supported Descriptor Types**:
  - `Settings`: Static code configurations, lazy dotted imports (`SettingsType.IMPORT`, `SettingsType.DEFFERED_IMPORT`), model strings (`SettingsType.MODEL_IMPORT`), and Python primitive types (`int`, `str`, `bool`).
  - `Constance`: Live admin-editable flags backed by `django-constance` with automatic fieldset registration.
  - `Configuration`: Database-stored versioned JSON settings resolved per `interface_type` and cached per schema context.
- **Zero Heavy Network Dependencies**:
  - Adapter backends and descriptors must avoid requiring optional heavy external packages (e.g., prefer Python's standard library `http.client` / `_http_client` over external `requests` for token verification).
- **Core Directory Isolation (`CORE_BASE_DIR`, `CORE_APP_DIR`, `CORE_SETUP_DIR`)**:
  - **Never Override Core Settings for Inheriting Projects**: Inheriting projects (host projects) define their own `BASE_DIR` and `APP_DIR` pointing to their own project root and host apps. Core settings must never be hijacked or overridden to accommodate host projects.
  - Core-internal paths (fixtures, dev seeders, autodiscovery) must always anchor to core-specific directory constants (`settings.CORE_BASE_DIR`, `settings.CORE_APP_DIR`, `settings.CORE_SETUP_DIR`).
  - `FileDataSource` and `AutoDiscovery` must receive complete paths anchored to these constants (e.g. `FileDataSource(os.path.join(settings.CORE_APP_DIR, "crm/fixtures/..."))` or `AutoDiscovery(root_path=settings.CORE_APP_DIR)`), ensuring host projects overriding `BASE_DIR` never break core fixtures, seeders, or module resolution.

---

### 3. Views & API (`api/views.py`, `api/serializers.py`)

> **Architecture in 1–2 Lines**:
> Views act as thin HTTP dispatchers delegating business logic to managers and services; serializers validate request schemas and format output data using dynamically resolved models.

#### Rules & Patterns

- **No Inline / Lazy Imports in Services & Views**:
  - Keep imports clean at module level. Avoid inline `from core.apps... import ...` inside view methods or service functions unless breaking an unavoidable circular dependency.
- **Module-Level Model Resolution**:
  - Call model getters once at the module top level:
    ```python
    User = get_user_model()
    ```
  - Do not repeatedly call `User = get_user_model()` inside `validate_*()`, `save()`, or view action methods.
- **Type Annotations via `typing.TYPE_CHECKING`**:
  - Annotate user and model parameters using quoted type annotations backed by `if typing.TYPE_CHECKING:` imports:
    ```python
    def get_jwt_tokens_for_user(user: "AbstractUser") -> dict: ...
    ```
- **Serializer Invariants**:
  - Always declare explicit `fields` lists. Never use `fields = "__all__"` on mutable entities.
  - Explicitly declare `read_only_fields = ["id", "created", "modified", ...]`.
  - Format choice representations using `serializers.CharField(source="get_<field>_display", read_only=True)`.
  - Expose model properties (`full_name`, totals) as read-only serializer fields.
- **View Invariants**:
  - Restrict `http_method_names` according to domain requirements.
  - Always query `.available_objects` for soft-deletable models and apply `select_related()` / `prefetch_related()` to prevent N+1 query bottlenecks.
  - For asynchronous state changes (such as OTP dispatch), return `status.HTTP_202_ACCEPTED` immediately to avoid leaking entity existence or blocking request worker threads.
  - **No Synchronous External Calls or Network I/O**: Views must never execute external service calls or network I/O (e.g., SMS/Email delivery) directly on the HTTP request thread. All external dispatches must be queued asynchronously via `queue_task()`. Errors during queuing must only be logged; never fall back to executing blocking external calls synchronously in the request-response cycle.

---

### 4. URLs & Routers (`urls.py`)

> **Architecture in 1–2 Lines**:
> Modular app routing registers ViewSets on environment-aware DRF routers configured via `get_api_router_instance()`.

#### Rules & Patterns

- Register routers using `get_api_router_instance()` (`SimpleRouter` in production, `DefaultRouter` in development for browsable documentation).
- Use kebab-case pluralized resource paths with an explicit `basename` (e.g. `router.register("users", UserViewSet, basename="users")`).

---

### 5. Utils & Algorithmic Generators (`core/utils/generators/`)

> **Architecture in 1–2 Lines**:
> Cross-cutting generation strategies (usernames, tokens, codes) are encapsulated in dedicated generator classes with comprehensive docstrings under `core/utils/generators/`.

#### Rules & Patterns

- Encapsulate generation state, fallback ladders, and normalization inside dedicated classes (e.g., `UsernameGenerator`).
- Provide an explicit `.generate(user_model=..., max_attempts=...)` instance method alongside a functional convenience helper (e.g., `generate_unique_username(...)`).
- Maintain comprehensive docstrings explaining argument priority, normalization rules, and collision escalation strategies.

---

### 6. Asynchronous Task Queuing (`core/utils/tasks.py`)

> **Architecture in 1–2 Lines**:
> Background jobs and external I/O dispatch via Celery workers wrapped by the standardized `queue_task()` utility.

#### Rules & Patterns

- Always use `queue_task()` instead of calling `.delay()` or `.apply_async()` directly.
- Default to `on_commit=True` so worker tasks execute only after database transactions commit.
- Pass unique `idempotency_key` arguments to prevent duplicate processing during worker retries or concurrent dispatches.

---

### 8. Template-Driven Frontend Architecture (`core/templates/`)

- **MANDATORY CONTEXT**: Always consult [`core/templates/Readme.md`](core/templates/Readme.md) before creating or modifying frontend templates, macros, or static assets.
- **Engine & Extensions**: Use **Jinja2** (`.jinja` file extension) for all application and domain UI views. Keep Django default DTL only for Django Admin and DRF browsable API.
- **Component Macro Design**: Implement UI elements as reusable Jinja2 `{% macro %}` components with explicit default arguments, `extra_classes`, and `caller()` slots.
- **Namespacing**: Core layout/components reside in `core/templates/core/`. Domain app templates reside in `core/apps/<app>/templates/<app>/`. Never create un-namespaced root templates.
- **Design Tokens (CSS Variables)**: Never hardcode colors, spacing, or typography. Reference tokens in `variables.css` (`var(--color-primary)`, `var(--spacing-md)`) to preserve multi-tenant white-labeling capability.
- **Lightweight Interactivity & Zero Inline JS**: Utilize centralized `Core` helpers in `core.js` and declarative data attributes (`data-sidebar-toggle`, `data-sidebar-mobile-toggle`, `data-modal-target`, `data-alert-dismiss`). **Never** write inline JavaScript (`onclick="..."`, ad-hoc DOM queries) inside Jinja2 templates or macro components.

## 5. Documentation Maintenance Standards

Always keep app-level documentation (`Readme.md`) synchronized with code changes:

- **New Features**: When implementing new models, settings, managers, or endpoints, update the corresponding app's `Readme.md`.
- **Fixes & Refactors**: If fixing a bug or refactoring existing logic and the documentation is outdated, update it immediately.
- **Documentation Rules**:
  - **No Large Code Dumps**: Do not paste large class definitions or lengthy boilerplate into documentation.
  - **Short, Crisp & Concise**: Highlight model relationships, architectural roles, manager helpers, and endpoints directly.
  - **Minimal Snippets**: Include example or helper snippets only when necessary for non-obvious integration or usage patterns.
