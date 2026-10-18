# Core Utilities Index (`core.utils`)

Location: [`core/utils/`](./__init__.py)

## Overview

The `core.utils` package provides cross-cutting, reusable utilities, base models, descriptors, algorithms, and service adapters used across all domain applications.

---

## ⚡ Quick Task Index (Cheat Sheet)

Find the right utility by what you want to accomplish:

| Intent / Task | Recommended Utility | Import Path |
| :--- | :--- | :--- |
| **Queue Celery task (transaction-safe)** | [`queue_task()`](./tasks.py#L39-L98) | `from core.utils.tasks import queue_task` |
| **Switch tenant DB schema** | [`core_schema_context`](./database.py#L14-L33) | `from core.utils.database import core_schema_context` |
| **Base entity model (UUID + soft-delete)** | [`BaseModel`](./models/model_bases.py#L89-L120) | `from core.utils.models import BaseModel` |
| **Safe single-object DB fetch** | [`get_object_or_raise()`](./models/helpers.py#L9-L20) | `from core.utils.models import get_object_or_raise` |
| **Track unsaved field modifications** | [`DirtyFieldsMixin`](./dirtyfields/dirtyfields.py#L19-L220) | `from core.utils.dirtyfields import DirtyFieldsMixin` |
| **Generate unique username/slug** | [`generate_unique_username()`](./generators/username.py#L123-L150) | `from core.utils.generators import generate_unique_username` |
| **Declarative app settings & toggles** | [`BaseSettings`](./app_settings/base.py), [`Setting`](./app_settings/types.py) | `from core.utils.app_settings import BaseSettings, Setting, Constance` |
| **Read-only REST serializer** | [`ReadOnlyModelSerializer`](./serializers/base.py#L8-L44) | `from core.utils.serializers import ReadOnlyModelSerializer` |
| **Staff/role conditional serializer** | [`ConditionalReadOnlySerializer`](./serializers/permission_based.py#L4-L47) | `from core.utils.serializers import ConditionalReadOnlySerializer` |
| **Register pluggable classes** | [`ClassRegistry`](./registry/class_registry.py#L8-L84), [`@auto_register`](./registry/class_registry.py#L138-L171) | `from core.utils.registry import ClassRegistry, auto_register` |
| **Mask PII & secrets in logs/payloads** | [`ContentMaskingUtils`](./error_handling/content_masking.py#L232-L398) | `from core.utils.error_handling.content_masking import ContentMaskingUtils` |
| **Autodiscover modules/seeders** | [`AutoDiscovery`](./autodiscovery.py#L345-L360) | `from core.utils.autodiscovery import AutoDiscovery` |
| **Timezone-aware dates/times** | [`get_local_datetime()`](./dates.py#L7-L40), [`get_local_date()`](./dates.py#L42-L72) | `from core.utils.dates import get_local_datetime, get_local_date` |
| **Environment & tenant checks** | [`is_production()`](./checks.py#L16-L21), [`is_multi_tenant()`](./checks.py#L9-L14) | `from core.utils.checks import is_production, is_multi_tenant` |
| **Environment-aware DRF API router** | [`get_api_router_instance()`](./routers.py#L7-L16) | `from core.utils.routers import get_api_router_instance` |
| **String case conversion** | [`camel_to_snake_case()`](./strings.py#L4-L26) | `from core.utils.strings import camel_to_snake_case` |
| **Runtime dynamic choices/enums** | [`LazyDynamicChoiceTypes`](./lazy_objects.py#L51-L89), [`TupleEnum`](./lazy_objects.py#L37-L49) | `from core.utils.lazy_objects import LazyDynamicChoiceTypes, TupleEnum` |
| **Graph traversal & DAG resolution** | [`DirectedGraph`](./datatypes/graph.py#L64-L125), [`InstanceDAGBuilder`](./datatypes/implementations.py#L18-L122) | `from core.utils.datatypes import BaseDAGBuilder, InstanceDAGBuilder` |
| **SMS backend adapter (console/test)** | [`ConsoleSMSBackend`](./backends/sms/console.py#L8-L31) | `from core.utils.backends.sms import BaseSMSBackend, ConsoleSMSBackend` |

---

## 📁 Subpackages

Detailed subpackage implementations and their dedicated documentation:

### 1. [`app_settings/`](./app_settings/Readme.md)
Descriptor-based configuration framework powering app-level `app_settings.py`.
* **[`BaseSettings`](./app_settings/base.py)**: Abstract container for app settings subclasses.
* **[`Setting`](./app_settings/types.py)**: Static code configurations, lazy imports (`IMPORT`, `DEFFERED_IMPORT`), model strings (`MODEL_IMPORT`), and primitives.
* **[`Constance`](./app_settings/types.py)**: Live admin-editable flags backed by `django-constance`.
* **[`Configuration`](./app_settings/types.py)**: Database-stored versioned JSON settings resolved per interface type.

### 2. [`backends/`](./backends/)
Pluggable infrastructure delivery adapters.
* **[`sms/base.py`](./backends/sms/base.py)**: [`BaseSMSBackend`](./backends/sms/base.py#L4-L24) abstract contract (`send_sms(to, message)`).
* **[`sms/console.py`](./backends/sms/console.py)**: [`ConsoleSMSBackend`](./backends/sms/console.py#L8-L31) implementation for dev/test output to console and logs.

### 3. [`datatypes/`](./datatypes/)
Custom data structures, graph traversals, and dependency resolution builders.
* **[`graph.py`](./datatypes/graph.py)**: [`Graph`](./datatypes/graph.py#L5-L62) and [`DirectedGraph`](./datatypes/graph.py#L64-L125) with in-degree calculation, Kahn's algorithm BFS topological sort, and cycle detection.
* **[`queue.py`](./datatypes/queue.py)**: Pointer-based [`Queue`](./datatypes/queue.py#L6-L84) with `peep()`, `clean_queue()`, `enqueue()`, and `dequeue()`.
* **[`implementations.py`](./datatypes/implementations.py)**: [`BaseDAGBuilder`](./datatypes/implementations.py#L6-L16) and [`InstanceDAGBuilder`](./datatypes/implementations.py#L18-L122) for sorting dependent classes/objects.

### 4. [`dirtyfields/`](./dirtyfields/)
Tracks field modifications on Django model instances before saving.
* **[`dirtyfields.py`](./dirtyfields/dirtyfields.py)**: [`DirtyFieldsMixin`](./dirtyfields/dirtyfields.py#L19-L220) providing `get_dirty_fields()`, `is_dirty()`, and M2M change detection.
* **[`compare.py`](./dirtyfields/compare.py)**: State comparison routines with timezone and file handling (`compare_states`, `raw_compare`, `timezone_support_compare`).

### 5. [`error_handling/`](./error_handling/Readme.md)
PII sanitization, sensitive data masking, and error serialization.
* **[`content_masking.py`](./error_handling/content_masking.py)**:
  * [`ContentMaskingUtils`](./error_handling/content_masking.py#L232-L398): `filter_sensitive_content()`, `mask_email()`, `mask_phone()`.
  * [`PatternMatcher`](./error_handling/content_masking.py#L45-L192): Regex engine with word boundary detection for sensitive tokens.
  * [`stringify_dict()`](./error_handling/content_masking.py#L205-L230): Flattens nested dicts for telemetry.

### 6. [`generators/`](./generators/)
Algorithmic identifier and token generation strategies.
* **[`username.py`](./generators/username.py)**:
  * [`UsernameGenerator`](./generators/username.py#L8-L121): Builds normalized slug from first name, last name, email, or phone number, adding cryptographically secure pseudorandom suffixes to avoid DB collisions.
  * [`generate_unique_username()`](./generators/username.py#L123-L150): Convenience wrapper function.

### 7. [`models/`](./models/Readme.md)
Foundation models, soft-delete mechanics, semantic versioning, and query helpers.
* **[`model_bases.py`](./models/model_bases.py)**:
  * [`BaseModel`](./models/model_bases.py#L89-L120): UUID PK, timestamps, soft-delete tracking (`is_removed`, `removed_by`), and `get_object()`.
  * [`BaseVersioningModel`](./models/model_bases.py#L154-L219): Semantic version integers (`major`, `minor`, `patch`) with `bump_version()`.
  * [`BaseLogModel`](./models/model_bases.py#L134-L152): Choice-based state tracking model with timestamps.
  * [`AbstractParty`](./models/model_bases.py#L9-L39), [`AbstractAddress`](./models/model_bases.py#L41-L87): Reusable identity and address models.
* **[`soft_delete.py`](./models/soft_delete.py)**: [`DeletionTrackingModel`](./models/soft_delete.py#L15-L122) capturing deleting user from context or arguments.
* **[`versioning.py`](./models/versioning.py)**: [`SimpleVersionModelMixin`](./models/versioning.py#L10-L57) synchronizing string and numeric versions on `save()`.
* **[`helpers.py`](./models/helpers.py)**: [`get_object_or_raise()`](./models/helpers.py#L9-L20), [`safe_get_object_or_raise()`](./models/helpers.py#L22-L45), [`filter_objects_or_raise()`](./models/helpers.py#L47-L64).

### 8. [`registry/`](./registry/)
Dynamic class registry pattern for extensible systems.
* **[`base.py`](./registry/base.py)**: [`BaseRegistry`](./registry/base.py#L7-L21) abstract interface.
* **[`class_registry.py`](./registry/class_registry.py)**:
  * [`ClassRegistry`](./registry/class_registry.py#L8-L84): Keyed dictionary registry with duplicate protection.
  * [`UnorderedClassRegistry`](./registry/class_registry.py#L86-L136): Set-based class registry with case-insensitive `contains()`.
  * [`@auto_register`](./registry/class_registry.py#L138-L171): Class decorator for auto-registering components.

### 9. [`serializers/`](./serializers/Readme.md)
Base DRF model serializers enforcing field-level mutability contracts.
* **[`base.py`](./serializers/base.py)**: [`ReadOnlyModelSerializer`](./serializers/base.py#L8-L44) (locks all fields to read-only) and [`DynamicReadOnlyModelSerializer`](./serializers/base.py#L46-L82).
* **[`permission_based.py`](./serializers/permission_based.py)**: [`ConditionalReadOnlySerializer`](./serializers/permission_based.py#L4-L47) allowing field-level mutation based on request context and user permissions.

---

## 📄 Top-Level Modules

Single-file utilities located directly under `core/utils/`:

### [`autodiscovery.py`](./autodiscovery.py)
* **[`AutoDiscovery`](./autodiscovery.py#L345-L360)** / **[`AutoDiscoveryMixin`](./autodiscovery.py#L25-L343)**: Recursively or selectively traverses directories up to a given `scan_depth`, locates target Python files (e.g. `seeder.py`), executes pre/post hooks, and safely imports modules via `importlib`.
* **[`AutoDiscoveryError`](./autodiscovery.py#L19-L22)**: Discovery or module resolution failure exception.

### [`checks.py`](./checks.py)
* **[`is_multi_tenant()`](./checks.py#L9-L14)**: Returns `True` if `django_tenants` is in `settings.INSTALLED_APPS`.
* **[`is_production()`](./checks.py#L16-L21)**: Returns `True` if `DEBUG=False` and `DJANGO_ENV == "production"`.
* **[`is_development()`](./checks.py#L23-L28)**: Inverted check for development mode (`not is_production()`).
* **[`is_model(kls)`](./checks.py#L30-L39)**: Validates if `kls` is a Django `models.Model` subclass or `ModelBase` instance.

### [`database.py`](./database.py)
* **[`get_public_schema_name()`](./database.py#L7-L12)**: Returns configured `PUBLIC_SCHEMA_NAME` or defaults to `"public"`.
* **[`core_schema_context`](./database.py#L14-L33)**: Context manager & decorator for multi-tenant schema switching on `connections[database]`, cleanly restoring tenant context upon exit.

### [`dates.py`](./dates.py)
* **[`get_local_datetime(dt=None, naive_is_utc=True)`](./dates.py#L7-L40)**: Normalizes naive or aware datetimes into timezone-aware datetimes under `settings.TIME_ZONE`. Returns current local datetime when `dt=None`.
* **[`get_local_date(dt=None, naive_is_utc=True)`](./dates.py#L42-L72)**: Extracts the calendar `date` in `settings.TIME_ZONE` from `datetime` or `date`.

### [`file_handling.py`](./file_handling.py)
* **[`load_file_from_package(target_filename, file_path=None, target_class=None)`](./file_handling.py#L6-L34)**: Dynamically imports a module located in the same package as `file_path` or `target_class`.
* **[`classes_from_file(file=None, file_path=None)`](./file_handling.py#L36-L53)**: Introspects and extracts class definitions from an imported module using `inspect.getmembers`.

### [`lazy_objects.py`](./lazy_objects.py)
* **[`LazyDynamicChoiceTypes`](./lazy_objects.py#L51-L89)**: Proxy wrapper around dynamic choice collections, allowing apps to register choices at runtime via `.contribute()`.
* **[`TupleEnum`](./lazy_objects.py#L37-L49)**: ReprEnum tuple helper providing `.value` and `.label` properties for clean Django choices.
* **[`DynamicChoiceType`](./lazy_objects.py#L7-L35)**: Base class for dynamic choices exposing `.choices` and `.values`.

### [`routers.py`](./routers.py)
* **[`get_api_router_instance()`](./routers.py#L7-L16)**: Returns DRF `DefaultRouter` in development (`settings.DEBUG=True`) for browsable API docs, and lightweight `SimpleRouter` in production.

### [`strings.py`](./strings.py)
* **[`camel_to_snake_case(class_name)`](./strings.py#L4-L26)**: Regex-based case converter handling acronyms (e.g. `"HTTPResponse"` -> `"http_response"`).

### [`tasks.py`](./tasks.py)
* **[`queue_task(task, on_commit=True, ignore_result=True, idempotency_key=None, ...)`](./tasks.py#L39-L98)**: Celery task dispatch wrapper supporting database transaction `on_commit` hooks, schema-prefixed idempotency keys, and result backend suppression.
* **[`import_task(task_path)`](./tasks.py#L19-L37)**: Resolves and imports a Celery task function from a dotted Python path.
* **[`TaskQueuingException`](./tasks.py#L11-L16)**: Domain exception raised on task queuing validation errors.
