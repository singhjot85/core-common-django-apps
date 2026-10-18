# Core App: Configurations (`core.apps.configurations`)

Location: [`core/apps/configurations/`](./__init__.py)

## Overview

The `configurations` app manages dynamic, version-controlled JSON configuration payloads in the database. It provides multi-layer caching, JSON schema associations, runtime choice registration, and multi-tenant schema-level configuration version tracking.

## Architecture & Models

```
InterfaceTypeChoices (Lazy Registry)
         │
 AbstractConfiguration (Versioned JSON store, cached per schema)
   ├── Configuration (Swappable via CONFIGURATIONS_CONFIGURATION_MODEL)
   └── ConfigurationSchema (Swappable via CONFIGURATIONS_CONFIGURATION_SCHEMA_MODEL)
         │ (when is_multi_tenant())
 AbstractTenantConfiguration (Pins active interface versions per tenant)
   └── TenantConfiguration (Swappable via CONFIGURATIONS_TENANT_CONFIGURATION_MODEL)
```

### Key Models ([`models_abstract.py`](models_abstract.py))

- **[`AbstractConfiguration`](models_abstract.py#L73-L181)**:

  - Inherits [`BaseVersioningModel`](../../utils/models/model_bases.py).
  - Stores configuration JSON in `details` associated with an `interface_type` and optional `schema`.
  - `get_configuration(interface_type)`: Retrieves configuration from cache, falling back to database query and repopulating cache with schema-scoped keys (`{schema}:configurations:{interface_type}`).
  - `set_config(interface_type, details)`: Updates or creates configuration records and clears/refreshes the cache.

- **[`ConfigurationManager`](models_abstract.py#L21-L71)**: Custom manager with `get_latest()` and `update_latest()` methods.
- **[`AbstractConfigurationSchema`](models_abstract.py#L183-L197)**: Holds JSON Schema specifications for validating configuration payloads.

- **[`AbstractTenantConfiguration`](models_abstract.py#L224-L311)** _(Multi-tenant only)_:
  - Manages active configuration versions for specific tenant schemas.
  - `sync_tenant_configuration(schema_name)`: Synchronizes tenant configurations with the database state across schemas.

## Model Getters & Registry

- **Swappable Model Resolvers ([`__init__.py`](__init__.py))**:
  - [`get_configuration_model()`](__init__.py#L14-L23)
  - [`get_configuration_schema_model()`](__init__.py#L26-L35)
  - [`get_tenant_configuration_model()`](__init__.py#L38-L47)
- **[`InterfaceTypeChoices`](constants.py#L3)**: Global lazy choice instance populated by domain apps during initialization.

## Quick Example

```python
from core.apps.configurations import get_configuration_model

Configuration = get_configuration_model()

# Retrieve cached configuration for an interface
config_details = Configuration.get_configuration(interface_type="CRM_PIPELINE")
```

## App Settings (`app_settings.py`)

- **`DEV_SEEDER_SETUP_PATH`**: Path to the development seeders directory (defaults to `"setup"`, anchored to `settings.CORE_BASE_DIR` or absolute path). Configurable via `settings.CORE_CONFIGURATIONS_SETTINGS["DEV_SEEDER_SETUP_PATH"]`.

## Management Commands

- **`dev_setup`** (alias: `seed_data`):
  - Validates development environment using `core.utils.checks.is_development()`.
  - Discovers all registered seeders via `core.utils.autodiscovery.AutoDiscovery` from `DEV_SEEDER_SETUP_PATH` (anchored to `settings.CORE_BASE_DIR`) and core app fixtures (`settings.CORE_APP_DIR`).
  - Triggers `SeedData().run()` to execute seeders in topological dependency order using each seeder's configured `data_source` (`FileDataSource`).
  - Executable via make target: `make dev-setup` (runs in temporary Docker container).
