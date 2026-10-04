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

- **Customer Entity Endpoints**: `DELETE` and global `GET /` (list) are disallowed across all customer resources. Detailed retrieval, creation, and updates are supported.
  - `/customers/`: Detail/create/update customer profiles (nested contacts, addresses, identifications, preferences).
  - `/customer-phones/`: Detail/create/update phone numbers (with `POST .../set-primary/`).
  - `/customer-emails/`: Detail/create/update email addresses (with `POST .../set-primary/`).
  - `/customer-addresses/`: Detail/create/update addresses (with `POST .../set-primary/`).
  - `/customer-identifications/`: Detail/create/update customer KYC/identity records.
  - `/customer-preferences/`: Detail/create/update customer preference values.
- **Preference Types Configuration**:
  - `/customer-preference-types/`: Lists and retrieves available preference type definitions (`DELETE` disallowed).
