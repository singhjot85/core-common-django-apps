# CRM (Customer Relationship Management) App

The `crm` app handles customer onboarding and relationship tracking for projects in `core-apps-django`.

## Core Scope & Responsibilities

- **Customer Profiles**: Extends `AbstractParty` (`first_name`, `middle_name`, `last_name`, `business_name`, `full_name` property) and `BaseModel` (UUID, timestamping, soft delete).
- **Contact Channels**:
  - `CustomerPhone`: Phone numbers with primary designation and type classification.
  - `CustomerEmail`: Email addresses with primary designation and type classification.
- **Addresses**:
  - `CustomerAddress`: Physical/mailing addresses extending `AbstractAddress` (`address_line_1`, `city`, `state`, `postal_code`, `country`, `latitude`, `longitude`, `full_address` property).
- **KYC & Identifications**:
  - `CustomerIdentification`: Identity documents (Aadhaar, PAN, Driving License, Passport, Voter ID, GSTIN, CIN) linked to verification records via Generic Foreign Keys (`GenericForeignKey`).

## Managers & Helper Methods

`CustomerPhone`, `CustomerEmail`, and `CustomerAddress` use a specialized manager (`CustomerAttributeManager`) with:
- `get_primary(customer)`: Retrieves the primary contact/address record for a given customer.
- `set_primary(instance_or_pk, customer=None)`: Marks the given record as primary while safely resetting `is_primary=False` on other records for that customer.

## Multi-Tenant & Swappability

All CRM models are swappable via Django settings:
- `CRM_CUSTOMER_MODEL` (default: `"crm.Customer"`)
- `CRM_CUSTOMER_PHONE_MODEL` (default: `"crm.CustomerPhone"`)
- `CRM_CUSTOMER_EMAIL_MODEL` (default: `"crm.CustomerEmail"`)
- `CRM_CUSTOMER_ADDRESS_MODEL` (default: `"crm.CustomerAddress"`)
- `CRM_CUSTOMER_IDENTIFICATION_MODEL` (default: `"crm.CustomerIdentification"`)

Access concrete models dynamically via:
```python
from core.apps.crm import (
    get_customer_model,
    get_customer_phone_model,
    get_customer_email_model,
    get_customer_address_model,
    get_customer_identification_model,
)
```

## API Endpoints

- `/customers/`: List, retrieve, create, update, soft-delete customer profiles.
- `/customer-phones/`: Manage customer phone numbers.
- `/customer-emails/`: Manage customer email addresses.
- `/customer-addresses/`: Manage customer addresses.
- `/customer-identifications/`: Manage customer KYC/identity records.
