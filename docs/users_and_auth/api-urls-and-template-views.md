# Analysis: API URLs Auto-Discovery & User Authentication Template Views

## 1. Context & Objectives
The user has started wiring automated URL configuration for tenant, public, and project apps in `core/utils/urls.py` and root URL configurations in `core/config/urls.py` and `core/config/public_urls.py`.
The objective is to:
1. **Review and fix** the URL auto-discovery functions (`build_tenant_app_urlpatterns`, `build_public_app_urlpatterns`, `build_app_urlpatterns`).
2. Add thorough **docstrings**, type annotations, and error resilience.
3. Build **Template Views** (`LoginView`, `SignupView`, `RegisterView`, `ForgotPasswordView`) in `core/apps/users/api/template_views.py` (and `template_view.py` compatibility alias) utilizing the previously built `authenticated_view.jinja` template.
4. Wire both the API endpoints (`<base_url>/api/...`) and the Template UI endpoints (`<base_url>/#/...` / `<base_url>/...`).
5. Write complete **unit tests** and verify with `make t`.
6. Update documentation.

## 2. Code Review of User's Wired URL Logic

### Issue 1: `TypeError: unsupported operand type(s) for -: 'list' and 'list'`
- **Location**: `core/utils/urls.py` (lines 7-12, 27-32)
- **Problem**: Python `list` does not support subtraction `-`. `settings.DJANGO_TENANT_PRIVATE_APPS` and `settings.SHARED_DJANGO_APPS` are lists. Executing this raises `TypeError`.
- **Solution**: Compute exclusion using set subtraction or list comprehension:
  ```python
  excluded = set(
      getattr(settings, "SHARED_DJANGO_APPS", [])
      + getattr(settings, "TENANT_ONLY_DJANGO_APPS", [])
      + getattr(settings, "SHARED_EXTRA_DEPENDENCIES", [])
      + getattr(settings, "TENANT_ONLY_EXTRA_DEPENDENCIES", [])
  )
  tenant_apps = [app for app in getattr(settings, "DJANGO_TENANT_PRIVATE_APPS", []) if app not in excluded]
  ```

### Issue 2: `ModuleNotFoundError: No module named '<app>.url'`
- **Location**: `core/utils/urls.py` (lines 20, 40, 53)
- **Problem**: `include(f"{dotted_app_path}.url")` looks for `url.py`. In this repository and Django standard practice, URL modules are named `urls.py`. Furthermore, apps without a `urls.py` module (e.g. `core.apps.configurations`) crash Django startup.
- **Solution**: Use `f"{dotted_app_path}.urls"`. Check `importlib.util.find_spec(urls_module)` before attempting `include()`, so apps without URLs are safely skipped.

### Issue 3: `ImproperlyConfigured: url_patterns vs urlpatterns`
- **Location**: `core/config/urls.py` and `core/config/public_urls.py`
- **Problem**: Variables are named `url_patterns = [...]` instead of Django's required `urlpatterns = [...]`. Django's URL resolver fails to find any URL patterns.
- **Solution**: Rename to `urlpatterns`.

### Issue 4: Nested Quote Syntax in F-Strings
- **Location**: `core/utils/urls.py` (lines 18, 38, 51)
- **Problem**: `f"{prefix}/{dotted_app_path.split(".")[-1]}/{version}/"` uses inner double-quotes inside a double-quoted f-string.
- **Solution**: Use single-quotes: `f"{prefix}/{dotted_app_path.split('.')[-1]}/{version}/"`.

## 3. Template Views Architecture (`core/apps/users/api/template_views.py`)

### Requirements:
- Views to implement: `LoginView`, `SignupView`, `RegisterView`, `ForgotPasswordView`.
- Location: `core/apps/users/api/template_views.py` (with `template_view.py` alias).
- Base Class: Standard Django `TemplateView` (extending or using Jinja2 backend).
- Template: `core/views/authenticated_view.jinja`.

### View Details:
1. **`LoginView`**:
   - `initial_tab = "signin"`
   - `initial_method = "password"`
   - Provides action endpoints: `login_action`, `otp_send_action`, `otp_verify_action`.
2. **`SignupView`**:
   - `initial_tab = "signup"`
   - Provides action endpoint: `signup_action`.
3. **`RegisterView`**:
   - Direct alias/subclass of `SignupView`.
4. **`ForgotPasswordView`**:
   - `initial_tab = "signin"`
   - `initial_method = "password"`
   - Context flag `show_forgot_password_modal = True` or dedicated reset flow context.

## 4. URL Wiring & Conventions

Following the convention:
- `<base_url>/api/...` -> Backend API endpoints (e.g., `/api/users/v1/...`, `/api/crm/v1/...`)
- `<base_url>/admin/...` -> DjangoAdmin (`/admin/`)
- `<base_url>/#/...` / `<base_url>/...` -> UI/Template endpoints:
  - Root `path("", LoginView.as_view(), name="ui-root")` serves the frontend gateway (supporting `#` SPA client hash-routing).
  - Explicit UI paths:
    - `path("login/", LoginView.as_view(), name="ui-login")`
    - `path("signup/", SignupView.as_view(), name="ui-signup")`
    - `path("register/", RegisterView.as_view(), name="ui-register")`
    - `path("forgot-password/", ForgotPasswordView.as_view(), name="ui-forgot-password")`

## 5. Testing Plan
1. Unit tests for `core/utils/urls.py`:
   - `test_build_tenant_app_urlpatterns`
   - `test_build_public_app_urlpatterns`
   - `test_build_app_urlpatterns`
   - Graceful skip when an app lacks a `urls.py`.
2. Unit tests for `core/apps/users/api/template_views.py`:
   - `LoginView` renders `authenticated_view.jinja` with signin context.
   - `SignupView` and `RegisterView` render with signup context.
   - `ForgotPasswordView` renders correctly.
   - Reverse URL lookups (`ui-login`, `ui-signup`, `ui-register`, `ui-forgot-password`).
3. Verification via `make t DIR=core/tests`.
