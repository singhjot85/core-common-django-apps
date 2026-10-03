# Core Utilities (`core.utils`)

Location: [`core/utils/`](./__init__.py)

## Overview

The `core.utils` package contains foundational utilities, base classes, descriptors, and helper routines shared across all domain applications in the project.

## Module Index

| Module / Package | Description |
| :--- | :--- |
| [`app_settings/`](./app_settings/Readme.md) | Descriptor-based dynamic application settings and configuration framework. |
| [`error_handling/`](./error_handling/Readme.md) | Sensitive data masking, string serialization, and structured domain exceptions. |
| [`models/`](./models/Readme.md) | Base models (`BaseModel`, `BaseVersioningModel`), soft deletion with user tracking, and query helpers. |
| [`serializers/`](./serializers/Readme.md) | Read-only and permission-conditional DRF model serializers. |

## Top-Level Utilities

* **[`checks.py`](./checks.py)**:
  * [`is_multi_tenant()`](./checks.py#L8-L12): Checks if `django_tenants` is present in `settings.INSTALLED_APPS`.
  * [`is_production()`](./checks.py#L15-L19): Determines if the current environment is running under production settings (`DEBUG=False`).
* **[`file_handling.py`](./file_handling.py)**:
  * [`load_file_from_package()`](./file_handling.py#L6-L34): Dynamically imports a module located within a given package path or relative to a class.
  * [`classes_from_file()`](./file_handling.py#L36-L53): Inspects and extracts class definitions from an imported module.
* **[`lazy_objects.py`](./lazy_objects.py)**:
  * [`LazyDynamicChoiceTypes`](./lazy_objects.py#L51-L89): Lazy choice registry that allows applications to dynamically register choices at runtime via `.contribute()`.
  * [`TupleEnum`](./lazy_objects.py#L37-L49): Enumeration helper providing `.value` and `.label` tuple properties.
* **[`routers.py`](./routers.py)**:
  * [`get_api_router_instance()`](./routers.py#L7-L15): Returns `DefaultRouter` in debug mode (browsable root API) and `SimpleRouter` in production.
* **[`tasks.py`](./tasks.py)**:
  * [`queue_task()`](./tasks.py#L39-L98): Standardized Celery task queueing wrapper supporting transaction `on_commit` hooks, schema-scoped idempotency keys, and result-backend ignoring.
  * [`import_task()`](./tasks.py#L19-L36): Resolves and imports a Celery task function from a dotted Python string path.
