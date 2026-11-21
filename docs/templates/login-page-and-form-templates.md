# Analysis: Core Login Page & Dynamic Form Templates (Lean Architecture)

## 1. Goal & Constraints
- Build a reusable core login page template (`authenticated_view.jinja`) and modular form templates (`core/templates/core/forms/`).
- Follow the design and UX of `local_data/ux_mockups/login.html` (Tenant Access Gateway, Tabbed Sign In / Sign Up, Password / OTP sub-switch, Social SSO, and security badge footer).
- Apply **Ponytail (lazy senior dev)** rules: zero bloat, reuse existing component macros from `core/components/common/`, zero inline JavaScript, use tokens from `variables.css`.

## 2. Component & File Breakdown

### A. Core Form System (`core/templates/core/forms/`)

All field templates import and wrap macros from `core/components/common/forms.jinja` to avoid duplicate CSS or diverging form logic.

1. **`base_form.jinja`** (~25 lines)
   - Macro: `base_form(action="", method="post", form_id=None, title=None, subtitle=None, submit_label="Submit", submit_variant="primary", form_errors=None, extra_classes="")`
   - Structure: `<form>` element, `{{ csrf_input }}`, optional header (`title`/`subtitle`), error summary banner (`{% if form_errors %}`), `{{ caller() }}` for fields, and standard submit button from `buttons.jinja`.

2. **Field Wrappers (`form_field_<name>.jinja`)** (5–20 lines each)
   - `form_field_text.jinja`: calls `input(type="text", ...)` from `core/components/common/forms.jinja`.
   - `form_field_email.jinja`: calls `input(type="email", ...)`.
   - `form_field_password.jinja`: calls `input(type="password", ...)`, includes an integrated password visibility toggle button with `data-password-toggle`.
   - `form_field_otp.jinja`: renders 6 individual digit input boxes (`data-otp-box`, `inputmode="numeric"`, `maxlength="1"`) with auto-advance and countdown resend anchor.
   - `form_field_checkbox.jinja`: calls `checkbox(...)`.
   - `form_field_select.jinja`: calls `select(...)`.
   - `form_field_hidden.jinja`: `<input type="hidden" name="{{ name }}" value="{{ value }}">`.

3. **`dynamic_form.jinja`** (~35 lines)
   - Macro: `dynamic_form(fields=[], action="", method="post", submit_label="Submit", form_id=None, extra_classes="")`
   - Iterates through `fields` array and renders the matching `form_field_*` based on `field.type` (defaulting to text).
   - Wraps the fields using `base_form()`.

### B. Authenticated View (`core/templates/core/views/authenticated_view.jinja`) (~120 lines)
- Extends `core/base.jinja`. Overrides `{% block sidebar %}`, `{% block header %}`, and `{% block footer %}` with clean auth-specific structure (reusing base assets, tokens, and `core.js`).
- Layout:
  1. **Brand Identity Header**: Tenant logo / Material icon, `{{ PROJECT_LABEL or 'Core Console' }}`, and "Tenant Access Gateway" subtitle.
  2. **Card Container**: Built using `card()` from `core/components/common/cards.jinja`.
  3. **Header Mode Tabs**: "Sign In" vs "Create Account", switching via declarative `data-auth-tab="signin"` and `data-auth-tab="signup"`.
  4. **Sign In Tab**:
     - Sub-segment switcher: Password vs One-Time Code (`data-auth-method="password"`, `data-auth-method="otp"`).
     - **Password Flow**: Email / identity input, Password input (with show/hide), Remember device checkbox, "Forgot password?" link, and "Sign In" submit CTA.
     - **OTP Flow**: Verified phone/email input, "Send Passcode" CTA, 6-digit challenge key input with countdown timer, and "Verify & Authorize" CTA.
     - **Social SSO Row**: Google Workspace, Apple ID, and Meta/Enterprise SSO buttons.
  5. **Create Account Tab**:
     - Administrator full name, corporate email, tenant domain prefix with `.core.internal` suffix, root password, terms checkbox, and "Provision Tenant Workspace" CTA.
  6. **Security Footer**:
     - 256-bit SSL Encrypted, Enterprise Tenant Isolation, and PCI-DSS compliance badges.
     - Links: Privacy Policy, Terms of Service, Platform Status.

### C. Client-Side Interactivity (`core/static/core/js/core.js`) (~35 lines added)
- Pure event delegation on `document.addEventListener("DOMContentLoaded")`:
  1. `[data-auth-tab]`: switches between `#auth_section_signin` and `#auth_section_signup`.
  2. `[data-auth-method]`: switches between `#auth_form_password` and `#auth_form_otp`.
  3. `[data-password-toggle]`: toggles target input between `type="password"` and `type="text"`.
  4. `[data-otp-box]`: auto-focuses next input on single-char entry, focuses previous on backspace.

### D. CSS Styles (`core/static/core/css/components.css`) (~40 lines added)
- Uses existing variables (`--color-surface-sunken`, `--color-primary`, `--radius-lg`, etc.).
- Adds scoped rules for:
  - Auth page centering canvas (`.auth-canvas`, `.auth-card`).
  - Auth tab switches (`.auth-tabs`, `.auth-tab-btn.active`).
  - OTP digit inputs (`.otp-input-group`, `.otp-digit-box`).
  - Social login grid (`.social-auth-grid`, `.social-auth-btn`).

## 3. Verification & Testing Plan
1. Unit tests in `core/tests/templates/test_jinja2_templates.py`:
   - Test rendering of `base_form`, each `form_field_*` macro, and `dynamic_form`.
   - Test `authenticated_view.jinja` renders Sign In, OTP, Signup, and Social SSO structures.
   - Verify zero inline scripts and correct presence of `data-auth-*` attributes.
2. Run `make t DIR=core/tests/templates` to ensure all existing and new tests pass.
