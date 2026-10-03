# Core Utils: Models & Mixins

Location: [`core/utils/models/`](./__init__.py)

## Overview

The `models` subpackage provides standard abstract base models, soft-deletion mechanics with user tracking, semantic versioning models, and safe query retrieval helpers.

## Key Base Models ([`model_bases.py`](./model_bases.py))

* **[`BaseModel`](./model_bases.py#L89-L120)**: Primary abstract class for database entities.
  * Includes UUID primary key (`UUIDModel`), created/modified timestamps (`TimeStampedModel`), and soft delete tracking (`DeletionTrackingModel`).
  * Features `get_object(**filters)` for safe model retrieval.
* **[`BaseVersioningModel`](./model_bases.py#L154-L219)**: Version-managed model with semantic version integers (`major`, `minor`, `patch`), version resolution, and `bump_version()`.
* **[`BaseLogModel`](./model_bases.py#L134-L152)**: Status-tracking log model with [`DefaultLogStatusChoices`](./model_bases.py#L122-L132) (`created`, `in_progress`, `queued`, `succeded`, `failed`).
* **[`AbstractParty`](./model_bases.py#L9-L39)**: Reusable profile model with name breakdown and `full_name` property.
* **[`AbstractAddress`](./model_bases.py#L41-L87)**: Physical address entity with geographic coordinates and formatted address helper.

## Soft Deletion & Versioning

* **[`DeletionTrackingModel`](./soft_delete.py#L15-L122)**:
  * Extends `SoftDeletableModel` with `removed_by` FK.
  * Captures the deleting user from request context, `delete(deleted_by=user)` kwargs, or positional arguments.
* **[`SimpleVersionModelMixin`](./versioning.py#L10-L57)**:
  * Automatically synchronizes semantic `version` string (e.g., `"1.2.0"`) with individual numeric fields during `save()`.

## Query Helpers ([`helpers.py`](./helpers.py))

* **[`get_object_or_raise(model, **kwargs)`](./helpers.py#L9-L20)**: Queries model (using `available_objects` if soft-deletable) or raises sanitized `ObjectNotFound`.
* **[`safe_get_object_or_raise(model, **kwargs)`](./helpers.py#L22-L45)**: Gracefully handles duplicates (`MultipleObjectsReturned`) by falling back to model ordering and logging a warning.
* **[`filter_objects_or_raise(model, **kwargs)`](./helpers.py#L47-L64)**: Returns filtered queryset or raises `ObjectNotFound` if empty.
