# Core App: Tenants (`core.apps.tenants`)

Location: [`core/apps/tenants/`](./__init__.py)

## Overview

The `tenants` app manages multi-tenant schemas for PostgreSQL via `django-tenants`. It provides asynchronous schema provisioning through Celery, tenant domain mapping, contact metadata, branding configurations, and read-only REST endpoints.

## Schema Provisioning Lifecycle

```
Tenant Saved
    │
    ├── Generates unique `public_id` (e.g. Tenant-{label}-{uuid})
    └── Enqueues `provision_tenant_schema` via `queue_task(on_commit=True)`
            │
            ├── 1. Creates PostgreSQL schema if not exists
            ├── 2. Runs schema migrations
            └── 3. Updates TenantStatus: PROVISIONING -> READY (or FAILED)
```

## Key Models ([`models_abstract.py`](./models_abstract.py))

- **[`AbstractTenants`](./models_abstract.py#L16-L73)**:
  - Extends `TenantMixin`, [`BaseModel`](../../utils/models/model_bases.py#L89-L120), and `StatusModel`.
  - `auto_create_schema = False`: Defers schema creation from HTTP requests to background tasks.
  - `status`: Tracks tenant provisioning state using [`TenantStatus`](./constants.py#L5-L13) (`PROVISIONING`, `READY`, `FAILED`).
- **[`AbstractDomain`](./models_abstract.py#L75-L87)**: Tenant domain routing model subclassing `DomainMixin`.
- **[`AbstractTenantContactInfo`](./models_abstract.py#L89-L118)**: Structured contact information ([`TenantContactInfoChoices`](./constants.py#L15-L23): `EMAIL`, `ADDRESS`, `PHONE`).
- **[`AbstractTenantBranding`](./models_abstract.py#L120-L141)**: One-to-one tenant branding and customization store.

### Swappable Concrete Models ([`models.py`](./models.py))

- [`Tenants`](./models.py#L4-L12) (`TENANTS_TENANT_MODEL`)
- [`Domain`](./models.py#L14-L22) (`TENANTS_DOMAIN_MODEL`)
- [`TenantContactInfo`](./models.py#L24-L32) (`TENANTS_CONTACT_INFO_MODEL`)
- [`TenantBranding`](./models.py#L34-L42) (`TENANTS_BRANDING_MODEL`)

## Tasks & API

- **[`provision_tenant_schema()`](./tasks.py#L16-L48)**: Shared Celery task for background database schema creation and migration execution.
- **[`TenantBrandingViewSet`](./api/views.py#L9-L24)**: Read-only API endpoint for retrieving branding data by `tenant__label` (e.g. `/api/branding/<tenant_name>/`). `list` action is disabled.
- **Serializers ([`api/serializers.py`](./api/serializers.py))**: [`TenantSerializer`](./api/serializers.py#L12-L21), [`TenantContactInfoSerializer`](./api/serializers.py#L5-L10), and [`TenantBrandingSerializer`](./api/serializers.py#L23-L30).
- **Router ([`urls.py`](./urls.py))**: Exports `tenants_router`.
