# Swappable Models (profile: `swappable_models: true`)

Skip this file entirely if the profile has `swappable_models: false`; use ordinary `models.py` then.

## Why
Django's `swappable` Meta option lets a host project replace a concrete model with its own subclass
without forking the shared app. It only works if nothing binds to the concrete class at import time.

## Rules
1. **Logic lives in the abstract class** (`models_abstract.py` or `models_abstract/`): fields, managers,
   methods, properties, `Meta` options. `Meta.abstract = True`.
2. **`models.py` holds only concrete shells**: subclass the abstract model, inherit its `Meta`, set
   `swappable = "<LABEL>_<MODEL>_MODEL"`. No new fields or methods.
3. **Never import concrete models** in admin, serializers, views, tasks, managers, or other apps.
   Use the getter exported from the app's `__init__.py`.
4. **Resolve getters once at module level** (`Plan = get_plan_model()`), not inside functions or loops.
5. **FKs use setting strings**: `to=settings.<LABEL>_<MODEL>_MODEL` or `settings.AUTH_USER_MODEL`. Never a class.
6. **Each model needs a setting** in the registry file: `<LABEL>_<MODEL>_MODEL = "<label>.<Model>"`.

## Where the concrete import IS allowed
`models.py` itself, migrations, and tests that assert the default wiring. Nothing else. `check_app.py` flags
violations.

## Layout choice
- 1-3 simple models: `models_abstract.py`
- 4+ models or complex domain: `models_abstract/` package, one module per model, re-exported from `__init__.py`
  (use `--abstract-dir`).

## Getter pattern
```python
def get_plan_model():
    return typing.cast(type["AbstractPlan"], django_apps.get_model(settings.BILLING_PLAN_MODEL, require_ready=False))
```
`TYPE_CHECKING` import of the abstract class gives IDE/mypy support without eager imports at startup.

## Pitfalls
- `swappable` key must be a real Django setting; a typo fails only at migrate time.
- Changing the swappable key after migrations exist is a breaking change for every host project.
- Circular imports: abstract models must not import from the app's `__init__.py` (it imports settings classes).
