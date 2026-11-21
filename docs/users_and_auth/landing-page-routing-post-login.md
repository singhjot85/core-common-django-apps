# Analysis: Landing Page Routing & Forwarding Post-Login

## 1. Context & User Goal
- **Requirement:** Route/forward users from `LoginView` to a `LandingPage` upon successful authentication.
- **Configurability:** Make the landing page route configurable in app/project settings.
- **Core Abstraction:** The core framework does not force a specific host application landing page yet (each consuming project will implement its own). Core must provide:
  1. An abstract, extensible way to configure the landing page URL / route name.
  2. A default fallback landing page if the consuming project hasn't configured a custom one.
  3. Automatic forwarding/redirecting post-login and guard redirects for already authenticated users.

---

## 2. Architectural Analysis

### A. Configuration Engine (`app_settings.py` & Django settings)
- **Hierarchy of Resolution:**
  1. Safe `next` query parameter (standard Django pattern: `request.GET.get("next")` / `request.POST.get("next")` validated with `url_has_allowed_host_and_scheme`).
  2. App setting: `app_settings.LANDING_PAGE_URL` in `core.apps.users.app_settings.UsersSettings`.
  3. Django global setting fallback: `getattr(settings, "LOGIN_REDIRECT_URL", None)`.
  4. Default core fallback route: `"ui-landing"` (or `"/"` / `"/dashboard/"`).
- **Resolver Utility:**
  - A clean helper: `get_landing_page_url(request=None, default=None) -> str`.
  - Supports:
    - Named URL patterns (e.g., `"dashboard"`, `"ui-landing"`, `"home"`).
    - Absolute/relative URL paths (e.g., `"/app/dashboard/"`, `"/"`).
    - Resolves via Django's `resolve_url()` with graceful fallback so an unresolvable string name does not crash the app.

### B. Default Landing Page in Core
- **Default View:** `DefaultLandingPageView(TemplateView)`
  - Renders `core/views/default_landing.jinja`.
  - Provides a clean, modern placeholder dashboard/welcome screen that:
    - Uses the standard core app shell (`core/base.jinja`) with navbar and sidebar.
    - Shows welcome card, user context (name, email, role), quick links to settings/admin, and clear guidance for developers on how to override `LANDING_PAGE_URL` in their host project settings.
    - Route name: `"ui-landing"`, exposed at `/landing/` (or `/dashboard/`).
- **Overridability:**
  - Host project can set `LOGIN_REDIRECT_URL = "my-custom-dashboard"` in `settings.py` or `CORE_USERS_SETTINGS = {"LANDING_PAGE_URL": "my-custom-dashboard"}`.
  - Core views will immediately honor that URL without modifying any core views or templates.

### C. Login View Integration (`core.apps.users.api.template_views.LoginView`)
- **Already Authenticated Guard:**
  - If an already authenticated user (`request.user.is_authenticated`) navigates to `/login/`, automatically redirect them to `get_landing_page_url(request)` (following standard Django `LoginView.redirect_authenticated_user = True`).
- **Context Injection:**
  - Provide `landing_page_url` and `next_url` in template context for `authenticated_view.jinja` so both frontend JavaScript and form actions know where to redirect upon successful auth.
- **Form Submission Support (Dual-Mode):**
  - **Traditional Server-Side POST:** `LoginView.post()` processes standard credentials, authenticates via Django's auth backend, calls `login(request, user)`, sets session cookie, and returns `HttpResponseRedirect(get_landing_page_url(request))`.
  - **Client-Side / API POST:** `core.js` handles AJAX submission to `/api/users/v1/auth/login/`, and on 200 OK receives or uses `landing_page_url` to forward `window.location.href = redirectUrl`.

---

## 3. Data & Process Analysis
- **Missing / Invalid Configuration:** If `LANDING_PAGE_URL` is an invalid route name or missing, gracefully fall back to `"ui-landing"` or `"/"`. Never raise `NoReverseMatch` to the user.
- **Open Redirect Protection:** Always sanitize any `next` parameter via `django.utils.http.url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()})`.
- **Thread & Async Safety:** Pure HTTP redirect / context logic; no background tasks or blocking I/O needed.
- **Multi-Tenant Context:** Schema-agnostic; honors the active tenant/public schema context for URL reversal.

---

## 4. Proposed Implementation Plan (Lean & Ponytail)
1. **App Setting:** Add `LANDING_PAGE_URL` to `UsersSettings` in `core/apps/users/app_settings.py` (Settings type string with fallback to `LOGIN_REDIRECT_URL` or `"ui-landing"`).
2. **URL Resolver:** Add `get_landing_page_url(request=None)` helper in `core/apps/users/utils.py` (or `template_views.py`).
3. **Default Landing View & Template:**
   - Create `core/templates/core/views/default_landing.jinja` (lean placeholder extending `core/base.jinja`).
   - Add `DefaultLandingPageView` in `core/apps/users/api/template_views.py`.
   - Wire route `path("landing/", DefaultLandingPageView.as_view(), name="ui-landing")` in `core/config/urls.py` and `core/config/public_urls.py`.
4. **Login View Post-Login Forwarding:**
   - In `LoginView`:
     - Add `redirect_authenticated_user = True` check in `dispatch()`.
     - In `get_context_data()`, supply `landing_page_url` and `next_url`.
     - Add clean `post()` method to handle session login and redirect to `landing_page_url`.
   - In `core.js` and `authenticated_view.jinja`:
     - Ensure forms include hidden `next` input if present.
     - Ensure client-side auth success redirects to `landing_page_url`.
5. **Tests:**
   - Test default landing page renders with user context.
   - Test `get_landing_page_url` with custom route names, raw URLs, and `next` parameter sanitization.
   - Test `LoginView` redirect for already-authenticated users.
   - Test post-login redirect flow.
