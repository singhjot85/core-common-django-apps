# Users App Core Cleanup Analysis

## 1. Context & Scope
Cleanup the `users` app to eliminate backwards-compatibility aliases and the `BASE_USER_MODEL` dynamic inheritance anti-pattern.

Target files:
- `core/apps/users/api/serializers/__init__.py`
- `core/apps/users/app_settings.py`
- `core/apps/users/models_abstract.py`
- `core/utils/models/base_models/user_base.py`
- `core/utils/models/base_models/__init__.py`
- `core/utils/models/__init__.py`
- `core/apps/users/Readme.md`
- Test files: `core/tests/users/test_serializers.py`, `core/tests/users/test_app_settings.py`, `core/tests/users/test_models.py`

## 2. Analysis Checklist
- **Input and output:** N/A (refactoring internal class definitions, module exports, and model inheritance; no change to API contract or DB schemas).
- **Reuse vs new:** No new models or services. `AbstractUser` inherits directly from `DjangoAbstractUser` and `BaseModel`.
- **Database:** No schema alterations; `AbstractUser` maintains the identical concrete field definitions (`phone_number`, `is_phone_verified`, `is_email_verified`, plus `BaseModel` UUID, timestamps, soft-delete fields).
- **Caching, async, cron:** N/A.
- **Failure policy per case:** N/A.
- **Retries:** N/A.
- **Logging:** N/A.
- **Tenancy:** `User` remains shared/tenant dual-registered per architecture.
- **Data:** N/A (no fixture or seeder changes needed).
- **Settings:** Remove `BASE_USER_MODEL` descriptor from `UsersSettings`. Point `SIGNUP_SERIALIZER` default to `core.apps.users.api.serializers.PasswordSignupSerializer`.
- **Libraries vs utils:** Remove dead `BaseUserModel` from `core/utils/models/`.
- **Backup need:** No DB migrations or mutations. Backup is not strictly required, but available via `make db-dump`.
- **Docs impact:** Update `core/apps/users/Readme.md` to remove `BASE_USER_MODEL` descriptor and base-model swapping notes, and update serializer descriptor defaults.

## 3. Implementation Phases
1. **Phase 1: Serializers cleanup (`__init__.py`)**
   - Clean up imports in `core/apps/users/api/serializers/__init__.py` (remove `import x as x`, add clean `__all__`).
   - Remove `SignupSerializer = PasswordSignupSerializer` and `LoginSerializer = PasswordLoginSerializer`.
   - Update `app_settings.SIGNUP_SERIALIZER` to reference `PasswordSignupSerializer`.
   - Update callers in `core/tests/users/test_serializers.py` and `test_app_settings.py`.
2. **Phase 2: Remove `BASE_USER_MODEL` & `BaseUserModel`**
   - Remove `BASE_USER_MODEL` setting descriptor from `core/apps/users/app_settings.py`.
   - Directly declare `phone_number`, `is_phone_verified`, `is_email_verified`, and `full_name` property on `AbstractUser` in `core/apps/users/models_abstract.py`, inheriting `(DjangoAbstractUser, BaseModel)`.
   - Remove `core/utils/models/base_models/user_base.py` and prune exports in `core/utils/models/`.
   - Update `core/tests/users/test_models.py` and `test_app_settings.py`.
3. **Phase 3: Docs and validation**
   - Update `core/apps/users/Readme.md`.
   - Run tests (`make t TEST_DIR=core/tests/users`).
   - Run pre-commit checks.
