# Analysis: Model Factories across Core Apps (`docs/model-factories/analysis.md`)

## 1. Context & Motivation
Currently, unit and integration tests across `core/tests/` instantiate database models directly using `.objects.create(...)` with manual keyword arguments (85+ occurrences). This leads to repetitive boilerplate, fragile test setups whenever model fields or constraints change, and violates the repo's intended testing design (`AGENTS.md` section 9: *"No factories.py exists yet. Create one when you need it"* and `backend-pytest/SKILL.md` section 56: *"Create database objects with factories... Factories create real rows. That is the right way"*).

The goal of this initiative is to:
1. Provide first-class `factories.py` modules in every app using `factory_boy`.
2. Adhere strictly to **AGENTS.md Rule 1**: Dynamic resolution via app model getters (`User = get_user_model()`).
3. Refactor all tests across `core/tests/` to use these factories instead of raw `.objects.create(...)`.
4. Update agent instructions (`AGENTS.md`, `backend-pytest/SKILL.md`) to enforce factory usage in tests.

---

## 2. Technical Specification

### Input and Output
- **Input**: Model field parameters, overrides, and relations passed by tests.
- **Output**: Valid Django model instances created via `DjangoModelFactory` (`.create()`, `.build()`, `.build_batch()`, `.create_batch()`).

### Reuse vs New
- **Reuse**: `factory-boy` (`>= 3.3.3,<4.0.0`) is already present in `pyproject.toml` and lockfile.
- **New Modules**:
  - `core/apps/tenants/factories.py`
  - `core/apps/users/factories.py`
  - `core/apps/configurations/factories.py`
  - `core/apps/crm/factories.py`
  - `core/apps/invoices/factories.py`
  - `core/apps/integrations/factories.py`
  - `core/apps/integrations/email/factories.py`
  - `core/apps/integrations/sms/factories.py`

### Factory Inventory per App
1. **`core.apps.tenants.factories`**:
   - `TenantFactory`: `schema_name` (Sequence), `label`, `is_active=True`, `status="ready"`.
   - `DomainFactory`: `domain` (Sequence: `tenant-{n}.localhost`), `tenant` (SubFactory), `is_primary=True`.
   - `TenantBrandingFactory`: `tenant` (SubFactory).
   - `TenantContactInfoFactory`: `tenant` (SubFactory), `contact_email` (Faker).
2. **`core.apps.users.factories`**:
   - `UserFactory`: `username` (Sequence: `user_{n}`), `email` (Sequence: `user_{n}@example.com`), `phone_number` (Sequence), `is_active=True`. Supports post-generation `password`.
   - `SocialAccountFactory`: `user` (SubFactory), `provider="google"`, `uid` (Sequence).
   - `OTPLogFactory`: `recipient`, `delivery_method="email"`, `status="pending"`.
3. **`core.apps.configurations.factories`**:
   - `ConfigurationFactory`: `name` (Sequence: `config_{n}`), `version="1.0.0"`, `interface_type="system"`, `configuration={"key": "val"}`, `is_active=True`.
4. **`core.apps.crm.factories`**:
   - `CustomerFactory`: `first_name` (Faker), `last_name` (Faker), `user` (None or SubFactory), `is_active=True`.
   - `CustomerEmailFactory`: `customer` (SubFactory), `email` (Sequence), `is_primary=True`.
   - `CustomerPhoneFactory`: `customer` (SubFactory), `phone` (Sequence), `is_primary=True`.
   - `CustomerAddressFactory`: `customer` (SubFactory), `address_line_1` (Faker), `city` (Faker), `postal_code` (Faker), `country="US"`, `is_primary=True`.
   - `CustomerIdentificationFactory`: `customer` (SubFactory), `identification_type="passport"`, `identification_number` (Sequence), `status="unverified"`.
   - `CustomerPreferenceTypeFactory`: `name` (Sequence), `code` (Sequence), `data_type="boolean"`.
   - `CustomerPreferenceFactory`: `customer` (SubFactory), `preference_type` (SubFactory), `value="true"`.
5. **`core.apps.invoices.factories`**:
   - `BillingOrganizationFactory`: `name` (Sequence), `tax_id` (Sequence), `currency="USD"`.
   - `InvoicePartyFactory`: `name` (Sequence), `party_type="client"`, `billing_organization` (SubFactory).
   - `InvoicePartyEmailFactory`: `party` (SubFactory), `email` (Sequence), `is_primary=True`.
   - `InvoicePartyPhoneFactory`: `party` (SubFactory), `phone` (Sequence), `is_primary=True`.
   - `InvoicePartyAddressFactory`: `party` (SubFactory), `address_line_1` (Faker), `city` (Faker), `country="US"`.
   - `InvoiceTemplateFactory`: `template` (Faker), `interface_type="invoice"`, `version="1.0.0"`.
   - `InvoiceFactory`: `billing_organization` (SubFactory), `party` (SubFactory), `invoice_number` (Sequence: `INV-{n}`), `status="draft"`.
   - `InvoiceItemFactory`: `invoice` (SubFactory), `description` (Faker), `quantity=1`, `unit_price=Decimal("100.00")`, `amount=Decimal("100.00")`.
6. **`core.apps.integrations.factories`**:
   - `IntegrationFactory`: `label` (Sequence: `integration_{n}`), `integration_key="email"`, `mock=True`, `active=True`.
   - `CredentialsManagerFactory`: `integration` (SubFactory), `key="api_key"`.
   - `EmailLogFactory`: `recipient` (Faker), `subject` (Faker), `status="success"`, `backend="ConsoleEmailBackend"`.
   - `EmailTemplateFactory`: `subject` (Faker), `template` (Faker), `interface_type="auth"`, `version="1.0.0"`.
   - `SMSLogFactory`: `recipient` (Faker), `status="success"`, `backend="ConsoleSMSBackend"`.
   - `SMSTemplateFactory`: `template` (Faker), `interface_type="otp"`, `version="1.0.0"`.

### Database, Caching, Async & Tenancy
- **Database**: No migrations.
- **Tenancy**: Models are created in the current schema context. Tenant-scoped models (e.g. `Customer`, `Invoice`) require being created within an active tenant schema or passing tenant context where required.
- **Async & Caching**: N/A.

### Impact on Host Projects
- **Zero breaking changes**: Host projects inherit default factories and can subclass them or override model targets via their swapped models if desired.

### Documentation Impact
- `AGENTS.md`: Update Section 6 (add rule requiring factories for test model creation) and Section 9 (retire "No factories.py exists yet" gap).
- `.agents/skills/backend-pytest/SKILL.md`: Update rules to require `factories.py` imports over `.objects.create`.
- App `Readme.md` files: Note factory exports under testing section.

---

## 3. Rollout Phases (one commit per phase per `vcs-workflow`)
- **Phase 1**: Analysis & approval gate (this document).
- **Phase 2**: Implement `factories.py` in each app (`users`, `tenants`, `configurations`, `crm`, `invoices`, `integrations`).
- **Phase 3**: Refactor tests (`core/tests/users/`, `core/tests/crm/`, `core/tests/invoices/`, `core/tests/integrations*/`, etc.) to use factories.
- **Phase 4**: Update `AGENTS.md`, `backend-pytest/SKILL.md`, and module `Readme.md` files. Run full test suite & pre-commit.
