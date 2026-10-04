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

### Phase 4: Testing Phase

- Write unit tests for individual functions and service methods.
- Mock external APIs, I/O boundaries, and Celery tasks.
- Validate multi-tenant schema isolation where applicable.

## 4. Key Design Norms & Architectural Rules

### 1. No Multi-Table Inheritance (MTI)

- **Single Concrete Table per Entity**: Multi-table inheritance (`class Child(ParentModel)`) creates unnecessary joins and migration complexity.
- Use a single table with discriminator fields (`type`, `sub_type`, `status`) and abstract mixins for shared behavior.

### 2. Cross-App Model Decoupling (Swappable Models)

- **Never** hard-import another app's concrete model directly across domain apps.
- Use Django's swappable model pattern:
  - Reference foreign keys using `settings.<APP>_<MODEL>_MODEL` (e.g., `settings.TENANTS_TENANT_MODEL`).
  - Resolve model classes at runtime using `django.apps.apps.get_model()` or dedicated app model getter functions (e.g., `get_tenant_model()`).

### 3. App Settings Framework (`core.utils.app_settings`)

- Every app needing configurable defaults or runtime parameters declares a `BaseSettings` subclass.
- **Descriptors Available**:
  - `Settings`: Static code configurations and lazy dotted imports (`SettingsType.MODEL_IMPORT`, `SettingsType.DEFFERED_IMPORT`).
  - `Constance`: Live admin-editable flags backed by `django-constance` with automatic schema/fieldset registration.
  - `Configuration`: Database-stored versioned JSON settings resolved per `interface_type` and cached per schema.
- **Project Overrides**: Settings can be overridden in `django.conf.settings` via dictionaries (`settings.<APP>_SETTINGS`).

### 4. Base Model Hierarchy (`core.utils.models`)

All domain models must inherit from one of the core base models:

| Base Class            | Purpose                        | Key Attributes / Behavior                                                                      |
| :-------------------- | :----------------------------- | :--------------------------------------------------------------------------------------------- |
| `BaseModel`           | Standard domain entities       | UUID PK (`id`), `created`, `modified`, soft delete (`is_removed`, `removed_by`)                |
| `BaseVersioningModel` | Version-tracked configurations | Semantic version integers (`version_major/minor/patch`), formatted `version`, `bump_version()` |
| `BaseLogModel`        | Audit logs & event histories   | UUID PK, timestamps, choice-based `status`, `status_changed`                                   |

- **Soft Deletion**: `.delete()` soft-deletes rows by default (`is_removed=True`), recording the user via `removed_by`. Hard deletion requires explicit `soft=False`.
- **Safe Model Lookups**: Use query helpers (`safe_get_object_or_raise`, `filter_objects_or_raise`) rather than raw `Model.objects.get()` when handling potentially ambiguous datasets.

### 5. Error Handling & Data Sanitization

- Never expose raw database errors or unsanitized lookup queries in logs or API payloads.
- Use `ContentMaskingUtils.filter_sensitive_content()` to sanitize passwords, tokens, API keys, emails, and phone numbers before logging or returning error messages.

### 6. API & Routing Conventions

- **ViewSets**: Use DRF `ViewSet` / `ReadOnlyModelViewSet` rather than function-based views.
- **Thin Views, Rich Services**: Business logic belongs in service classes or managers, not inside view methods.
- **Serializers**: Use `ReadOnlyModelSerializer` or `DynamicReadOnlyModelSerializer` to strictly control mutations.
- **Router Construction**: Always register viewsets using `get_api_router_instance()` (`SimpleRouter` in production, `DefaultRouter` in development).

### 7. Asynchronous Task Queuing

- Use the standardized `queue_task()` wrapper (`core.utils.tasks`) instead of calling `.delay()` or `.apply_async()` directly.
- Default to `on_commit=True` to ensure database transactions are committed before workers pick up tasks.
- Pass unique `idempotency_key` arguments to prevent duplicate processing during retries or concurrent dispatches.

## 5. Documentation Maintenance Standards

Always keep app-level documentation (`Readme.md`) synchronized with code changes:

- **New Features**: When implementing new models, settings, managers, or endpoints, update the corresponding app's `Readme.md`.
- **Fixes & Refactors**: If fixing a bug or refactoring existing logic and the documentation is outdated, update it immediately.
- **Documentation Rules**:
  - **No Large Code Dumps**: Do not paste large class definitions or lengthy boilerplate into documentation.
  - **Short, Crisp & Concise**: Highlight model relationships, architectural roles, manager helpers, and endpoints directly.
  - **Minimal Snippets**: Include example or helper snippets only when necessary for non-obvious integration or usage patterns.
