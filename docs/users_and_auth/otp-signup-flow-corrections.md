# Analysis: OTP Signup Flow Corrections

## 1. Requirement Summary & Goal

Revamp the user signup flow using One-Time Passwords (OTP):
1. **No separate verify button**: The button adjacent to the phone input acts as "Generate OTP" (or "Send Code"), not "Verify Phone".
2. **Atomic Verification & Registration**: Verification occurs exclusively as part of `POST auth/signup/` (e.g. `/api/users/v1/auth/signup/`).
3. **Revamped User Flow**:
   - User enters entire form data (`first_name`, `last_name`, `phone_number`, optional `email`).
   - User clicks **Generate OTP**.
   - OTP is dispatched asynchronously via background queue with `purpose="signup"`.
   - The 6-digit OTP challenge is displayed and user enters the received code.
   - User clicks **Create Account** (`POST auth/signup/`).
4. **Backend Validation (`SignupSerializer`)**:
   - Validate uniqueness: ensure no existing user with given `email`, `phone_number`, or `username` (flat error messages).
   - Validate OTP: verify submitted `otp` against cache for the destination identifier (`phone_number`).
   - If all validations pass, create the user with `is_phone_verified=True` (and unusable password if password omitted), issue JWT tokens, attach auth cookies, and return HTTP 201 Created.

---

## 2. System Analysis

- **Input Data**:
  - `first_name` (str, optional/required in UI)
  - `last_name` (str, optional/required in UI)
  - `phone_number` (str, E.164 phone string)
  - `email` (str, optional email address)
  - `username` (str, optional; automatically generated via `USERNAME_GENERATOR` strategy when omitted)
  - `password` (str, optional; unusable password set when omitted)
  - `otp` / `otp_code` (str, 6-digit passcode)
- **Input Source**:
  - Web UI: `form_otp_signup` in `core/templates/core/views/auth/otp_login.jinja` submitted via Fetch API.
  - REST API: Direct `POST /api/users/v1/auth/signup/` requests.
- **Output Contract**:
  - HTTP 201 Created: `{ "access": "<jwt>", "refresh": "<jwt>", "access_expires_in": int, "user": {...}, "redirect_url": "..." }`.
  - HTTP 400 Bad Request: Field validation errors (e.g. `{"otp": ["Invalid OTP code."]}`, `{"phone_number": ["A user with this phone number already exists."]}`).
- **Caching & Async Tasks**:
  - Dispatching OTP: uses existing `send_otp_task` dispatched asynchronously via `queue_task` to prevent blocking request threads and prevent account enumeration.
  - Verifying OTP: fast Valkey/Redis cache lookup via `OTPServiceFactory.verify_otp(identifier, code)`.
- **Database & Models**:
  - No database schema migrations required. `AbstractUser` already has `phone_number`, `email`, `username`, `is_phone_verified`, and `is_email_verified`.

---

## 3. Data & Validation Analysis

- **Duplicate Checks**:
  - `validate_username`: verifies `User.objects.filter(username__iexact=clean_username).exists()`.
  - `validate_email`: verifies `User.objects.filter(email__iexact=clean_email).exists()`.
  - `validate_phone_number`: verifies minimum 7 digits and `User.objects.filter(phone_number=clean_phone).exists()`.
- **OTP Validation**:
  - Field: `otp = serializers.CharField(max_length=10, required=False, allow_blank=True, write_only=True, default="")`.
  - When OTP is supplied (or when `phone_number` is provided without a `password` in OTP signup):
    - Identify target identifier (default to `phone_number`, fallback to `email`).
    - Verify code via `OTPServiceFactory.verify_otp(identifier=identifier, code=otp)`.
    - If verification fails, raise `serializers.ValidationError({"otp": msg})`.
    - If verification succeeds, flag `attrs["is_phone_verified"] = True` (or `is_email_verified = True`).
- **User Creation**:
  - In `create(self, validated_data)`: pop `otp` (and `otp_code`) before invoking `User.objects.create_user(**validated_data)`.
  - Generates username via configured generator if omitted.
  - Sets unusable password if password was blank.

---

## 4. Frontend & Template Analysis

1. **`core/templates/core/views/auth/otp_login.jinja`**:
   - Change `form_otp_signup` action from `otp_verify_action` to `action="{{ signup_action|default('/api/users/v1/auth/signup/') }}"`.
   - Update `btn_send_signup_otp` button label: replace `{{ labels.verify_phone }}` with `{{ labels.generate_otp|default("Generate OTP") }}`.
   - Keep `#otp_signup_challenge_wrapper` hidden until OTP is dispatched.
   - Name the OTP field `otp` (matching `SignupSerializer`).
2. **`core/static/core/js/core.js`**:
   - `checkSignupPhone`: only toggle `btn_send_signup_otp.disabled`; do NOT show the challenge box prior to clicking Generate OTP.
   - `[data-action-send-otp]`:
     - Inspect parent form; if `form_otp_signup`, pass `purpose: "signup"`.
     - Upon HTTP 202 dispatch success: show `#otp_signup_challenge_wrapper`, focus first OTP digit box, make phone input `readOnly`, and change button text to "Sent".
   - `form_otp_signup` submit handler:
     - Replace previous handler that was posting to `/auth/otp/verify/`.
     - Collect full form data (`first_name`, `last_name`, `phone_number`, `email`, `otp`).
     - Submit `POST` to form `action` (`/api/users/v1/auth/signup/`).
     - On HTTP 201: store JWT tokens, and redirect to `data.redirect_url`.
     - On error (HTTP 400): show error toast with validation details and re-enable submit button.

---

## 5. Test Strategy

1. **Serializer Tests (`core/tests/users/test_serializers.py`)**:
   - `test_signup_with_valid_otp_phone`: verifies user created with `is_phone_verified=True`.
   - `test_signup_with_invalid_otp`: verifies validation error on `otp`.
   - `test_signup_duplicate_phone_error`: verifies duplicate phone number error.
   - `test_signup_duplicate_email_error`: verifies duplicate email error.
   - `test_signup_password_flow_without_otp`: verifies username/email + password signup works without OTP.
2. **View & API Tests (`core/tests/users/test_views.py`)**:
   - `test_signup_view_with_otp_success`: validates HTTP 201 Created and JWT cookie/payload delivery.
   - `test_signup_view_with_invalid_otp_returns_400`: validates HTTP 400 Bad Request.
3. **Template & Rendering Tests**:
   - Verify `SignupView` renders the expected action URL and button text.
4. **Verification via Make**:
   - Run `make t DIR=core/tests/users` and pre-commit checks.
