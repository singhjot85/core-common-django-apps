# Core Templates & Frontend Architecture Guide

This module defines the template-driven frontend architecture for the core framework. It provides a modular, component-based, server-rendered UI built with **Jinja2**, CSS Custom Properties (Variables), and lightweight JavaScript, designed for plug-and-play consumption by submoduling projects.

---

## 1. Architectural Philosophy & Directory Layout

### Core Foundation vs App-Scoped Bundles vs Consuming Projects

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Consuming Project Layer                         │
│   (sample_project/templates/pages/dashboard.jinja, custom overrides)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ imports & extends
┌───────────────────────────────────▼────────────────────────────────────┐
│                       Domain App Template Bundles                      │
│   core/apps/crm/templates/crm/...                                      │
│   core/apps/tenants/templates/tenants/...                              │
│   core/apps/invoices/templates/invoices/...                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ relies on
┌───────────────────────────────────▼────────────────────────────────────┐
│                         Core UI Foundation                             │
│   core/templates/core/base.jinja                                       │
│   core/templates/core/components/ (buttons, tables, cards, modals, ...)│
│   core/static/core/ (variables.css, base.css, components.css, core.js) │
└────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
core/
├── static/
│   └── core/
│       ├── css/
│       │   ├── variables.css      # All CSS variables (theme, colors, spacing, typography)
│       │   ├── base.css           # Base reset, typography, responsive utilities
│       │   └── components.css     # Component-specific CSS rules
│       └── js/
│           ├── core.js            # Base utilities (CSRF token, toast messages, modal helpers)
│           └── service.js         # Core data & API service layer for DRF endpoints
├── templates/
│   ├── Readme.md                  # This specification and developer guide
│   └── core/
│       ├── base.jinja             # Master HTML page shell
│       ├── layout/
│       │   ├── navbar.jinja       # Global top navigation bar
│       │   ├── sidebar.jinja      # App switcher / modular sidebar navigation
│       │   └── footer.jinja       # Global page footer
│       └── components/
│           ├── common/
│           │   ├── icons.jinja    # Google Material Symbols icon macro
│           │   ├── buttons.jinja  # Button, button group, icon button macros
│           │   ├── cards.jinja    # Container cards, stat/metric cards, gauge & service cards, banners, telemetry strips
│           │   ├── tables.jinja   # Data table, row actions, pagination
│           │   ├── badges.jinja   # Status pill, tag badges
│           │   └── forms.jinja    # Input, select, textarea, checkbox, form group
│           └── feedback/
│               ├── alerts.jinja   # Flash banners and dismissible messages
│               └── modals.jinja   # Modal dialog macro with header, body, footer slots
│       ├── forms/                 # Reusable form builder and specialized field macros
│       │   ├── base_form.jinja    # Form container (CSRF, header, errors, submit button)
│       │   ├── dynamic_form.jinja # Schema-driven dynamic form builder
│       │   ├── form_field_text.jinja
│       │   ├── form_field_email.jinja
│       │   ├── form_field_password.jinja
│       │   ├── form_field_otp.jinja
│       │   ├── form_field_checkbox.jinja
│       │   ├── form_field_select.jinja
│       │   └── form_field_hidden.jinja
│       └── views/                 # Ready-to-use core views
│           └── authenticated_view.jinja # End-to-end multi-flow auth view (Login, Signup, OTP, SSO)
├── utils/
│   └── jinja2/
│       ├── backend.py             # Custom Jinja2Backend with app_dirname='templates'
│       ├── environment.py         # Jinja2 environment factory
│       ├── filters/               # Modular filters (dates.py, currency.py)
│       └── globals/               # Modular globals (urls.py)
│   └── labels.py                  # Centralized i18n translations & LabelDict proxy
└── apps/
    ├── crm/
    │   └── templates/
    │       └── crm/
    │           ├── crm.jinja                    # Full-page CRM management view
    │           └── components/
    │               ├── customer_table.jinja     # Customer list table component
    │               ├── customer_card.jinja      # Customer profile card
    │               └── customer_phone.jinja     # Customer phone management
    └── tenants/
        └── templates/
            └── tenants/
                ├── tenants.jinja                # Full-page Organization management
                └── components/
                    ├── tenant_card.jinja        # Organization profile card
                    └── member_table.jinja       # Organization members list
```

---

## 2. Jinja2 Engine, Loaders & Environments

The platform maintains a strict separation between **trusted application UI templates** and **dynamic, user-editable database templates**.

### 1. Trusted Application UI Templates (`TEMPLATES` backend)
- **Engine**: Configured via `core.utils.jinja2.Jinja2Backend` in Django settings.
- **App Dirs**: `app_dirname = "templates"` ensures templates are autodiscovered across installed apps (e.g. `core/templates/` and `<app>/templates/`).
- **Loader**: Automatically uses `jinja2.FileSystemLoader` pointing to project and app template directories.
- **Environment**: Initialized via `core.utils.jinja2.environment.jinja2_environment`.
- **Bindings & Context**: Full request context, CSRF token helpers (`csrf_input`, `csrf_token`), static/url resolution (`url`, `static`), messages framework, and format filters (`format_date`, `format_currency`).

### 2. Dynamic Database Templates & Sandboxing (`core.utils.jinja2`)
- **Loader (`SafeDatabaseLoader`)**:
  - Dynamically resolves templates from database models inheriting `BaseTemplateModel`.
  - Supports colon identifiers (`app:model:interface`) and virtual URIs (`db://app/model/interface`).
  - Implements multi-tenant Redis caching via `connection.schema_name`.
  - Gracefully falls back to filesystem templates when no database override exists.
- **Sandbox (`jinja2_sandboxed_environment`)**:
  - Built on `jinja2.sandbox.ImmutableSandboxedEnvironment` to prevent Server-Side Template Injection (SSTI).
  - Enforces `StrictUndefined` so missing placeholders raise errors immediately.
  - Exposes only sanitized filters (`CORE_SAFE_FILTERS`).
- **Render Helpers**:
  - `render("template_name", context)`: Safely renders a database or sandboxed file template. Context must only be plain primitives or dictionaries, never live ORM model instances.
  - `render_block("template_name", "block_name", context)`: Renders an individual named block (e.g., `{% block subject %}` in an email).

### Standard Bindings in Application UI Templates
Every Jinja2 UI template automatically has access to:
- `url("named_route", *args, **kwargs)`: Reverse Django URL routing.
- `static("path/to/asset.css")`: Static asset URL resolution.
- `csrf_input`: Standard HTML hidden CSRF token input tag.
- `csrf_token`: Raw CSRF token string (for JavaScript fetch headers).
- `request`: Current HTTP request object (including `request.user` and `request.tenant`).
- `messages`: Django messages framework iterator.
- `format_date(val)` / `format_datetime(val)` / `format_currency(val)`: Usable both as filters (`{{ val|format_date }}`) and as functions (`{{ format_date(val) }}`).
- `icon("icon_name", size=20)`: Google Material Symbols icon component.


---

## 3. Rules for Adding New Components, Pages, or App Templates

Follow these strict design rules whenever adding or modifying frontend templates:

### Rule 1: Always Use `.jinja` Extension
- Core and domain templates must use the `.jinja` extension.
- This prevents collision with Django's default DTL engine (which remains active for Django Admin and DRF browsable API).

### Rule 2: Strict Namespacing
- **Core components**: Place inside `core/templates/core/components/<category>/<component>.jinja`.
- **Domain app components**: Place inside `core/apps/<app>/templates/<app>/components/<component>.jinja`.
- **Domain app full views**: Place inside `core/apps/<app>/templates/<app>/<view_name>.jinja`.
- **Never** place templates directly under `templates/` without an app/domain folder namespace.

### Rule 3: Component Macro Design Standard
Components must be declared as Jinja2 `{% macro %}` blocks with:
1. Explicit parameter lists with default values.
2. An optional `extra_classes=""` argument to allow styling customization by the caller.
3. An optional `attrs={}` or `**kwargs` for custom HTML attributes.
4. Support for `caller()` slots where flexible inner HTML content is needed:

```jinja
{# Example: core/templates/core/components/common/buttons.jinja #}
{% macro button(label=None, variant="primary", size="md", type="button", href=None, icon=None, extra_classes="", disabled=False) %}
  {% set base_class = "btn btn-" ~ variant ~ " btn-" ~ size ~ (" " ~ extra_classes if extra_classes else "") %}
  {% if href %}
    <a href="{{ href }}" class="{{ base_class }}" role="button" {% if disabled %}aria-disabled="true" tabindex="-1"{% endif %} {{ kwargs|xmlattr }}>
      {% if icon %}<span class="btn-icon">{{ icon|safe }}</span>{% endif %}
      {% if label %}{{ label }}{% endif %}
      {% if caller %}{{ caller() }}{% endif %}
    </a>
  {% else %}
    <button type="{{ type }}" class="{{ base_class }}" {% if disabled %}disabled{% endif %} {{ kwargs|xmlattr }}>
      {% if icon %}<span class="btn-icon">{{ icon|safe }}</span>{% endif %}
      {% if label %}{{ label }}{% endif %}
      {% if caller %}{{ caller() }}{% endif %}
    </button>
  {% endif %}
{% endmacro %}
```

### Rule 4: Design Tokens & CSS Variables (`variables.css`)
- **Never** hardcode hex colors or arbitrary pixel values in component CSS.
- Always use CSS custom properties defined in `variables.css`:
  - Colors: `var(--color-primary)`, `var(--color-primary-hover)`, `var(--color-bg)`, `var(--color-surface)`, `var(--color-text)`, `var(--color-border)`
  - Spacing: `var(--spacing-xs)`, `var(--spacing-sm)`, `var(--spacing-md)`, `var(--spacing-lg)`, `var(--spacing-xl)`
  - Radii: `var(--radius-sm)`, `var(--radius-md)`, `var(--radius-lg)`
  - Typography: `var(--font-family-base)`, `var(--font-size-sm)`, `var(--font-size-base)`, `var(--font-size-lg)`
- **Dark Theme & Multi-Tenant White-Labeling**:
  - Dark theme tokens are declared under `[data-theme="dark"]` and `@media (prefers-color-scheme: dark)`.
  - Dynamic tenant white-labeling can be achieved by overriding these root variables per tenant.

### Rule 5: Modularity & Customization in Consuming Projects
Consuming projects (such as `sample_project` or customer microservices) can consume UI in two ways:
1. **Full-Page App View**:
   ```jinja
   {% extends "crm/crm.jinja" %}
   {% block page_title %}Custom CRM Dashboard{% endblock %}
   ```
2. **Cherry-Picking Component Macros into Custom Layouts**:
   ```jinja
   {% extends "core/base.jinja" %}
   {% from "core/components/common/cards.jinja" import stat_card %}
   {% from "crm/components/customer_table.jinja" import customer_table %}
   {% from "tenants/components/tenant_card.jinja" import tenant_card %}

   {% block content %}
     <div class="dashboard-grid">
       {{ tenant_card(tenant) }}
       {{ customer_table(customers) }}
     </div>
   {% endblock %}
   ```

### Rule 6: Client-Side Interactivity Standard (`core.js` API)
- JavaScript in `core/static/core/js/core.js` provides centralized, lightweight vanilla JS primitives:
  - **Sidebar Management**:
    - `Core.sidebar.toggle()`: Toggles desktop sidebar collapse (persisting preference to `localStorage`).
    - `Core.sidebar.collapse()` / `Core.sidebar.expand()`: Explicit desktop sidebar state setters.
    - `Core.sidebar.toggleMobile()` / `Core.sidebar.openMobile()` / `Core.sidebar.closeMobile()`: Controls mobile drawer visibility (`.open` class).
  - **Theme Management**:
    - `Core.theme.get()`: Returns active theme (`'dark'` or `'light'`).
    - `Core.theme.set('dark' | 'light' | 'auto')`: Sets active theme and persists to `localStorage`.
    - `Core.theme.toggle()`: Toggles between light and dark themes.
  - **Modal Management**:
    - `Core.modal.open(modalId)`: Opens modal and disables background body scrolling.
    - `Core.modal.close(modalId)`: Closes modal and restores scrolling.
  - **Alert Management**:
    - `Core.alert.dismiss(element)`: Removes parent alert banner.
  - **Auth & Forms Management**:
    - `Core.auth.switchTab(tabKey)`: Switches between Sign In and Create Account views.
    - `Core.auth.switchMethod(methodKey)`: Switches between Password and OTP authentication sub-methods.
    - `Core.auth.togglePassword(btn)`: Toggles password field masking between `password` and `text`.
  - **REST API Client**:
    - `Core.api.get(url)`, `Core.api.post(url, data)`, `Core.api.patch(url, data)`, `Core.api.delete(url)`: Standard fetch wrapper auto-injecting CSRF token headers and parsing JSON payloads.

### Rule 7: Zero Inline JavaScript Anti-Pattern
- **CRITICAL ANTI-PATTERN — Inline JavaScript & Ad-Hoc DOM Queries**:
  - **NEVER** write inline JavaScript handlers (such as `onclick="..."`, `onchange="..."`) or raw DOM selectors (such as `document.querySelector('.app-sidebar').classList.toggle(...)`) directly inside Jinja2 templates or macro components.
  - **Why?** Inline scripts violate Content Security Policy (CSP), bypass centralized event delegation, cause hard-to-debug state inconsistencies, and pollute template readability.
- **Correct Pattern — Declarative Data Attributes & Central Event Delegation**:
  - Always wire UI components to interactive behaviors using declarative `data-*` attributes:
    - `data-sidebar-toggle`: Desktop sidebar collapse toggle.
    - `data-sidebar-mobile-toggle`: Mobile navigation drawer toggle.
    - `data-modal-target="modal-id"`: Triggers opening the target modal.
    - `data-modal-close`: Triggers closing the target/parent modal.
    - `data-alert-dismiss`: Dismisses and removes the parent alert banner.
    - `data-auth-tab="signin|signup"`: Switches authentication top-level tab.
    - `data-auth-method="password|otp"`: Switches sign-in sub-method.
    - `data-password-toggle="field-id"`: Toggles password visibility on the referenced input.
    - `data-otp-group`: Auto-advances focus across 6 segmented challenge digits.
  - All event listeners are automatically attached on `DOMContentLoaded` by `core.js`.

---

## 4. Form Templates & Authentication Views

### Forms System (`core/templates/core/forms/`)

The forms architecture provides lightweight, composable wrappers around the base input macros in `core/components/common/forms.jinja`, ensuring visual consistency and centralized styling without duplicate code.

#### 1. `base_form.jinja`
Form wrapper providing standard HTML `<form>`, CSRF token, optional header, error callout, and submit CTA.
```jinja
{% from "core/forms/base_form.jinja" import base_form %}

{% call base_form(action="/login/", method="post", title="Sign In", submit_label="Continue") %}
  {{ form_field_email("email", label="Work Email", required=True) }}
  {{ form_field_password("password", label="Password", required=True) }}
{% endcall %}
```

#### 2. Individual Field Macros (`form_field_<type>.jinja`)
- `form_field_text.jinja`: Standard single-line text input.
- `form_field_email.jinja`: Email input with type validation.
- `form_field_password.jinja`: Password input with integrated show/hide toggle button (`data-password-toggle`).
- `form_field_otp.jinja`: 6-digit challenge input with auto-advance and automatic synchronization with a hidden `<input>` value.
- `form_field_checkbox.jinja`: Custom-styled checkbox.
- `form_field_select.jinja`: Dropdown select menu with options array.
- `form_field_hidden.jinja`: Hidden input element for tokens or state.

#### 3. `dynamic_form.jinja`
Schema-driven form engine that accepts a list of field specifications and dispatches to the corresponding field template:
```jinja
{% from "core/forms/dynamic_form.jinja" import dynamic_form %}

{% set fields = [
  {"name": "full_name", "type": "text", "label": "Full Name", "required": true},
  {"name": "email", "type": "email", "label": "Email Address", "required": true},
  {"name": "role", "type": "select", "label": "Role", "options": [{"value": "admin", "label": "Administrator"}, {"value": "member", "label": "Member"}]},
  {"name": "agree_terms", "type": "checkbox", "label": "I accept terms of service"}
] %}

{{ dynamic_form(fields=fields, action="/register/", submit_label="Create Account") }}
```

### Authentication View (`core/templates/core/views/authenticated_view.jinja`)

A ready-to-use authentication page that extends `core/base.jinja` and replaces navigation chrome with a focused, centered gateway card.

- **Capabilities**:
  - Tabbed interface switching between **Sign In** and **Create Account**.
  - Sub-method toggle between **Password** and **One-Time Passcode (OTP)**.
  - Social Single Sign-On (SSO) buttons for Google Workspace, Apple ID, and Enterprise identity providers.
  - Security badges in footer (256-bit SSL, Tenant Isolation, PCI-DSS compliance).
- **Interactivity**: 100% declarative via data attributes (`data-auth-tab`, `data-auth-method`, `data-password-toggle`, `data-otp-group`). Zero inline JavaScript.
- **Customization**:
  - Context variables: `PROJECT_LABEL`, `brand_logo_url`, `terms_url`, `privacy_url`, `status_url`, `social_providers`.
  - Blocks: `{% block auth_header %}`, `{% block auth_card %}`, `{% block auth_footer %}`.
