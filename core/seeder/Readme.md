# Database Seeder Framework (`core.seeder`)

Location: [`core/seeder/`](./__init__.py)

## Overview

The `core.seeder` framework provides a declarative, dependency-driven database seeding and fixture population engine for Django applications. It is designed specifically for multi-tenant architectures, supporting schema switching, topological dependency resolution via Directed Acyclic Graphs (DAGs), atomic database transactions, and relation linking.

---

## Architecture & Execution Lifecycle

The seeder framework executes in four distinct phases:

```
┌─────────────────────────┐
│ 1. Subclass Declaration │  --> __init_subclass__() registers seeder classes into
│   & Registration        │      `seeder_registry` (and `fixture_registry` if fixture).
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ 2. Autodiscovery        │  --> AutoDiscovery scans configured setup directories (e.g. `setup/`,
│                         │      `core/apps/*/fixtures/`) and imports seeder modules.
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ 3. Topological DAG Sort │  --> SeederRunner inspects `depends_on` models and `execution_order`,
│    (Kahn's Algorithm)   │      constructs a DAG, and produces a strictly ordered execution list.
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│ 4. Transactional Schema │  --> Inside transaction.atomic(), iterates through seeders, switches
│    Execution            │      schema context (`core_schema_context`), and creates model records.
└─────────────────────────┘
```

---

## 1. Declarative Seeder Definition

Seeders inherit from [`BaseSeeder`](./base.py) and configure an inner `Meta` inheriting from [`BaseMeta`](./base.py).

```python
import os
from django.conf import settings
from core.apps.crm import get_customer_model
from core.apps.users import get_user_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource

Customer = get_customer_model()
User = get_user_model()


class DevCustomerSeeder(BaseSeeder):
    """Development mock seeder for Customer records."""

    class Meta(BaseMeta):
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "business_name",
            "customer_type",
            "status",
            "user__email",  # Forward relation lookup
        ]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(
                settings.CORE_BASE_DIR, "setup/crm/dev_customer/customers.json"
            )
        )
        depends_on = [User]       # Prerequisite model dependency
        execution_order = 2       # Priority order for initial execution
```

### `BaseMeta` Configuration Options

| Attribute | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `model` | `models.Model` | *Required* | Target Django model class to populate. |
| `fields` | `list[str]` | *Required* | List of field names allowed to be populated from input data. |
| `data_source` | `AbstractDataSource` | `None` | Pluggable source supplying seed data (e.g. `FileDataSource`). |
| `depends_on` | `list[type[Model]]` | `[]` | List of prerequisite model classes that must be seeded before this seeder. |
| `execution_order` | `int \| None` | `None` | Optional execution priority integer (lower numbers execute earlier). |
| `is_fixture` | `bool` | `False` | When `True`, registered into `fixture_registry` for production environments. |
| `schema_name` | `str \| None` | `None` | Specific database schema to target (e.g. `"public"`). Defaults to tenant rules. |
| `tenant_type` | `str` | `ORGANIZATION` | `settings.TENANT_TYPE_ORGANIZATION` or `"public"`. |
| `object_create_method`| `Callable` | `manager.get_or_create` | Custom manager persistence callable (e.g. `get_or_create_user`). |
| `related_seeders` | `dict[str, type[BaseSeeder]]` | `{}` | Mapping of field names to nested `BaseSeeder` classes for automatic child creation. |

---

## 2. Dependency Resolution & Topological Sorting

The execution engine uses [`InstanceDAGBuilder`](../utils/datatypes/implementations.py) to resolve prerequisites into a Directed Acyclic Graph:

1. **Model Prerequisite Mapping**: [`SeederRunner.get_dependencies()`](./runners.py) maps each model in `Meta.depends_on` to the corresponding registered `BaseSeeder` responsible for seeding that model (comparing `app_label`, `model_name`, and `db_table`).
2. **Kahn's BFS Topological Sort**: The runner constructs directed edges `(prerequisite_seeder -> dependent_seeder)` and executes Kahn's algorithm in `O(V + E)` time. If circular dependencies are detected, a [`CycleError`](../exceptions.py) is raised immediately.
3. **Initial Root Prioritization**: Seeders declaring the minimum `execution_order` (e.g. `1`) are validated by `is_initial_attribute()` and pinned to the start of the execution sequence.

---

## 3. Data Sources (`FileDataSource`)

Seed data is abstracted via [`AbstractDataSource`](./datasource.py). The primary implementation is [`FileDataSource`](./datasource.py):

* **Compiled Mode (`LOAD_COMPILED`)**: Reads a single JSON file containing a list of records:
  ```python
  FileDataSource("setup/crm/dev_customer/customers.json")
  ```
* **Individual Mode (`LOAD_INDIVIDUAL`)**: Scans a directory for multiple individual `*.json` files:
  ```python
  FileDataSource("setup/crm/dev_customer", load_method=FileDataSource.LOAD_INDIVIDUAL)
  ```

---

## 4. Multi-Tenant Schema Context & Execution

Database seeders run within multi-tenant schemas via [`core_schema_context`](../utils/database.py):

* **Single Schema Seeders**: If `schema_name` is explicitly set (e.g. `"public"`), the seeder runs within that target schema context.
* **All Tenant Schemas (`ALL_SCHEMAS`)**: For seeders with `tenant_type = settings.TENANT_TYPE_ORGANIZATION` and no explicit `schema_name`, [`SeederRunner._run()`](./runners.py) automatically queries all active tenants (`TenantStatus.READY`) and executes the seed routines across each tenant schema.
* **Item-Level Schema Override (`_schema_name`)**: Individual records in seed JSON can specify `"_schema_name": "public"` to target a specific schema for that record (e.g. superuser creation).

---

## 5. Relation Handling & Lookup Syntax

Seeders automatically resolve and link relationships:

* **Forward ForeignKeys via double underscore (`__`)**:
  ```json
  {
      "first_name": "Charlie",
      "user__email": "admin1@localhost.com"
  }
  ```
  The seeder executes `User.objects.get(email="admin1@localhost.com")` and assigns it to the `user` ForeignKey.
* **Nested Related Seeders**: When `related_seeders = {"profile": UserProfileSeeder}` is defined, nested JSON dictionaries automatically instantiate and seed the related model before attaching it to the parent record.
* **Deferred Linking**: Forward singular relations (`ForwardSingularRelation`), reverse singular relations (`ReverseSingularRelation`), and related managers (`ManagerRelation`) handle FK, O2O, and M2M assignments.

---

## 6. Execution Runners & Management Commands

| Runner | Registry | Environment Guard | Description |
| :--- | :--- | :--- | :--- |
| [`SeedDevelopmentData`](./runners.py) | `seeder_registry` | Dev / Test only (`is_development()`) | Discovers and runs development mock seeders and fixtures. |
| [`SeedFixtures`](./runners.py) | `fixture_registry` | All environments | Populates static production fixtures (statuses, preferences, schemas). |

### CLI Management Command

```bash
# Via Make target (recommended)
make dev-setup

# Or via manage.py directly in development container
python manage.py run_dev_seeders
```

---

## Appendix: Django Model Field Inspection Reference

### Identifying Field Types

```python
from django.db import models

for field in MyModel._meta.get_fields():
    if isinstance(field, models.ManyToManyField):
        pass  # Many-to-Many
    elif isinstance(field, models.ForeignKey):
        pass  # Foreign Key (Many-to-One)
    elif isinstance(field, models.OneToOneField):
        pass  # One-to-One
    elif field.auto_created and not field.concrete:
        pass  # Reverse relation (related_name accessor)
    else:
        pass  # Concrete attribute (CharField, IntegerField, etc.)
```

### Quick Check Attributes

| Attribute | Meaning |
| :--- | :--- |
| `field.is_relation` | True for any relation (FK, O2O, M2M, Reverse) |
| `field.many_to_one` | ForeignKey |
| `field.one_to_many` | Reverse ForeignKey |
| `field.one_to_one` | OneToOneField (forward or reverse) |
| `field.many_to_many` | ManyToManyField (forward or reverse) |
| `field.concrete` | Real database column on this model's table |
| `field.auto_created` | Reverse relations created automatically |
