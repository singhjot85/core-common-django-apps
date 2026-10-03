# Core Utils: Error Handling & Content Masking

Location: [`core/utils/error_handling/`](./__init__.py)

## Overview

The `error_handling` package provides domain exceptions and sensitive content sanitization utilities to prevent sensitive credentials, PII (emails, phone numbers), and secret tokens from leaking into logs, telemetry, and error payloads.

## Key Components

### 1. Content Masking ([`content_masking.py`](./content_masking.py))
* **[`PatternMatcher`](./content_masking.py#L45-L192)**: Pre-compiled regex engine for fast keyword matching against configured sensitive phrases with word boundary detection.
* **[`ContentMaskingUtils`](./content_masking.py#L232-L398)**:
  * `filter_sensitive_content(stringified=False, deep_search=True, **attributes)`: Recursively masks sensitive fields in dictionaries/lists.
  * `mask_email(email)`: Retains structure while obscuring username and domain prefix (e.g. `us***r@ex***.com`).
  * `mask_phone(phone)`: Obscures digits while preserving formatting.
* **[`stringify_dict()`](./content_masking.py#L205-L230)**: Serializes nested dictionaries into flat strings for telemetry.

### 2. Exceptions ([`exceptions.py`](./exceptions.py))
* **[`ObjectNotFound`](./exceptions.py#L16-L55)**: Raised when an entity is missing. Automatically masks lookup arguments when building error messages.
* **[`InvalidTypeError`](./exceptions.py#L6-L14)**: Type-mismatch exception with expected vs received details.
* **[`CycleError`](./exceptions.py#L57-L62)**: Circular dependency detection.
* **[`RegistryException`](./exceptions.py#L79-L82)**, **[`SeederException`](./exceptions.py#L65-L68)**, **[`ObjectCreatorException`](./exceptions.py#L71-L76)**.

## Example Usage

```python
from core.utils.error_handling.content_masking import ContentMaskingUtils

# Masking dictionary for logging
sanitized_data = ContentMaskingUtils.filter_sensitive_content(
    password="super_secret_password", # pragma: allowlist secret
    email="user@example.com",
    user_id=101,
)
```
