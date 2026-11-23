# Analysis: Logging Configuration Cleanup

## Problem Statement
Current logging produces too much clutter on the console and organizes log files into nested subdirectories with large file sizes (50MB). The user requires:
1. Shell/console: Only app-level logs and essential package logs (Django server, Celery lifecycle, errors). No DB query or autoreload spam.
2. `logs/` directory directly containing clean, unnested files:
   - `logs/info.log`: INFO-level logs from external packages (excluding autoreload).
   - `logs/perf.log`: Performance telemetry, including DB queries (`django.db.backends`), cache queries, Celery task metrics/errors, and custom perf logs.
   - `logs/errors.log`: Error and critical level logs across app and external packages.
3. Manageable file sizes: Reduce default max log file size (from 50MB to 5MB with rotation) to prevent IDE crashes when viewing logs.

## Decision Matrix

### Input and Output
- **Input**: Environment variables (`BACKEND_LOG_DIRECTORY`, `BACKEND_LOG_LEVEL`, `BACKEND_LOGFILE_BYTES`, `BACKEND_LOGFILE_BACKUPS`) and log records emitted by Python `logging`.
- **Output**:
  - Console: Clean, colored terminal output for app logs, necessary package logs, and errors.
  - `logs/info.log`: Rotating file for INFO level records from packages and app.
  - `logs/perf.log`: Rotating file for database queries (`django.db.backends`), cache queries, Celery task perf, and performance records.
  - `logs/errors.log`: Rotating file for ERROR and CRITICAL records.

### Reuse vs New
- **Reuse**:
  - `SensitiveContentFilter` (PII masking).
  - `ColoredConsoleFormatter` (colorized terminal formatting).
  - `create_log_config` & `get_logging_config` factories.
  - Enum pattern in `CoreLoggingHandlers`.
- **New / Modified**:
  - `SkipAutoreloadFilter`: Excludes noisy `django.utils.autoreload` log records.
  - Flat log file layout: `LOG_DIR / f"{name}.log"` without nested subfolders (`info.log`, `perf.log`, `errors.log`).
  - Dedicated loggers for `django.db.backends`, `django.core.cache`, `celery.task`, and `perf`/`performance` routed to `file_perf`.
  - Package-specific logger levels and propagation settings to keep shell noise minimal.
  - `APP_LOGFILE_BYTES` default lowered from 50MB to 5MB (`5 * 1024 * 1024`).

### Database
- N/A. No migrations or database schema changes.

### Caching, Async, Cron
- Caching: `django.core.cache` logs routed to `logs/perf.log`.
- Async: `celery` lifecycle logs on console/info; `celery.task` execution/timing logs routed to `logs/perf.log`.
- Cron: N/A.

### Failure Policy Per Case
- Misconfigured log levels or directory creation errors raise `ImproperlyConfigured` or fall back cleanly during dictionary configuration.

### Retries
- N/A.

### Logging Context
- PII/Secrets masked via `SensitiveContentFilter`.

### Tenancy
- N/A. Logging is process-wide infrastructure.

### Data
- N/A. No fixtures or seed data.

### Settings
- `BACKEND_LOG_DIRECTORY`: Default `"logs"`.
- `BACKEND_LOG_LEVEL`: Default `"INFO"` (was `ERROR`).
- `BACKEND_LOGFILE_BYTES`: Default `5 * 1024 * 1024` (5MB).
- `BACKEND_LOGFILE_BACKUPS`: Default `5`.

### Libraries vs Utils
- Logging lives in `core/config/logging/`.

### Backup Need
- N/A. No database state touched.

### Docs Impact
- Add `core/config/logging/Readme.md` to document logging architecture, destinations, loggers, and env vars.
