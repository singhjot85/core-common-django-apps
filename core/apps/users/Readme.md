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
)

User = get_user_model()
SocialAccount = get_social_account_model()
OTPLog = get_otp_log_model()
```

---

## 3. Configuration & App Settings (`app_settings.py`)

All behaviors, base model bindings, and operational toggles are governed by `UsersSettings(BaseSettings)` under the `CORE_USERS_SETTINGS` project key.

### Declared Descriptors

- **`BASE_USER_MODEL`** (`SettingsType.DEFFERED_IMPORT`): Dotted path to the abstract base model class that `AbstractUser` inherits from (default: `"core.utils.models.BaseUserModel"`).
- **`SIGNUP_SERIALIZER`** (`SettingsType.IMPORT`): Serializer used for new user registration (default: `"core.apps.users.api.serializers.SignupSerializer"`).
- **`USER_DETAILS_SERIALIZER`** (`SettingsType.IMPORT`): Serializer used for user profile retrieval and updates (default: `"core.apps.users.api.serializers.UserDetailsSerializer"`).
- **`SMS_BACKEND`** (`SettingsType.IMPORT`): Adapter class responsible for SMS dispatch (default: `"core.apps.users.services.otp.ConsoleSMSBackend"`).
- **`USERNAME_GENERATOR`** (`SettingsType.IMPORT`): Strategy callable for generating unique usernames when omitted during signup (default: `"core.utils.generators.username.generate_unique_username"` backed by `core.utils.generators.UsernameGenerator`).

### Constance Runtime Flags

- **`ENABLE_PASSWORD_LOGIN`** (`bool`, default `True`): Toggles username/password login.
- **`ENABLE_OTP_LOGIN`** (`bool`, default `True`): Toggles phone and email OTP login.
- **`ENABLE_SOCIAL_LOGIN`** (`bool`, default `True`): Toggles Google and third-party social logins.
- **`ALLOW_AUTO_REGISTRATION_ON_OTP`** (`bool`, default `True`): Automatically provisions an account when an unknown phone/email verifies an OTP.
- **`OTP_EXPIRY_SECONDS`** (`int`, default `300`): Lifetime of generated OTP codes in Redis/cache.
- **`OTP_MAX_ATTEMPTS`** (`int`, default `5`): Maximum failed attempts before an OTP code is locked.
- **`OTP_LENGTH`** (`int`, default `6`): Digit count for numeric OTP codes.

---

## 4. Authentication Architecture & Modalities

### 1. Flexible Signup
- **Captured Information**: `first_name`, `last_name`, optional `email`, and optional `phone_number`.
- **Optional Username**: If omitted, the system generates a unique username from a combination of the user's name, email prefix, and cryptographic random characters.
- **Optional Password**: Users registering via OTP or Google have an unusable password set (`user.set_unusable_password()`). A password can be set later via standard password management endpoints.
- **Google Social Signup**: Creates user profile from Google ID token claims (`email`, `given_name`, `family_name`), sets email as verified, and associates a `SocialAccount`.

### 2. Multi-Channel Login
- **Username & Password**: Authenticates against `ModelBackend` for accounts with a usable password. Accounts created without passwords receive a descriptive message directing them to OTP or social login.
- **Phone Number OTP Login**:
  1. Client sends phone number.
  2. Server returns `202 Accepted` and asynchronously verifies the account and dispatches OTP.
  3. Client verifies OTP code.
  4. Server issues SimpleJWT token pair (`access`, `refresh`) and user profile.
- **Email OTP Login**:
  1. Client sends email address.
  2. Server returns `202 Accepted` and asynchronously verifies the account and dispatches OTP.
  3. Client verifies OTP code.
  4. Server issues SimpleJWT token pair and user profile.
- **Google Social Login**: Client sends Google ID token $\rightarrow$ server validates token $\rightarrow$ authenticates or registers user $\rightarrow$ returns SimpleJWT token pair.

### 3. Asynchronous OTP Dispatch Policy
- Calling `/api/users/auth/otp/send/` validates identifier syntax (returns `400 Bad Request` only on malformed phone/email syntax).
- For all valid formats, the endpoint immediately returns **`202 Accepted`** with no user existence disclosure, protecting against account enumeration and timing attacks.
- The actual user existence lookup, OTP code generation, Redis TTL caching, and SMS/Email dispatch are processed in a Celery background task via `core.utils.tasks.queue_task`.

---

## 5. API Surface & Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/users/auth/signup/` | `POST` | Registers new user; returns SimpleJWT tokens and user profile. |
| `/api/users/auth/login/` | `POST` | Standard username/password login via `dj-rest-auth` + SimpleJWT. |
| `/api/users/auth/logout/` | `POST` | Invalidates / blacklists refresh token. |
| `/api/users/auth/token/refresh/` | `POST` | Refreshes SimpleJWT access token. |
| `/api/users/auth/user/` | `GET`, `PUT`, `PATCH` | Retrieves and updates current user profile. |
| `/api/users/auth/password/change/` | `POST` | Changes password for authenticated user. |
| `/api/users/auth/password/reset/` | `POST` | Initiates password reset flow. |
| `/api/users/auth/password/reset/confirm/` | `POST` | Confirms password reset with token. |
| `/api/users/auth/otp/send/` | `POST` | Asynchronously dispatches OTP via phone or email (`202 Accepted`). |
| `/api/users/auth/otp/verify/` | `POST` | Verifies OTP and returns SimpleJWT tokens. |
| `/api/users/auth/social/google/` | `POST` | Exchanges Google ID token for SimpleJWT tokens. |
