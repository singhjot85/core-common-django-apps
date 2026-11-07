# CRM (Customer Relationship Management) App

The `crm` app handles customer onboarding, contact channels, KYC identification, and customer preferences for projects in `core-apps-django`.

## Core Scope & Responsibilities

- **Customer Profiles**: Extends `AbstractParty` (`first_name`, `middle_name`, `last_name`, `business_name`, `full_name` property) and `BaseModel` (UUID, timestamping, soft delete).
- **Contact Channels**:
  - `CustomerPhone`: Phone numbers with primary designation and contact type classification.
  - `CustomerEmail`: Email addresses with primary designation and contact type classification.
- **Addresses**:
  - `CustomerAddress`: Physical/mailing addresses extending `AbstractAddress` (`address_line_1`, `city`, `state`, `postal_code`, `country`, `full_address` property).
- **KYC & Identifications**:
  - `CustomerIdentification`: Identity records (Aadhaar, PAN, Driving License, Passport, Voter ID, GSTIN, CIN) linked to verification records via Generic Foreign Keys (`GenericForeignKey`).
- **Customer Preferences**:
  - `CustomerPreferenceType`: Definitions for preferences (`code`, `label`, `data_type`, `default_value`, `values` for choice/multi-select options).
  - `CustomerPreference`: Customer-specific preference values (`customer`, `preference_type`, `value`), validated against their type definition.

## Managers & Helper Methods

`CustomerPhone`, `CustomerEmail`, and `CustomerAddress` use `CustomerAttributeManager` with:
- `get_primary(customer)`: Retrieves the primary record for a given customer.
- `set_primary(instance_or_pk, customer=None)`: Marks the record as primary while safely resetting `is_primary=False` on other records for that customer.

## Multi-Tenant & Swappability

All CRM models are swappable via Django settings:
- `CRM_CUSTOMER_MODEL` (default: `"crm.Customer"`)
- `CRM_CUSTOMER_PHONE_MODEL` (default: `"crm.CustomerPhone"`)
- `CRM_CUSTOMER_EMAIL_MODEL` (default: `"crm.CustomerEmail"`)
- `CRM_CUSTOMER_ADDRESS_MODEL` (default: `"crm.CustomerAddress"`)
- `CRM_CUSTOMER_IDENTIFICATION_MODEL` (default: `"crm.CustomerIdentification"`)
- `CRM_CUSTOMER_PREFERENCE_TYPE_MODEL` (default: `"crm.CustomerPreferenceType"`)
- `CRM_CUSTOMER_PREFERENCE_MODEL` (default: `"crm.CustomerPreference"`)

Access concrete models dynamically via `core.apps.crm` model getters:
```python
from core.apps.crm import (
    get_customer_model,
    get_customer_phone_model,
    get_customer_email_model,
    get_customer_address_model,
    get_customer_identification_model,
    get_customer_preference_type_model,
    get_customer_preference_model,
)
```

## API Endpoints & Method Policies

- **Customer Entity Endpoints**: `DELETE` and global `GET /` (list) are disallowed across all customer resources. Detailed retrieval, creation, and updates are supported. Child attributes are nested under the customer URL; `customer` is derived from the URL path (`customer_pk`) and is read-only in mutation request bodies to prevent cross-customer data injection.
  - `/customers/`: Detail/create/update customer profiles (nested contacts, addresses, identifications, preferences).
  - `/customers/{customer_pk}/phones/`: Detail/create/update phone numbers (with `POST .../set-primary/`).
  - `/customers/{customer_pk}/emails/`: Detail/create/update email addresses (with `POST .../set-primary/`).
  - `/customers/{customer_pk}/addresses/`: Detail/create/update addresses (with `POST .../set-primary/`).
  - `/customers/{customer_pk}/identifications/`: Detail/create/update customer KYC/identity records.
  - `/customers/{customer_pk}/preferences/`: Detail/create/update customer preference values.
- **Preference Types Configuration**:
  - `/customer-preference-types/`: Lists and retrieves available preference type definitions (`DELETE` disallowed).

## Document Storage & Upload Strategies

`CustomerIdentification.document` handles KYC identity files (Aadhaar, PAN, DL, etc.). In production, files must be stored in dedicated object storage (AWS S3, Google Cloud Storage, or MinIO).

### Option 1: Django-Managed Storage (`django-storages`)
Django streams file uploads directly to the configured storage backend.

- **Configuration:**
  ```python
  STORAGES = {
      "default": {
          "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
          "OPTIONS": {
              "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
              "region_name": os.getenv("AWS_S3_REGION_NAME", "ap-south-1"),
              "default_acl": None,  # Private bucket
              "querystring_auth": True,  # Generates expiring signed URLs for retrieval
          },
      },
  }
  ```
- **Trade-offs:** Seamless integration with existing `FileField` serializers; however, large uploads stream through the Django worker process, consuming server memory and bandwidth.

### Option 2: Direct-to-Storage Presigned URLs (Recommended)
Clients upload file binaries directly to cloud object storage, bypassing the Django application server.

- **Workflow:**
  1. **Request Upload URL:** Client calls an endpoint (e.g., `POST .../identifications/upload-url/`) with document metadata (`mime_type`, `type`).
  2. **Generate Presigned URL:** Django validates permissions and generates a time-limited S3/GCS presigned `PUT` URL.
  3. **Direct Upload:** Client executes a `PUT` request with the binary payload directly to S3/GCS.
  4. **Register Identification:** Client submits the resulting object key to the nested identifications endpoint (`POST /customers/{customer_pk}/identifications/`).
  5. **Async Processing:** Background tasks (OCR/KYC validation) are queued via `queue_task()` without blocking the request thread.
- **Trade-offs:** Requires a two-step client flow, but eliminates backend I/O bottlenecks and supports horizontal scale.

### Security & Multi-Tenancy Rules
- **Tenant Isolation:** Storage keys are partitioned by schema: `<tenant_schema>/<type>/<customer_id>/<filename>`.
- **Private Access:** S3 Block Public Access must remain enabled. Identity documents contain sensitive PII and must only be accessed via expiring presigned GET URLs.
