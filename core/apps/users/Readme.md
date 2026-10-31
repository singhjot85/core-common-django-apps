# Users & Authentication App

The `users` app provides a modular, multi-tenant-ready authentication framework built on top of Django's default authentication mechanics. It incorporates dual-model inheritance, fine-grained swappability via `app_settings`, asynchronous OTP dispatch, and `dj_rest_auth` integration with SimpleJWT.

---

## 1. Architectural Overview & Design Principles

- **Django Auth Backend Compatibility**: By default, the app behaves identically to standard Django authentication using `django.contrib.auth.backends.ModelBackend`, Django's permission framework (`PermissionsMixin`), groups, and Django Admin.
- **Layered Swappability**:
  - **Base Model Swapping**: The user model dynamically resolves its base class (`BaseUserModel`) via `users/app_settings.py`. Inheriting projects can inject custom fields or mixins into the User model without replacing the concrete entity.
  - **Concrete Model Swapping**: Standard Django `AUTH_USER_MODEL = "users.User"` swappability is preserved for consuming projects requiring a fully custom user model.
  - **Service & Strategy Swapping**: SMS backends, username generators, and serializers are swappable via `app_settings.py`.
- **Decoupled Imports**: Following repository standards, concrete models are never imported directly. Code resolves models via dynamic getters (`get_user_model()`, etc.) exported from the app root.

---

## 2. Model Hierarchy & Conventions

The app adheres to the `models_abstract` and `models` pattern used across `core-apps-django`:

```
core/apps/users/
├── models_abstract.py   # Abstract definitions with business logic and managers
└── models.py            # Concrete models declaring swappable settings keys
```

### Models

| Model | Abstract Base Class | Key Fields & Responsibilities |
| :--- | :--- | :--- |
| **`User`** | `AbstractUser` | Inherits both `django.contrib.auth.models.AbstractUser` and `BaseUserModel` (UUID PK, created/modified timestamps, soft delete tracking, phone number, and verification flags). |
| **`SocialAccount`** | `AbstractSocialAccount` | Extends `BaseModel`. Links third-party OAuth providers (Google, Apple) to user accounts with unique provider UID and metadata JSON snapshots. |
| **`OTPLog`** | `AbstractOTPLog` | Extends `BaseLogModel`. Audit trail capturing OTP recipient, channel, purpose (login/signup), and lifecycle delivery status. |

### Dynamic Model Getters

Concrete models are resolved dynamically via `core.apps.users`:

```python
from core.apps.users import (
    get_user_model,
    get_social_account_model,
    get_otp_log_model,
    get_system_user,
)

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()
system_user = get_system_user()  # Or User.get_system_user()
```

---

## 3. Configuration & App Settings (`app_settings.py`)

All behaviors, base model bindings, and operational toggles are governed by `UsersSettings(BaseSettings)` under the `CORE_USERS_SETTINGS` project key.

### Declared Descriptors

- **`BASE_USER_MODEL`** (`SettingsType.DEFFERED_IMPORT`): Dotted path to the abstract base model class that `AbstractUser` inherits from (default: `"core.utils.models.BaseUserModel"`).
- **`SIGNUP_SERIALIZER`** (`SettingsType.IMPORT`): Serializer used for new user registration (default: `"core.apps.users.api.serializers.SignupSerializer"`).
- **`USER_DETAILS_SERIALIZER`** (`SettingsType.IMPORT`): Serializer used for user profile retrieval and updates (default: `"core.apps.users.api.serializers.UserDetailsSerializer"`).
- **`SMS_BACKEND`** (`SettingsType.IMPORT`): Adapter class responsible for SMS dispatch (default: `"core.utils.backends.sms.console.ConsoleSMSBackend"`).
- **`USERNAME_GENERATOR`** (`SettingsType.IMPORT`): Strategy callable for generating unique usernames when omitted during signup (default: `"core.utils.generators.username.generate_unique_username"` backed by `core.utils.generators.UsernameGenerator`).
- **`SYSTEM_USER_USERNAME`** (`str`, default: `"system"`): Username used for the internal audit system user provisioned via `post_migrate`.
- **`LOCKOUT_TOKEN_TIMEOUT`** (`int`, default: `86400`): Cache validity timeout (in seconds) for account lockout unlock tokens.

### Constance Runtime Flags

- **`ENABLE_PASSWORD_LOGIN`** (`bool`, default `True`): Toggles username/password login.
- **`ENABLE_OTP_LOGIN`** (`bool`, default `True`): Toggles phone and email OTP login.
- **`ENABLE_SOCIAL_LOGIN`** (`bool`, default `True`): Toggles Google and third-party social logins.
- **`ALLOW_AUTO_REGISTRATION_ON_OTP`** (`bool`, default `True`): Automatically provisions an account when an unknown phone/email verifies an OTP.
- **`OTP_EXPIRY_SECONDS`** (`int`, default `300`): Lifetime of generated OTP codes in Redis/cache.
- **`OTP_MAX_ATTEMPTS`** (`int`, default `5`): Maximum failed attempts before an OTP code is locked.
- **`OTP_LENGTH`** (`int`, default `6`): Digit count for numeric OTP codes.

---

## 4. Service Architecture & Template Patterns

- **OTP Services (`services/otp/`)**:
  - `BaseOTPService`: Abstract template method base class standardizing user existence checks, cryptographic code generation, HMAC-SHA256 hashing, TTL caching, lockout protection, and delivery audit logging to `OTPLog`.
  - `PhoneOTPService`: SMS delivery hook delegating to configured `SMS_BACKEND`.
  - `EmailOTPService`: Email delivery hook invoking Django `send_mail`.
  - `OTPServiceFactory`: Channel registry (`phone`, `email`) and dynamic strategy dispatcher.
- **Social Services (`services/social/`)**:
  - `BaseSocialAuthService`: Abstract template method base class orchestrating IDP token verification, claims normalization, `SocialAccount` association, and auto-provisioning with unusable passwords.
  - `GoogleAuthService`: Google OAuth2 / OIDC token verification via standard library `http.client`.
  - `SocialAuthServiceFactory`: Provider registry (`google`) and strategy dispatcher.
- **SMS Backends (`core/utils/backends/sms/`)**:
  - `BaseSMSBackend`: Cross-app abstract base class declaring `@abc.abstractmethod def send_sms(to, message)`.
  - `ConsoleSMSBackend`: Development backend logging SMS payloads to standard logging output.

---

## 5. Authentication Architecture & Modalities

### 1. Flexible Signup
- **Captured Information**: `first_name`, `last_name`, optional `email`, and optional `phone_number`.
- **Optional Username**: If omitted, the system generates a unique username from a combination of the user's name, email prefix, and cryptographic random characters.
- **Optional Password**: Users registering via OTP or Google have an unusable password set (`user.set_unusable_password()`). A password can be set later via standard password management endpoints.
- **Google Social Signup**: Creates user profile from Google ID token claims (`email`, `given_name`, `family_name`), sets email as verified, and associates a `SocialAccount`.

### 2. Multi-Channel Login
- **Username & Password**: Authenticates against `ModelBackend` for accounts with a usable password. Accounts created without passwords receive a descriptive message directing them to OTP or social login.
- **Phone Number OTP Login & Signup**:
  1. Client sends phone number to generate OTP (`/api/users/v1/auth/otp/sms/send/` with `purpose="login"` or `purpose="signup"`).
  2. Server returns `202 Accepted` and asynchronously dispatches OTP.
  3. Client submits phone number and 6-digit OTP code directly to `/api/users/v1/auth/otp/sms/login/` or `/api/users/v1/auth/otp/sms/signup/`.
  4. Server verifies OTP, authenticates or provisions the user account, and issues SimpleJWT token pair (`access`, `refresh`) and user profile.
- **Email OTP Login & Signup**:
  1. Client sends email address to generate OTP (`/api/users/v1/auth/otp/email/send/`).
  2. Server returns `202 Accepted` and asynchronously dispatches OTP.
  3. Client submits email address and 6-digit OTP code directly to `/api/users/v1/auth/otp/email/login/` or `/api/users/v1/auth/otp/email/signup/`.
  4. Server verifies OTP, authenticates or provisions user, and issues SimpleJWT token pair and user profile.
- **Google Social Login**: Client sends Google ID token $\rightarrow$ server validates token $\rightarrow$ authenticates or registers user $\rightarrow$ returns SimpleJWT token pair.

### 3. Asynchronous OTP Dispatch Policy
- Calling `/api/users/v1/auth/otp/sms/send/` or `/api/users/v1/auth/otp/email/send/` validates identifier syntax (returns `400 Bad Request` only on malformed phone/email syntax).
- For all valid formats, the endpoint immediately returns **`202 Accepted`** with no user existence disclosure, protecting against account enumeration and timing attacks.
- The actual user existence lookup (for login flows), OTP code generation, Redis TTL caching, and SMS/Email dispatch are processed in a Celery background task via `core.utils.tasks.queue_task`.
- Under no circumstance should external delivery calls (SMS/Email) execute directly on the main HTTP request thread; if queuing fails, the error is logged without executing blocking external calls synchronously.

### 4. Server-Side Cookie Authentication & Middleware (`JWTCookieAuthenticationMiddleware`)
- **Location**: `core.utils.middleware.JWTCookieAuthenticationMiddleware`
- **Request Authentication**:
  - Automatically inspects incoming `request.COOKIES` for the access token (`access_token`, configurable via `settings.ACCESS_TOKEN_COOKIE_NAME`).
  - If valid and active, sets `request.user` to the authenticated user instance.
  - If expired or invalid on non-exempt routes, terminates request processing immediately with `404 Not Found` and deletes the expired cookies.
  - On exempt routes (`settings.JWT_AUTH_EXEMPT_PATHS`, defaulting to `/login/`, `/signup/`, `/register/`, `/api/users/v1/auth/`, `/static/`, `/favicon.ico`), permits access to the unauthenticated handler and attaches deletion headers to the response so stale cookies are evicted by the browser.
- **Outgoing Response Delegation**:
  - When authentication views complete (e.g. `PasswordAuthViewSet`, `EmailOTPAuthViewSet`, `SMSOTPAuthViewSet`, `GoogleLoginView`), the middleware detects issued tokens from `response.data` or `request._auth_tokens`.
  - Sets client-readable `access_token` and HttpOnly `refresh_token` (`settings.REFRESH_TOKEN_COOKIE_NAME`) cookies with `SameSite=Lax`.
- **Safe In-App Redirects**:
  - Validates `next` parameters across query parameters and JSON/form bodies using `url_has_allowed_host_and_scheme` to prevent open redirects.
  - When `app_settings.ONLY_ALLOW_IN_APP_REDIRECTS` is enabled (default `True`), redirects are restricted strictly to in-app endpoints hosted by the application.
  - Falls back directly to `settings.LOGIN_REDIRECT_URL` (or `"/"`).

---

## 6. API Surface & Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/users/v1/auth/password/signup/` | `POST` | Registers new user via username and password; returns SimpleJWT tokens and user profile. |
| `/api/users/v1/auth/password/login/` | `POST` | Password-based login with account lockout protection. |
| `/api/users/v1/auth/otp/sms/send/` | `POST` | Asynchronously generates and queues OTP dispatch to phone number (`202 Accepted`). |
| `/api/users/v1/auth/otp/sms/signup/` | `POST` | Atomically verifies phone OTP and provisions user account; returns SimpleJWT tokens. |
| `/api/users/v1/auth/otp/sms/login/` | `POST` | Authenticates existing user via verified phone OTP. |
| `/api/users/v1/auth/otp/email/send/` | `POST` | Asynchronously generates and queues OTP dispatch to email (`202 Accepted`). |
| `/api/users/v1/auth/otp/email/signup/` | `POST` | Atomically verifies email OTP and provisions user account; returns SimpleJWT tokens. |
| `/api/users/v1/auth/otp/email/login/` | `POST` | Authenticates existing user via verified email OTP. |
| `/api/users/v1/auth/unlock/` | `GET` | Validates unlock token and clears account lockout. |
| `/api/users/v1/auth/social/google/` | `POST` | Exchanges Google ID token for SimpleJWT tokens. |
| `/api/users/v1/auth/token/refresh/` | `POST` | Refreshes SimpleJWT access token. |
| `/api/users/v1/auth/logout/` | `POST` | Invalidates / blacklists refresh token. |
| `/api/users/v1/auth/user/` | `GET`, `PUT`, `PATCH` | Retrieves and updates current user profile. |
| `/api/users/v1/auth/password/change/` | `POST` | Changes password for authenticated user. |
| `/api/users/v1/auth/password/reset/` | `POST` | Initiates password reset flow. |
| `/api/users/v1/auth/password/reset/confirm/` | `POST` | Confirms password reset with token. |

---

## 7. UI Template Architecture & Session Shell

The users app provides modular templates under `core/templates/core/views/`:

| Template / View | Role & Responsibility |
| :--- | :--- |
| **`core/views/authenticated_view.jinja`** | Base layout shell for all authenticated views. Manages JWT cookies (`access_token`, `refresh_token`), watches token expiry, blocks the page with a modal overlay on session timeout, and routes back to login. |
| **`core/views/core_login_template.jinja`** | Gateway login page hosting a top-level switcher between **Password** and **OTP** methods, housing toast messages and security badges. |
| **`core/views/auth/username_login.jinja`** | Username & password login form + signup tab, live remaining attempt warnings, and social SSO buttons. |
| **`core/views/auth/otp_login.jinja`** | Phone/email OTP dispatch (with readonly freeze), 6-digit box auto-advance with clipboard suggestion, and verified phone signup. |

### Security & Token Dynamics

- **JWT Lifetime Jitter**: SimpleJWT access tokens are issued with a randomized lifetime between **65% and 75%** of `ACCESS_TOKEN_LIFETIME` (e.g. 100 mins base $\rightarrow$ 65 to 75 mins) to prevent synchronized expiration stampedes.
- **Zero-Enumeration Security**: Failed logins always return generic errors (`"Username or password combination is incorrect."` or `"Incorrect OTP."`) with remaining attempt counts without disclosing user existence.
- **Account Lockout & Unlock**: After exhausting attempts, OTP cache is invalidated, the account is locked, and an async task dispatches a secure 24-hour one-time unlock link email (`/api/users/v1/auth/unlock/?token=...`).
- **Database `<module>_template_label` Configuration & Multi-Language Fixtures**: Form labels across all auth templates (`Email`, `Password`, `First Name`, `Last Name`, buttons, tabs) are managed by `core/utils/labels.py` backed by the core `Configuration` model (`interface_type="users_template_label"`). Priority is:
  1. Backend-provided labels (passed via view `labels = {...}` or context `labels={...}`).
  2. Database-backed / cached `Configuration` (`users_template_label`) extracting the project's current UI language (`settings.UI_LANGUAGE` or `LANGUAGE_CODE`).
  3. Static centralized i18n template defaults (`DEFAULT_AUTH_LABELS`) if DB configuration is unmigrated, missing, or unreachable.
  4. Automatic humanized title-case fallback for unregistered keys.
- **Fixtures & Seeders**:
  - Production Fixture: `core/apps/configurations/fixtures/configuration/users_template_label.json` containing multi-language mapped labels (`en`, `es`, `fr`).
  - Production Fixture Seeder: `UsersTemplateLabelFixtureSeeder` in `core/apps/configurations/fixtures/seeders.py` (`is_fixture = True`).
  - Development Seeder: `DevUsersTemplateLabelSeeder` in `core/setup/users/seeders.py` (`is_fixture = False`).
  - Enforces `set_cache=False` during persistence to prevent cache stampedes.
