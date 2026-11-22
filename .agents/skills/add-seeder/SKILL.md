---
name: add-seeder
description: Author database seeders in the core framework (core.libraries.seeder) - production fixtures (is_fixture=True) and development mock-data seeders. Use when asked to seed models, create fixtures or mock/dev data, write BaseSeeder subclasses, wire seeder dependencies (depends_on, related_seeder_map), or debug seeder runs (make dev-setup, SeedFixtures).
---

# Seeder Authoring (`add-seeder`)

`core.libraries.seeder` is a decoupled, declarative, dependency-ordered seeding engine for multi-tenant Django apps. You describe *what* to seed via class attribute composition (`loader`, `method`, `related_seeder_map`); `BaseSeeder` and `SeederRunner` handle DAG ordering, multi-tenant schema isolation, atomic transactions, and relational graph linking.

Core facts:
- **No `BaseMeta`**: Configuration is declarative via top-level class attributes (`method = ...`, `loader = ...`).
- **Persistence Strategies**: Pluggable methods: `GetorCreateObject`, `UpdateOrCreateObject`, `CreateObject`.
- **Topological Sorting**: Handled by `SeederRunner(InstanceDAGBuilder)` over `depends_on` and model dependencies.
- **Relational Graph Linking**: Parent seeders coordinate child seeders via `related_seeder_map` with automatic parent foreign key injection and `$ref` lookups for external dependencies.
- **Multi-Tenant Schema Isolation**: Handled exclusively in the runner (`SeederRunner`), instantiating fresh seeder instances per tenant schema context to guarantee complete isolation.
- **Registries**: `seeder_registry` (all seeders) and `fixture_registry` (only `is_fixture = True`).

---

## 1. Step 0 - Decide the Tier

| Question | Fixture (production) | Dev seeder |
| :--- | :--- | :--- |
| Must exist in production for the app to work (configs, statuses, preference types, template labels)? | Yes | No |
| Fake/realistic sample data for local, QA or CI (users, customers, sample invoices)? | No | Yes |
| Runs via | `SeedFixtures` (uses `fixture_registry` only) | `make dev-setup` -> `python manage.py run_dev_seeders` |

> [!IMPORTANT]
> **Hard rule:** Production must never receive mock data. Anything with fake emails, sample users, or demo customer records is a dev seeder, always.

---

## 2. Placement & Naming

| | Production Fixture | Development Seeder |
| :--- | :--- | :--- |
| Python file | `core/apps/<app>/fixtures/seeder.py` (or `seeders.py`) | `core/setup/<app>/seeder.py` (or `seeders.py`) |
| Data directory | `core/apps/<app>/fixtures/<directory_name>/` | `core/setup/<app>/<directory_name>/` |
| Class name | `<ModelName>FixtureSeeder` (or `<Name>Seeder`) | `Dev<ModelName>Seeder` |
| `is_fixture` | `True` | `False` (default) |
| `schemas` | `["public"]` or `[settings.TENANT_TYPE_ORGANIZATION]` | Tenant or public as required |

---

## 3. Class Attributes & Architecture

Subclass `BaseSeeder` from `core.libraries.seeder`:

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

### Key Class Attributes

- `method`: An instance of `GetorCreateObject`, `UpdateOrCreateObject`, or `CreateObject`.
  - `model`: Target Django model class (always resolved via `get_<model>_model()` getter).
  - `lookup_fields`: Tuple of field names used for `get_or_create` or `update_or_create` lookups.
  - `default_fields`: Tuple of fields passed to defaults or creation kwargs.
  - `related_seeder_map`: Dict mapping relation keys in data to child seeder classes.
- `loader`: An instance of `FileBasedLoader(directory_name="...", load_method=...)`.
  - `directory_name`: Name of the folder or file.
  - `load_method`: `FileBasedLoader.LOAD_INDIVIDUAL` (directory of individual `.json` files) or `FileBasedLoader.LOAD_COMPILED` (single `.json` file containing an array).
- `schemas`: List of schemas or tenant types where this seeder runs (e.g. `["public"]` or `[settings.TENANT_TYPE_ORGANIZATION]`).
- `is_fixture`: Set to `True` for production fixtures; defaults to `False`.
- `is_root`: Defaults to `True`. Set `is_root = False` for child seeders that should only be invoked through a parent's `related_seeder_map`.
- `depends_on`: Explicit list of prerequisite seeder classes or models.
- `label`: Custom label string in registries (defaults to `snake_case` of class name).

---

## 4. Relations and Relational Graphs

### A. Nested Relations (`related_seeder_map`)

When a parent entity owns child entities (e.g. a Customer having phones, emails, and addresses):
1. Define child seeders with `is_root = False`.
2. Map the relation keys in the parent seeder's `related_seeder_map`.
3. In child records, parent foreign keys are automatically injected by `BaseSeeder.seed_data(data, parent=instance)`.

```python
class DevCustomerPhoneSeeder(BaseSeeder):
    method = GetorCreateObject(
        model=CustomerPhone,
        lookup_fields=("customer", "phone"),
        default_fields=("customer", "phone", "phone_type", "is_primary"),
    )
    is_root = False  # Only executed via DevCustomerSeeder


class DevCustomerSeeder(BaseSeeder):
    method = GetorCreateObject(
        model=Customer,
        lookup_fields=("first_name", "last_name"),
        default_fields=("first_name", "last_name", "phones"),
        related_seeder_map={
            "phones": DevCustomerPhoneSeeder,
        },
    )
    loader = FileBasedLoader(
        directory_name="dev_customer",
        load_method=FileBasedLoader.LOAD_INDIVIDUAL,
    )
```

Data file (`setup/crm/dev_customer/charlie.json`):
```json
{
  "first_name": "Charlie",
  "last_name": "Davis",
  "phones": [
    {
      "phone": "+1-555-0101",
      "phone_type": "mobile",
      "is_primary": true
    }
  ]
}
```

### B. Foreign Key References (`$ref`)

To reference an existing object (such as a User or Tenant) from a seed file, use the `$ref` syntax:

```json
{
  "first_name": "Charlie",
  "last_name": "Davis",
  "user": {
    "$ref": {
      "email": "charlie@example.com"
    }
  }
}
```
`ForwardSingularRelation` resolves `User.objects.get(email="charlie@example.com")` and assigns the foreign key before saving.

---

## 5. Transform Hooks (`set_<field_name>`)

If a field requires runtime computation or file loading (e.g. reading an external template file):
Define a `set_<field_name>(self, value)` method on the seeder.

```python
class ConfigurationSeeder(BaseSeeder):
    method = GetorCreateObject(
        model=Configuration,
        lookup_fields=("name", "interface_type"),
        default_fields=("name", "interface_type", "details"),
    )

    def set_details(self, value):
        """Transform hook: loads external template content if given a file path."""
        if isinstance(value, str) and (value.endswith(".html") or value.endswith(".json")):
            candidate = Path(settings.CORE_SETUP_DIR) / value
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        return value
```

---

## 6. Directory Resolution & Override Priority

`FileBasedLoader` searches for data paths across the system in the following order:
1. `settings.SETUP_DIR` (Host project overrides)
2. `settings.BASE_DIR`
3. `settings.CORE_SETUP_DIR` (Core default dev data)
4. `settings.CORE_BASE_DIR`

`FileBasedLoader` aggregates data from both `SETUP_DIR` and `CORE_SETUP_DIR`. Host projects overriding `SETUP_DIR` can supply custom data without breaking or modifying core data.

---

## 7. Running & Testing Seeders

Run dev seeders via the management command:
```bash
make dev-setup
```

Or trigger the runner directly in Python / tests:
```python
from core.libraries.seeder.runner import SeedDevelopmentData, SeedFixtures

# Run fixtures (production)
runner = SeedFixtures()
runner.run()

# Run dev seeders (development only)
dev_runner = SeedDevelopmentData()
dev_runner.run()
```

### Registry Verification Test Example

```python
from core.libraries.seeder.registry import fixture_registry, seeder_registry
from core.setup.crm.seeder import DevCustomerSeeder


def test_seeder_registration():
    assert seeder_registry.get("dev_customer_seeder") is DevCustomerSeeder
    # Child seeders or non-fixtures are not in fixture_registry
    assert "dev_customer_seeder" not in fixture_registry.registry
```

---

## 8. Checklist Before Finishing

- [ ] Model resolved through getter (`get_*_model()`); never direct concrete import.
- [ ] Declarative attributes: `method = ...`, `loader = ...` on the class body.
- [ ] `lookup_fields` and `default_fields` explicitly specified.
- [ ] `is_fixture` set to `True` for production fixtures; `False` for dev seeders.
- [ ] Child seeders marked with `is_root = False` and mapped in `related_seeder_map`.
- [ ] External model references use `$ref` syntax.
- [ ] JSON data contains valid structure and dummy domains (`example.com`).
- [ ] Pre-commit passes: `poetry run pre-commit run --all-files`.
- [ ] Tests pass via make target: `make t TEST_DIR=core/tests/libraries/`.
