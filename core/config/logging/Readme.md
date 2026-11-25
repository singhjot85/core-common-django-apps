# Logging Configuration

Centralized, structured logging configuration for the core framework and host projects.

## Purpose
Provides declarative dictionary logging configuration (`dictConfig`) tailored for multi-tenant Django applications and Celery workers. Enforces sensitive data and PII masking, minimizes console clutter, and routes performance metrics, package informational logs, and errors to dedicated rotating log files.

## Log Destinations & Layout

All log files reside directly in the directory configured by `BACKEND_LOG_DIRECTORY` (defaults to `logs/`):

| Destination | Target | Log Level | Description |
| --- | --- | --- | --- |
| `console` | `stdout` | Dynamic (`APP_LOG_LEVEL`) | Terminal output colorized by level. Restricted to app-level code, whitelisted packages (`django.server`, `celery`), and all `ERROR`/`CRITICAL` events. Suppresses autoreload and DB queries. |
| `file_info` | `logs/info.log` | `INFO` | Informational logs from external packages and application code. Suppresses `django.utils.autoreload` polling noise. |
| `file_requests` | `logs/requests.log` | `INFO` | HTTP requests made to backend, recording method, path, status, latency, IP, user, and schema context. |
| `file_performance` | `logs/perf.log` | `DEBUG` | Dedicated performance metrics: database queries (`django.db.backends`), cache queries (`django.core.cache`), Celery task telemetry (`celery.task`), and API request latency. |
| `file_error` | `logs/errors.log` | `ERROR` | System-wide error and critical log records. |
| `mail_admins` | Admin Email | `ERROR` | Production-only error reporting dispatched to `ADMINS`. |

## Settings & Environment Variables

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `BACKEND_LOG_DIRECTORY` | `str` | `logs` | Directory path where log files are created. |
| `BACKEND_LOG_LEVEL` | `str` | `INFO` | Base application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `PERFORMANCE`). |
| `BACKEND_LOGFILE_BYTES` | `int` | `5242880` (5MB) | Maximum file size before rotating (keeps files small for IDE performance). |
| `BACKEND_LOGFILE_BACKUPS` | `int` | `5` | Number of rotated log backups preserved per destination. |

## Filters & Security

- **SensitiveContentFilter**: Scans messages and argument payloads to automatically mask passwords, tokens, API keys, and PII using `ContentMaskingUtils`.
- **ConsoleNoiseFilter**: Filters terminal stream output to keep developer shells uncluttered, allowing only app logs, whitelisted packages, and errors.
- **SkipAutoreloadFilter**: Drops repetitive file-watching events from `django.utils.autoreload`.

## Gotchas

- **Database queries (`django.db.backends`)**: Queries are captured at `DEBUG` level and routed exclusively to `logs/perf.log` with `propagate=False`, keeping the terminal clean while preserving performance diagnostics.
- **Production fallback**: In production environments (`DJANGO_ENV="production"` with `DEBUG=False`), file handlers fall back to console output for containerized logging best practices.
