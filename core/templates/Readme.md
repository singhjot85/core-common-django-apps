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
│           └── api_client.js      # Fetch helper for DRF REST endpoints
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
│           │   ├── cards.jinja    # Container cards, stat/metric cards
│           │   ├── tables.jinja   # Data table, row actions, pagination
│           │   ├── badges.jinja   # Status pill, tag badges
│           │   └── forms.jinja    # Input, select, textarea, checkbox, form group
│           └── feedback/
│               ├── alerts.jinja   # Flash banners and dismissible messages
│               └── modals.jinja   # Modal dialog macro with header, body, footer slots
├── utils/
│   └── jinja2/
│       ├── backend.py             # Custom Jinja2Backend with app_dirname='templates'
│       ├── environment.py         # Jinja2 environment factory
│       ├── filters/               # Modular filters (dates.py, currency.py)
│       └── globals/               # Modular globals (urls.py)
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

## 2. Jinja2 Engine & Standard Helpers

All application UI templates use **Jinja2** via `core.utils.jinja2.Jinja2Backend`.

### Modular Environment Architecture (`core/utils/jinja2/`)
- `globals/urls.py`: `url("named_route", *args, **kwargs)` and `static("path/to/asset.css")`
- `filters/dates.py`: `format_date(val, fmt)` and `format_datetime(val, fmt)`
- `filters/currency.py`: `format_currency(val, symbol)`
- `environment.py`: Factory aggregating `CORE_GLOBALS` and `CORE_FILTERS` into the Jinja2 `Environment`.

### Standard Bindings in Templates
Every Jinja2 template automatically has access to:
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
  - **Modal Management**:
    - `Core.modal.open(modalId)`: Opens modal and disables background body scrolling.
    - `Core.modal.close(modalId)`: Closes modal and restores scrolling.
  - **Alert Management**:
    - `Core.alert.dismiss(element)`: Removes parent alert banner.
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
  - All event listeners are automatically attached on `DOMContentLoaded` by `core.js`.
