# Analysis: Refactoring `authenticated_view.jinja`, Modular Login Templates, Account Lockout & JWT Jitter

## 1. Executive Summary & Goals
This refactor decomposes authentication templates into reusable, single-responsibility components and elevates `authenticated_view.jinja` into the base authenticated template shell for all protected views in the framework.

Key Deliverables:
1. **`username_login.jinja`**: Username & password login + signup, social SSO buttons, attempt counter, and account lockout handling.
2. **`otp_login.jinja`**: Phone/email OTP login + multi-field signup (First Name, Last Name, Phone OTP verification, optional Email), clipboard paste support, auto-enable submit, attempt counter.
3. **`core_login_template.jinja`**: Gateway template with high-level switcher toggling between `username_login` and `otp_login`.
4. **`authenticated_view.jinja`**: Reusable base authenticated shell that seeds all protected views with JWT cookie management, token expiry monitoring, full-screen session timeout overlay dialog, and return-to-login routing.
5. **JWT Token Jitter**: Enforce token lifetime jitter so tokens are issued randomly between 65% and 75% of the configured lifetime.
6. **Account Lockout & Unlock Flow**:
   - Invalidate OTP and cache tracking upon exhausting max attempts.
   - Lock user account (`is_active=False` or dedicated lock state).
   - Async queue task to send email with a signed one-time account unlock link.
   - One-time unlock verification view/endpoint.

---

## 2. Component & Template Architecture

```
core/templates/core/
├── views/
│   ├── authenticated_view.jinja    # Base shell for all authenticated/protected views
│   │                               # (manages JWT cookies, expiration watcher, timeout modal)
│   ├── core_login_template.jinja   # Standalone login page with method switcher (Password vs OTP)
│   └── auth/
│       ├── username_login.jinja    # Username/password login + signup tab + social SSO
│       └── otp_login.jinja         # Phone/email OTP dispatch, 6-digit box, verified signup
```

### A. `username_login.jinja`
- **Tabs**: Switcher on top for [Sign In] and [Create Account] (default: Sign In).
- **Sign In Fields**:
  - `username` (required, text)
  - `password` (required, password with toggle)
  - Remaining attempts indicator banner (renders above submit button when attempts < max).
  - Submit button (initiates API call to `/api/users/v1/auth/login/`).
- **Social Login**: Clean SSO icon links/buttons (Google, Apple, Meta).
- **Error & Lockout Handling**:
  - Displays API errors in a toast/snackbar.
  - On exhausting attempts: shows lockout notification ("Account locked due to too many failed attempts. An unlock link has been emailed to you.").

### B. `otp_login.jinja`
- **Tabs**: Switcher on top for [Sign In] and [Create Account] (default: Sign In).
- **Sign In Fields**:
  - `email_or_phone` input + "Send OTP" button.
  - On 200 OK: input becomes `readonly`, styled with disabled/grey state, and OTP box group appears.
  - 6-digit OTP input:
    - Clipboard suggestion on clicking 1st box (`navigator.clipboard.readText()`).
    - Auto-advance on input, backspace retreat.
    - Submit button remains disabled (`disabled`, greyed out) until all 6 digits are entered.
  - Remaining attempts indicator above submit button.
  - Submit button triggers `/api/users/v1/auth/otp/verify/`.
- **Sign Up Fields**:
  - `first_name` (required) & `last_name` (required) in a 2-column grid.
  - `phone_number` (required) + "Verify Phone" button (dispatches OTP and unlocks 6-digit verification).
  - `email` (optional).
  - Submit button creates the user account once phone is verified.

### C. `core_login_template.jinja`
- Extends `core/base.jinja`.
- Renders the brand header (logo, title, subtitle).
- Provides top-level method switcher: **Username & Password** vs **One-Time Code (OTP)**.
- Mounts `username_login.jinja` and `otp_login.jinja` cleanly.
- Renders `.auth-footer` (security badges and legal links).

### D. `authenticated_view.jinja` (The Protected View Shell)
- Extends `core/base.jinja` (or wraps the application shell).
- Injects client-side authentication engine (`Core.authSession`):
  1. **Cookie Management**: Reads/writes `core_access_token` and `core_refresh_token` from `document.cookie`.
  2. **Token Expiry Watcher**:
     - Decodes JWT payload `exp` timestamp in JavaScript.
     - Sets a timer before expiration (and intercepts HTTP 401 in `Core.api`).
     - On expiry: activates full-screen blocking overlay (`.session-timeout-overlay`), displays a modal dialog ("Your session has expired. Please log in again to continue."), and provides a "Return to Login" button redirecting to `LOGIN_URL` (with `?next=<current_path>`).
- Any protected view (e.g., `dashboard.jinja`, `settings.jinja`, `tenant_list.jinja`) uses `{% extends "core/views/authenticated_view.jinja" %}`.

---

## 3. Backend Logic & Services Analysis

### A. JWT Token Jitter (65% – 75%)
- **Location**: `core/apps/users/api/views.py` inside `get_jwt_tokens_for_user(user)` (and any token generation service).
- **Algorithm**:
  - Retrieve base lifetime `base_lifetime = api_settings.ACCESS_TOKEN_LIFETIME` (default e.g. 60 or 100 minutes).
  - Calculate `jitter_ratio = secrets.SystemRandom().uniform(0.65, 0.75)`.
  - Calculate `jittered_seconds = int(base_lifetime.total_seconds() * jitter_ratio)`.
  - Set `refresh.access_token.set_exp(lifetime=datetime.timedelta(seconds=jittered_seconds))`.
  - Return tokens + `access_expires_in` (seconds) in response.
  - Set HTTP cookies (`core_access_token`, `core_refresh_token`) on response for seamless SSR & SPA compatibility.

### B. Attempt Tracking, Account Lockout & Zero-Enumeration Messaging
- **Cache Keys**:
  - `{schema}:auth_attempts:{identifier}`: tracks failed password or OTP attempts.
  - `{schema}:account_lock:{identifier}`: flags locked status.
- **Zero-Enumeration Security Rules**:
  - **Username/Password flow**:
    - Never reveal if a username exists or not.
    - On failure, always return generic message: `"Username or password combination is incorrect."` along with `remaining_attempts`.
  - **Phone/Email OTP flow**:
    - On OTP request, always return success (or HTTP 202 Accepted) regardless of whether the account exists, allowing the UI to transition seamlessly to the 6-digit input step.
    - On OTP verification failure, always return generic message: `"Incorrect OTP."` along with `remaining_attempts`.
- **Lockout Mechanism**:
  - When `failed_attempts >= max_attempts` (default 5):
    1. Invalidate OTP from cache: `cache.delete(...)`.
    2. If user exists in DB:
       - Set `user.is_active = False` (or set lockout flag).
       - Generate secure one-time unlock token in cache (24h TTL): `{schema}:unlock_token:{token} -> user_id`.
       - Queue Celery task `send_account_unlock_email_task(user_id=..., unlock_token=...)` via `queue_task(..., on_commit=False)`.
    3. Return consistent lockout message without leaking account existence:
       ```json
       {
         "error": "account_locked",
         "message": "Account locked due to too many failed attempts. If an account is associated with this identity, an unlock link has been emailed to you.",
         "remaining_attempts": 0
       }
       ```
  - When `failed_attempts < max_attempts`:
    - Return generic error with `remaining_attempts: max_attempts - attempts`.


### C. Account Unlock Flow
- **Endpoint**: `/api/users/v1/auth/unlock/` (or UI endpoint `/auth/unlock/`).
- Validates the one-time token from cache.
- Re-enables the user (`user.is_active = True`, clears lockout flags and failed attempt counts).
- Redirects user to `/login/` with a success message banner ("Your account has been successfully unlocked. Please sign in.").

---

## 4. Open Points & Design Decisions for Feedback

1. **Token Storage Strategy**:
   - Store tokens in both `document.cookie` (for server-rendered templates / navigations) and return in API response body (for API clients). Should cookies be configured with `SameSite=Lax` and configurable `Secure` flag?
2. **Email Backend for Unlock Link**:
   - We will use the existing core email adapter infrastructure (`core.utils.backends.email` / Celery task `queue_task`) to dispatch the unlock notification.
3. **Lockout Trigger on Unknown Identifiers**:
   - If an identifier doesn't exist in the database, we track attempts by identifier in cache and return identical error messages / remaining attempts to prevent user enumeration attacks.
