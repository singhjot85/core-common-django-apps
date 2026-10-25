---
name: add-seeder
description: Author database seeders in the core framework (core.seeder) - production fixtures (is_fixture=True) and development mock-data seeders. Use when asked to seed models, create fixtures or mock/dev data, write BaseSeeder subclasses, wire seeder dependencies (depends_on, execution_order, related_seeders), or debug seeder runs (make dev-setup, SeedFixtures).
---

# Seeder Authoring (`add-seeder`)

`core.seeder` is a declarative, dependency-ordered seeding engine for multi-tenant Django apps. You describe *what* to seed (model, fields, data source, dependencies); `BaseSeeder` handles ordering, schema context and per-record transactions.

Core facts:
- Seeders are sorted with a topological sort (Kahn's algorithm) over `depends_on`; `execution_order` breaks ties.
- Each record is created inside its own `transaction.atomic()`.
- Schema isolation is handled via `core_schema_context` (`public` vs tenant schemas).
- Two registries: `seeder_registry` (everything) and `fixture_registry` (only `is_fixture = True`).

---

## 1. Step 0 - Decide the tier

| Question | Fixture (production) | Dev seeder |
| :--- | :--- | :--- |
| Must exist in production for the app to work (configs, statuses, preference types, template labels)? | Yes | No |
| Fake/realistic sample data for local, QA or CI (users, customers)? | No | Yes |
| Runs via | `SeedFixtures` (uses `fixture_registry` only) | `make dev-setup` -> `python manage.py run_dev_seeders` |

**Hard rule:** production must never receive mock data. Anything with fake emails, known passwords, or sample business records is a dev seeder, always. When unsure, it is a dev seeder.

---

## 2. Placement & naming

| | Production Fixture | Development Seeder |
| :--- | :--- | :--- |
| Python | `core/apps/<app>/fixtures/seeders.py` | `core/setup/<app>/seeders.py` |
| Data dir | `core/apps/<app>/fixtures/<model_name>/` | `core/setup/<app>/dev_<model_name>/` |
| Class name | `<Name>FixtureSeeder` (no `Dev` prefix) | `Dev<Name>Seeder` |
| `is_fixture` | `True` | `False` (default) |
| Path anchor | `settings.CORE_APP_DIR` | `settings.CORE_BASE_DIR` |

Examples: `UsersTemplateLabelFixtureSeeder`, `DevUserSeeder`, `DevCustomerSeeder`; data at `core/apps/configurations/fixtures/configuration/` and `core/setup/crm/dev_customer/customers.json`.

Never hardcode absolute or relative-to-cwd paths; always build them from `settings.CORE_APP_DIR` / `settings.CORE_BASE_DIR` so host projects with custom paths keep working.

---

## 3. Minimal template

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
        fields = ["first_name", "last_name", "business_name",
                  "customer_type", "status", "user__email"]
        tenant_type = settings.TENANT_TYPE_ORGANIZATION
        data_source = FileDataSource(
            os.path.join(settings.CORE_BASE_DIR,
                         "setup/crm/dev_customer/customers.json")
        )
        depends_on = [User]      # users are seeded first
        execution_order = 2
```

Matching data file (`customers.json`, compiled mode = a JSON array):

```json
[
  {
    "first_name": "Asha",
    "last_name": "Verma",
    "business_name": "Verma Traders",
    "customer_type": "business",
    "status": "active",
    "user__email": "asha@example.com"
  }
]
```

Rules:
1. Resolve models with the app getters (`get_user_model()`, `get_customer_model()`); never import concrete model classes.
2. Subclass `BaseSeeder` and declare `class Meta(BaseMeta)`.
3. Use only reserved domains (`example.com`, `localhost`) for fake emails.

---

## 4. `Meta` options

**Required**
- `model` - model class (via getter).
- `fields` - allow-list of keys read from each record. Keys not listed are silently ignored, so a typo or a forgotten field produces missing data, not an error.
- `data_source` - an `AbstractDataSource`, normally `FileDataSource`.

**Optional**
- `depends_on: list[type[Model]]` - models that must be seeded first. Required for every model referenced through `__` lookups or FKs.
- `execution_order: int | None` - lower runs earlier; use for deterministic ordering among independent seeders. Dependencies always win over order.
- `object_create_method` - defaults to `model._default_manager.get_or_create`. Override for custom creation (e.g. `User.objects.get_or_create_user` / `get_or_create_superuser` so passwords are hashed).
- `related_seeders: dict[str, type[BaseSeeder]]` - nested records. If a record has a dict under a relation key (e.g. `"customer_phone": {"phone": "+15550000"}`), the named seeder creates and links the child (FK, 1-1, M2M).
- `is_fixture: bool` - `True` registers the seeder in `fixture_registry` as well as `seeder_registry`.
- `tenant_type` - `settings.TENANT_TYPE_ORGANIZATION` (tenant schemas, default) or `settings.TENANT_TYPE_PUBLIC` (public schema).
- `schema_name` - pin to a specific schema, e.g. `"public"`. Prefer pinning explicitly for shared/global data; the runner may override `tenant_type` inside an active schema context, but not an explicit `schema_name`.
- Per-record `"_schema_name": "public"` - forces one record into a given schema (e.g. a global superuser).

**`__` relation lookups**: `"user__email"` in `fields` plus `{"user__email": "a@example.com"}` in data resolves `User.objects.get(email=...)` and assigns it to `user`. The referenced model must be in `depends_on`, and the target record must already exist (or be seeded earlier).

---

## 5. Data sources

```python
# Compiled: one JSON file containing an array of records (default)
FileDataSource(path_to_file.json)  # same as load_method=FileDataSource.LOAD_COMPILED

# Individual: a directory of *.json files, one record per file
FileDataSource(path_to_dir, load_method=FileDataSource.LOAD_INDIVIDUAL)
```

Use **individual** mode for large or independently-reviewed records (multi-language templates, big config blobs); use **compiled** for small flat lists.

---

## 6. Lifecycle & override points

```
seed_data()  -> loads raw records from data_source.get_data()
   for each record:
      seed()                -> opens transaction.atomic()
        validate()          -> check raw dict; raise SeederException / ValidationError
        to_internal_values()-> Field.clean(), resolve '__' lookups, build relation objects
        create()            -> persist via object_create_method and link relations
```

Override only what you need:

```python
def validate(self, data):
    if "@" not in data.get("user__email", ""):
        raise SeederException("user__email must be a valid email")
    return data

def to_internal_values(self, data):
    self.context.update({"is_admin": data.pop("is_admin", False)})
    return super().to_internal_values(data)

def create(self, data):
    # e.g. configs: skip cache writes during bulk seeding
    return self._model.set_config(
        interface_type=data.get("interface_type"),
        details=data.get("details", {}),
        name=data.get("name"),
        set_cache=False,
    )
```

Prefer `object_create_method` when you only need a different manager call; override `create()` when you need more than one call or post-processing.

---

## 7. Production fixture example

`core/apps/configurations/fixtures/seeders.py`

```python
import os
from typing import Any
from django.conf import settings
from core.apps.configurations import get_configuration_model
from core.seeder.base import BaseMeta, BaseSeeder
from core.seeder.datasource import FileDataSource


class UsersTemplateLabelFixtureSeeder(BaseSeeder):
    """Production fixture: template labels."""

    class Meta(BaseMeta):
        model = get_configuration_model()
        fields = ["name", "interface_type", "details"]
        tenant_type = settings.TENANT_TYPE_PUBLIC
        schema_name = "public"
        is_fixture = True
        execution_order = 1
        data_source = FileDataSource(
            os.path.join(settings.CORE_APP_DIR,
                         "configurations/fixtures/configuration"),
            load_method=FileDataSource.LOAD_INDIVIDUAL,
        )

    def create(self, data: dict[str, Any]):
        return self._model.set_config(
            interface_type=data.get("interface_type", "users_template_label"),
            details=data.get("details", {}),
            name=data.get("name", "Users Template Labels"),
            set_cache=False,
        )
```

---

## 8. Common mistakes

| Mistake | Consequence | Fix |
| :--- | :--- | :--- |
| Mock data in a fixture seeder | Fake records reach production | Move to `core/setup/...` as `Dev*Seeder` |
| Fixture class named with `Dev` prefix, or dev class without it | Confusing intent, reviewers misjudge safety | Follow the naming table |
| `__` lookup without `depends_on` | Lookup runs before the parent exists -> `DoesNotExist` | Add the model to `depends_on` |
| Field missing from `fields` | Value silently dropped | Add it to the allow-list |
| Importing concrete models | Breaks swappable/custom model setups | Use `get_*_model()` |
| Creating users with plain `get_or_create` | Unhashed or unusable passwords | Use `get_or_create_user` / `get_or_create_superuser` |
| Real credentials, tokens, or PII in JSON | Secrets in git | Dummy values only; read secrets from env/settings |
| Relying on `get_or_create` with all fields as lookup | Editing a JSON value inserts a new row instead of updating | Override `create()` / `object_create_method` with a stable lookup key plus `defaults` (see Verify) |

---

## 9. Checklist before finishing

- [ ] Correct tier, path, class name and `is_fixture`
- [ ] Model resolved through getter; `fields` complete
- [ ] `depends_on` lists every FK / `__` target; `execution_order` set if order matters
- [ ] Schema binding is explicit for public/global data
- [ ] Data file is valid JSON, uses dummy values, lives in the right folder
- [ ] Seeder is idempotent: running it twice creates no duplicates
- [ ] Registry test added or updated (below)
- [ ] `make dev-setup` run locally (dev seeders) or `SeedFixtures` verified (fixtures)

---

## 10. Run & test

```bash
make dev-setup                      # dev seeders
python manage.py run_dev_seeders    # same thing, direct
```

```python
from core.seeder.registry import fixture_registry, seeder_registry
from core.apps.configurations.fixtures.seeders import UsersTemplateLabelFixtureSeeder
from core.setup.users.seeders import DevUsersTemplateLabelSeeder


def test_seeder_registrations():
    assert fixture_registry.get("users_template_label_fixture_seeder") is UsersTemplateLabelFixtureSeeder
    assert seeder_registry.get("dev_users_template_label_seeder") is DevUsersTemplateLabelSeeder
    assert "dev_users_template_label_seeder" not in fixture_registry.registry


def test_seeder_is_idempotent(db):
    # run the seeder twice, assert row count is unchanged after the second run
    ...
```

Registry keys are the snake_case form of the class name.

---

## Verify against the codebase (unconfirmed assumptions)

These were inferred from the original skill's examples, not from source. Confirm and edit before relying on them:
1. Dev data folder convention: `dev_<model_name>/` (used by all examples) vs the old table's `<model_name>/`.
2. Fixture class suffix `FixtureSeeder` (used by the example) vs the old table's `<ModelName>Seeder`.
3. Whether `get_or_create` receives all extracted fields as lookup kwargs or supports `defaults`.
4. Exact precedence between explicit `schema_name` and runner schema context.
5. How seeders get registered (import side effect / autodiscovery) so new files are picked up.