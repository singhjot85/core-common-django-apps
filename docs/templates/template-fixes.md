# Analysis: Template Quality & Security Refactoring

## 1. System Analysis
- **Scope**: `core/templates/core/` template files (`tables.jinja`, `alerts.jinja`, `modals.jinja`, `cards.jinja`, `navbar.jinja`, `sidebar.jinja`) and corresponding tests in `core/tests/templates/test_jinja2_templates.py`.
- **Exclusion**: Mobile sidebar navigation toggle (`data-sidebar-mobile-toggle`), explicitly deferred to a separate branch for dedicated mobile compatibility work.
- **Input / Source**: Jinja2 template rendering context (Django requests, messages, models, dicts, view kwargs).
- **Output Contract**: Server-rendered valid, accessible, and secure HTML.
- **Caching**: Multi-tenant Redis caching on database loader untouched; template files are filesystem-based and compiled by Jinja2 environment.
- **Async tasks / DB changes / Cron**: N/A.

## 2. Changes Planned

### 1. `core/templates/core/components/common/tables.jinja`
- **Issue**: Cell contents piped to `|safe` unconditionally: `<td>{{ cell|safe }}</td>`.
- **Fix**: Remove `|safe` to ensure HTML auto-escaping on arbitrary tabular data. Markupsafe objects and caller blocks remain supported.

### 2. `core/templates/core/components/feedback/alerts.jinja`
- **Issue**: `message_list` checks `msg.tag` instead of Django's standard `msg.tags`. Django messages always fall back to `"info"`.
- **Fix**: Resolve tag with `msg.tags or msg.tag or "info"`. Map `"error"` tag to `"danger"` alert variant. Support string messages gracefully.

### 3. `core/templates/core/components/feedback/modals.jinja`
- **Issue 1**: `max_width="500px"` parameter accepted in macro signature but never rendered on `.modal-dialog`.
- **Fix 1**: Add `style="max-width: {{ max_width }};"` to `.modal-dialog`.
- **Issue 2**: `aria-labelledby="{{ target_id }}_title"` output unconditionally, even when `title` is omitted, causing broken accessibility references.
- **Fix 2**: Only output `aria-labelledby="{{ target_id }}_title"` if `title` is present.

### 4. `core/templates/core/components/common/cards.jinja`
- **Issue 1**: Header block checks `{% if title or header_actions %}`, dropping `subtitle` when `title` is absent.
- **Fix 1**: Check `{% if title or subtitle or header_actions %}`.
- **Issue 2**: Raw `<button>` / `<a>` and icon `<span>` duplicated in `service_card` and `telemetry_strip`.
- **Fix 2**: Import and use `icon` and `button` macros.

### 5. `core/templates/core/layout/navbar.jinja`
- **Issue**: Hardcoded fallback `"tenant-ref-id"` rendered when `page_label_secondary` is missing, along with leftover `{# AGENT: ... #}` comment.
- **Fix**: Remove leftover comment; conditionally render the secondary badge only if `page_label_secondary` is truthy. Keep mobile toggle commented out as instructed.

### 6. `core/templates/core/layout/sidebar.jinja`
- **Issue**: Unauthenticated visitor displays hardcoded "Admin User" and "admin@example.com"; empty email generates `@example.com`.
- **Fix**: For unauthenticated sessions, show "Guest" without fake emails or omit the footer card if desired. Do not generate synthetic email domains.

## 3. Testing Plan
- Update and extend `core/tests/templates/test_jinja2_templates.py`:
  - Test table cell auto-escaping prevents script injection.
  - Test `message_list` with Django `Message(tags="error", message="Failed")` produces `alert alert-danger`.
  - Test `modal` applies custom `max_width` and conditional `aria-labelledby`.
  - Test `card` renders header when only `subtitle` is passed.
  - Test `navbar` does not render placeholder `"tenant-ref-id"` when `page_label_secondary` is empty.
  - Run `make t DIR=core/tests/templates` to verify all test suites pass.
