# Invoice Management App

The `invoices` app provides a robust, decoupled, and immutable invoicing framework designed to snapshot transaction data (parties, addresses, templates, line items, and taxes/fees) when issuing a bill.

## Core Scope & Architecture

- **Billing Organization (`AbstractBillingOrganization`)**:
  - Entity issuing the bill with auto-incrementing invoice sequence generation (`billing_start_sequence`, `billing_current_sequence`, `billing_suffix`).
  - Contact channels (`OrganizationEmail`, `OrganizationPhone`).
  - Tax & legal identification (`OrganizationFinancials`: Aadhaar, GSTIN, PAN).
  - Brand assets (`OrganizationAssets`: logos, stamps, signatures).
- **Invoice Party (`AbstractInvoiceParty`)**:
  - Immutable party snapshot at the time of bill issuance (`AbstractParty` attributes: names, business name).
  - Categorization via `InvoicePartyCategory` (e.g. VIP, Defaulter, Standard).
  - Optional linkage to `crm.Customer` source profile.
  - Snapshotted contact channels (`InvoicePartyEmail`, `InvoicePartyPhone`).
- **Invoicing & Address Snapshots**:
  - `InvoiceAddress`: Address snapshot extending `AbstractAddress` for billing and shipping destinations.
  - `InvoiceTemplate`: Semantic version-tracked HTML template snapshot (`BaseVersioningModel`).
  - `Invoice`: Root bill entity linking biller, party, billing/shipping addresses, template, and line entries.
- **Line Items & Taxes**:
  - `InvoiceItem`: Reusable catalog item model with inventory tracking (`current_stock`, `HSN_code`, `discount_options`).
  - `InvoiceItemEntry`: Line item snapshot capturing unit price, description, HSN code, and quantity at bill creation.
  - `InvoiceItemFee`: Tax or fee percentage (e.g., GST rate) attached directly to line entries.

## Cached Properties & Calculation Helpers

All models use `functools.cached_property` helpers for clean data access and runtime aggregation:

- **`BillingOrganization`**:
  - `primary_email`: Retrieves primary email instance for the billing entity.
  - `primary_phone`: Retrieves primary phone instance for the billing entity.
  - `financials`: Retrieves statutory tax/financial records.
  - `logo`: Retrieves the primary organization logo asset.
- **`InvoiceParty`**:
  - `primary_email`: Retrieves primary snapshotted party email.
  - `primary_phone`: Retrieves primary snapshotted party phone.
- **`InvoiceItemEntry`**:
  - `total_price`: Computes `unit_price * quantity`.
  - `total_fee_amount`: Sums calculated fee amounts across attached `InvoiceItemFee` entries.
  - `grand_total`: Computes `total_price + total_fee_amount`.
- **`InvoiceItemFee`**:
  - `fee_amount`: Calculates concrete amount from `(rate / 100) * total_price`.
- **`Invoice`**:
  - `entries`: Returns prefetched line item entries.
  - `subtotal`: Aggregates all line entry base amounts.
  - `total_fees`: Aggregates all taxes and fees across line entries.
  - `grand_total`: Aggregates `subtotal + total_fees`.

## Swappability Settings

All invoice models are swappable via Django settings in `core.config.settings.base_models`:

- `INVOICES_INVOICE_MODEL` (default: `"invoices.Invoice"`)
- `INVOICES_INVOICE_ADDRESS_MODEL` (default: `"invoices.InvoiceAddress"`)
- `INVOICES_INVOICE_TEMPLATE_MODEL` (default: `"invoices.InvoiceTemplate"`)
- `INVOICES_BILLING_ORGANIZATION_MODEL` (default: `"invoices.BillingOrganization"`)
- `INVOICES_ORGANIZATION_EMAIL_MODEL` (default: `"invoices.OrganizationEmail"`)
- `INVOICES_ORGANIZATION_PHONE_MODEL` (default: `"invoices.OrganizationPhone"`)
- `INVOICES_ORGANIZATION_FINANCIALS_MODEL` (default: `"invoices.OrganizationFinancials"`)
- `INVOICES_ORGANIZATION_ASSETS_MODEL` (default: `"invoices.OrganizationAssets"`)
- `INVOICES_INVOICE_PARTY_MODEL` (default: `"invoices.InvoiceParty"`)
- `INVOICES_INVOICE_PARTY_CATEGORY_MODEL` (default: `"invoices.InvoicePartyCategory"`)
- `INVOICES_INVOICE_PARTY_EMAIL_MODEL` (default: `"invoices.InvoicePartyEmail"`)
- `INVOICES_INVOICE_PARTY_PHONE_MODEL` (default: `"invoices.InvoicePartyPhone"`)
- `INVOICES_INVOICE_ITEM_MODEL` (default: `"invoices.InvoiceItem"`)
- `INVOICES_INVOICE_ITEM_ENTRY_MODEL` (default: `"invoices.InvoiceItemEntry"`)
- `INVOICES_INVOICE_ITEM_FEE_MODEL` (default: `"invoices.InvoiceItemFee"`)

Dynamic model getters are exported from `core.apps.invoices`:

```python
from core.apps.invoices import (
    get_invoice_model,
    get_invoice_address_model,
    get_invoice_template_model,
    get_billing_organization_model,
    get_invoice_party_model,
    get_invoice_item_model,
    get_invoice_item_entry_model,
    get_invoice_item_fee_model,
)
```

## API Endpoints & Method Policies

- **Invoice Entity Endpoints** (`urls.py` via `invoices_router`):
  - `/invoices/`: `GET` (list/retrieve) and `POST` (create). `PUT`/`PATCH`/`DELETE` are strictly blocked because issued invoices are immutable snapshots.
  - `/billing-organizations/`: Detail/create/update billing entities (with `POST .../generate-next-number/` action).
  - `/organization-emails/`: Detail/create/update organization emails (with `POST .../set-primary/`).
  - `/organization-phones/`: Detail/create/update organization phones (with `POST .../set-primary/`).
  - `/organization-financials/`: Detail/create/update statutory financials (Aadhaar, GSTIN, PAN).
  - `/organization-assets/`: Detail/create/update branding assets and logos.
  - `/invoice-parties/`: Detail/create/update snapshotted customer/vendor records.
  - `/invoice-party-categories/`: Detail/create/update customer categories (VIP, Defaulter, etc.).
  - `/invoice-party-emails/`: Detail/create/update snapshotted party emails.
  - `/invoice-party-phones/`: Detail/create/update snapshotted party phones.
  - `/invoice-addresses/`: Detail/create/update invoice address snapshots.
  - `/invoice-templates/`: Detail/create/update version-tracked HTML invoice templates.
  - `/invoice-items/`: Detail/create/update inventory item catalog.
  - `/invoice-item-entries/`: Detail/create/update line item snapshots on invoices.
  - `/invoice-item-fees/`: Detail/create/update line item taxes and fee percentages.
