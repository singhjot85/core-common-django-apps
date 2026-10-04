# Core Utils: Serializers

Location: [`core/utils/serializers/`](./__init__.py)

## Overview

The `serializers` subpackage provides base Django REST Framework model serializers designed to enforce read-only data contracts and permission-aware field level mutability.

## Key Serializers

### 1. Read-Only Serializers ([`base.py`](./base.py))
* **[`ReadOnlyModelSerializer`](./base.py#L8-L44)**:
  * Automatically sets `read_only=True` on all declared fields upon initialization.
  * Disables `create()` and `update()` methods by raising `rest_framework.exceptions.MethodNotAllowed`.
* **[`DynamicReadOnlyModelSerializer`](./base.py#L46-L82)**:
  * Selectively marks fields listed under `Meta.read_only_fields` as read-only.
  * Defaults to making all fields read-only if `read_only_fields` is omitted.

### 2. Permission-Based Serializers ([`permission_based.py`](./permission_based.py))
* **[`ConditionalReadOnlySerializer`](./permission_based.py#L4-L47)**:
  * Allows conditional read-only status based on request context and authentication state (e.g., fields specified in `Meta.conditional_read_only` become editable only by staff users).

## Example Usage

```python
from core.utils.serializers import ReadOnlyModelSerializer

class CustomerSummarySerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "public_id", "full_name"]
```
