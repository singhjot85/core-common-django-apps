# Modern Database Seeder Framework (`core.libraries.seeder`)

Location: [`core/libraries/seeder/`](./__init__.py)

## Overview

`core.libraries.seeder` provides a decoupled, declarative, and dependency-driven database seeding and fixture population engine for multi-tenant Django applications.

Key features:
- **Decoupled Architecture:** Lives in `core.libraries` with zero dependencies on specific business domain apps (`core.apps.*`).
- **Composition over Inner Meta:** Configuration is declared directly via top-level class attributes (`method = ...`, `loader = ...`).
- **Pluggable Persistence Methods:** Pluggable strategy classes (`GetorCreateObject`, `UpdateOrCreateObject`, `CreateObject`) encapsulate model querying and creation.
- **Relational Graphs & Nested Seeders:** Parent seeders coordinate child seeders via `related_seeder_map` with automatic parent foreign key injection and atomic saving.
- **Foreign Key `$ref` Syntax:** References existing model instances by key-value lookups (e.g. `{"user": {"$ref": {"email": "..."}}}`).
- **Schema Isolation via Runners:** `SeederRunner` constructs a topological DAG of seeders and executes one fresh instance per tenant schema context, preventing cross-tenant data leakage.
- **Custom Transform Hooks:** `set_<field_name>` hooks on seeder classes allow runtime modification and loading of external template files.

---

## Architecture

```
┌─────────────────────────────────┐
│     1. Seeder Definition        │  --> BaseSeeder with class attributes:
│ (method, loader, related_map)   │      method, loader, schemas, depends_on
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│      2. Class Registration      │  --> __init_subclass__() registers seeders into
│                                 │      seeder_registry (and fixture_registry if is_fixture).
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│      3. SeederRunner & DAG      │  --> Resolves dependencies via Kahn's algorithm
│                                 │      (DAG based on depends_on and method.model).
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│ 4. Isolated Schema Execution    │  --> Instantiates fresh seeder per schema context,
│                                 │      dispatches seed_data(), loads files, links relations.
└─────────────────────────────────┘
```

---

## Quick Example

```python
from django.conf import settings
from core.apps.crm import get_customer_model
from core.libraries.seeder import BaseSeeder, FileBasedLoader, GetorCreateObject

Customer = get_customer_model()


class DevCustomerSeeder(BaseSeeder):
    """Development mock seeder for Customer records."""

    method = GetorCreateObject(
        model=Customer,
        lookup_fields=("first_name", "last_name"),
        default_fields=("first_name", "middle_name", "last_name", "business_name", "customer_type", "status"),
        related_seeder_map={
            "phones": DevCustomerPhoneSeeder,
            "emails": DevCustomerEmailSeeder,
            "addresses": DevCustomerAddressSeeder,
        },
    )
    loader = FileBasedLoader(
        directory_name="dev_customer",
        load_method=FileBasedLoader.LOAD_INDIVIDUAL,
    )
    schemas = [settings.TENANT_TYPE_ORGANIZATION]
    is_fixture = False
```
