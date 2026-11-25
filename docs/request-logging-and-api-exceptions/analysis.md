# Analysis: Request Logging Middleware & API Exception Handler

## 1. Context & Motivation
To facilitate frontend (UI) and mobile (Android) developers during local development, backend requests need to be systematically logged to files without shell clutter.
Additionally, unhandled view exceptions currently crash to default HTML 500s or unformatted errors; a simple, graceful DRF `APIException` handler is needed to ensure structured JSON responses are returned to API consumers.

---

## 2. Technical Architecture & Decisions

### 2.1 Request Logging & Performance Telemetry
- **Handler & Logger additions in `core/config/logging`**:
  - Handler `FILE_REQUESTS` in `CoreLoggingHandlers`: maps to `logs/requests.log` with `RotatingFileHandler` (using existing `APP_LOGFILE_BYTES` and `APP_LOGFILE_BACKUP_COUNT`).
  - Logger `core.requests`: mapped to `FILE_REQUESTS`, log level `INFO`, `propagate=False`.
  - Perf Handler & Logger: `FILE_PERF` already maps to `logs/perf.log`. Logger `performance` / `perf` routes to `FILE_PERF`.
- **Request Logging Middleware (`core.config.middlewares.request_logging.RequestLoggingMiddleware`)**:
  - Placed in `core/config/middlewares/request_logging.py`.
  - Configured as the first middleware in local development (`core/config/settings/local.py`) so it accurately times request lifecycle across all downstream middlewares and views.
  - Captures: HTTP method, path, query parameters (masked), status code, response time in ms, remote IP address, authenticated user ID/username (or anonymous), and tenant schema name (from `connection.schema_name` if multi-tenant).
  - Performance telemetry: Dispatches execution time and route data to `performance` logger (`FILE_PERF`).
  - Security & PII protection (Rule 11): Sanitizes query params and request metadata via `ContentMaskingUtils.filter_sensitive_content`. Masks headers such as `Authorization` and `Cookie`.
  - Fail-safe: Middleware must never crash an application request if log formatting/file I/O fails.

### 2.2 API Exception Handler (`core.config.api_exception_handler.api_exception_handler`)
- Placed in `core/config/api_exception_handler.py`.
- Configured in `REST_FRAMEWORK["EXCEPTION_HANDLER"]`.
- Calls default DRF `rest_framework.views.exception_handler(exc, context)`.
- If DRF handles it (`response is not None`):
  - Passes through formatted response.
- If DRF does not handle it (`response is None`):
  - `ObjectDoesNotExist` / `core.exceptions.ObjectNotFound`: Returns `404 Not Found` with `{"detail": str(exc), "code": "not_found"}`.
  - Django `ValidationError`: Returns `400 Bad Request` with `{"detail": exc.messages if hasattr(exc, "messages") else str(exc), "code": "validation_error"}`.
  - Unhandled / generic `Exception`:
    - Logs error and full traceback via `logging.getLogger("django.request")`.
    - Returns `500 Internal Server Error` with `{"detail": "An unexpected error occurred. Please try again later.", "code": "internal_server_error"}`.

---

## 3. Plan & Phases (per `vcs-workflow`)
- **Phase 1: Analysis & Approval Gate** (this document).
- **Phase 2: Logging Config Updates**:
  - Add `FILE_REQUESTS` to `CoreLoggingHandlers` in `core/config/logging/handlers.py`.
  - Add `core.requests` logger to `core/config/logging/loggers.py`.
- **Phase 3: Middleware & Exception Handler Implementation**:
  - Implement `RequestLoggingMiddleware` and `JWTCookieAuthenticationMiddleware` in `core/config/middlewares/`.
  - Implement `api_exception_handler` in `core/config/api_exception_handler.py`.
  - Wire into `MIDDLEWARE` in `core/config/settings/local.py` (as first middleware) and `REST_FRAMEWORK["EXCEPTION_HANDLER"]` in `core/config/settings/base.py`.
- **Phase 4: Tests, Docs & Verification**:
  - Tests for `RequestLoggingMiddleware` in `core/tests/utils/test_middleware.py`.
  - Tests for `api_exception_handler` in `core/tests/utils/test_error_handling.py`.
  - Unit tests for new logging config in `core/tests/config/test_logging.py`.
  - Run full test suite (`make t`) and pre-commit (`poetry run pre-commit run --all-files`).
