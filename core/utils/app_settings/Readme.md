# LLD: `core.app_settings`

> Location: `core/utils/app_settings` <br/>

---

## What

`core.app_settings` is the shared framework every app's `app_settings.py` builds on. `app_settings` is a subpackage of the `core` app — it is not a separately installed app of its own.

It owns four setting types:

- `Setting`
- `Constance`
- `Configuration`

It also houses a `BaseSettings` container that every app's `<App>Settings` subclasses, plus the general-purpose helpers behind app-settings **autodiscovery** and **autoregistration**. Constance registration — walking every app's `app_settings` instance and wiring its `Constance` fields into `django-constance` at startup — is currently the one concrete autoregistration mechanism built on top of that generic machinery; the design leaves room for other setting types to plug in their own registration step later without needing a new discovery mechanism.

It owns none of any individual app's _settings_ — those live in each app's own `app_settings.py`. It also does not own the plain swappable-FK string convention (`CRM_CUSTOMER = 'crm.Customer'`) — that now lives centrally in `config.settings.base_models`, outside both this framework and any individual app's `app_settings.py`. This is the single most important thing to understand about this app, so it gets its own section below rather than a passing mention.

## Why

Every app in this platform needs some mix of: importable defaults a project may want to swap out (choice classes, strategy classes), model references usable differently depending on _when_ they're accessed (a migration vs. a running server), and runtime toggles (some needing live admin editability, some not). Without one shared implementation, every app would reinvent this — and the one genuinely easy-to-get-wrong piece (safely resolving a model class without crashing depending on import order) would get reinvented slightly differently, and slightly wrong, per app. This app exists so that hazard gets solved exactly once.

## Python / Django Concepts

### Descriptors

**What it is:** A descriptor is any object that defines `__get__`, `__set__`, or `__set_name__`. When an instance of one is placed as a class attribute, Python routes `instance.attribute` and `instance.attribute = value` through those methods instead of doing a plain dictionary lookup from `instance.__dict__`. This is the exact mechanism Django's own model fields (e.g. `models.CharField()`) are built on.

**Why this app needs it:** We want `app_settings.PARTY_TYPE_CHOICES` to _read_ like a normal attribute — clean syntax, works with IDEs — while secretly running real logic every time it's touched (check for a project override, import a module, cache the result). A descriptor is the only Python mechanism that lets plain attribute syntax trigger arbitrary code.

**Minor example:**

```python
class Loud:
    def __get__(self, instance, owner):
        print("reading!")
        return 42

class Holder:
    x = Loud()

Holder().x  # prints "reading!", evaluates to 42
```

### `__set_name__`

**What it is:** Python automatically calls `descriptor.__set_name__(owner_class, "attribute_name")` exactly once, the moment the class body that contains it finishes executing — nobody calls this manually.

**Why this app needs it:** Every setting field needs to know its own name (`"PARTY_TYPE_CHOICES"`) to look itself up in the project's override dictionary. Without `__set_name__`, you'd have to type the name twice — once as the attribute, once as a string argument — which is exactly the kind of duplication that drifts out of sync.

**Minor example:**

```python
class Named:
    def __set_name__(self, owner, name):
        print(f"I'm called {name} on {owner.__name__}")

class Holder:
    thing = Named()   # prints "I'm called thing on Holder" immediately
```

### `instance is None` in `__get__`

**What it is:** `__get__(self, instance, owner)` is called both for instance-level access (`obj.attr`) and class-level access (`TheClass.attr`, no instance exists). Python distinguishes these by passing `instance=None` in the class-level case.

**Why this app needs it:** Most of the time, resolving a setting means doing real work (importing, hitting the DB). But the framework also needs a way to get _the descriptor object itself_ — to introspect its `.default`, `.help_text`, or to call `.get_raw_value()` without triggering full resolution. Checking `instance is None` and returning `self` in that branch is what makes class-level access (`SomeSettings.SOME_FIELD`) return the raw descriptor instead of a resolved value.

### Metaclasses

**What it is:** Normally, `class Foo: ...` is built by Python's builtin `type`. A metaclass is a class used to build _other classes_ — supplying `metaclass=SomeMetaclass` means `SomeMetaclass` controls what happens the moment `class Foo(...)` is defined, once, at class-creation time (not per-instance).

**Why this app needs it:** Every settings class needs two things done automatically, without the app author remembering boilerplate:

1. turn its inner `Meta.app_label` into a usable override-key string, and
2. walk its class body and collect every field that's a `SettingType` descriptor, so the framework can enumerate "all of this app's settings" later (for autoregistration, for validation). A metaclass is where "the moment this class is defined" hooks live — no other mechanism runs code at exactly that point.

**Anti-pattern to notice here:** reaching for a metaclass for anything _other_ than "must run at class-definition time, for every subclass, without the subclass author opting in." If a `classmethod` or a plain helper function would do the job, prefer that.

### Django app-loading lifecycle (`django.setup()`)

**What it is:** Starting any Django process (`runserver`, `migrate`, a Celery worker, pytest) runs `django.setup()`, which does three things in strict order: (1) load `settings.py`, (2) import every installed app's `models.py`, building the app registry, (3) call `AppConfig.ready()` for every app, in `INSTALLED_APPS` order, only after step 2 is fully done for _all_ apps.

**Why this app needs it:** `app_settings.py` typically gets imported as a side effect of `models.py` importing it (for `choices=...`), which happens during step 2 — while the app registry is still being built, and _before_ anyone's `ready()` has fired. Anything that needs the app registry to be fully populated (like resolving a model class by its label) is unsafe to run at that point, and must instead be deferred until step 3 or later.

**Minor example of the danger this avoids:** calling `django.apps.apps.get_model("crm", "Customer")` directly inside `app_settings.py`'s top-level code would sometimes crash with `AppRegistryNotReady` and sometimes not — depending on which app happened to get imported first that run.

**Where ordering _within_ step 3 actually matters:** `AppConfig.ready()` calls happen one at a time, in `INSTALLED_APPS` order — unlike step 2, this order is not "everyone finishes before anyone starts." `core`'s autodiscovery `ready()` doesn't strictly need to run before or after any other app's `ready()`, _provided_ no other app's `ready()` ever reads a `Constance`-backed value. If one ever did, that read would need `core`'s registration to have already happened — meaning `core` would need to run _first_ in `INSTALLED_APPS`, not last. See Gotchas.

### Lazy evaluation

**What it is:** Deferring a computation until its result is actually needed, rather than running it eagerly.

**Why this app needs it:** It's the general principle behind the specific fix above — a descriptor's `__get__` only runs when someone actually accesses the attribute. Since real code (views, signal handlers, Celery tasks) only ever touches `app_settings.SOMETHING` well after step 3 has completed, using a descriptor is a way of _guaranteeing_ laziness through the language itself, rather than a rule everyone has to remember to follow by hand.

## LLD Concepts

### Template Method pattern

**The pattern:** A base class defines the overall _shape_ of an operation, deferring one or more steps to subclasses. Here, `SettingType.__get__` always does the same three things — get a raw value, resolve it, optionally type-cast it — but `resolve()` itself is left abstract, and each concrete setting type fills in what "resolve" means for it.

**Why this app follows it:** Every setting type shares identical override-lookup logic (`project_settings.<APP>_APP_SETTINGS[name]` → `default`). Only the _last_ step — turning a raw value into something usable — genuinely differs per type. Template Method lets that shared logic live in exactly one place, written once.

**Minor example of the shape:** `DefferedImport.resolve()` imports a module and grabs an attribute; `Flag.resolve()` just returns what it was given unchanged; `Constance` is the one type that steps outside this shape entirely (see below), because its access pattern is fundamentally different, not just a different resolution step.

### Swappable references (generalizing Django's `AUTH_USER_MODEL`)

**The pattern:** Rather than one app hard-importing another app's model directly, the _target_ is a configuration value (a string, resolved at the right moment) that a project can redirect. Django itself does this for exactly one model, and puts that one string directly in `settings.py` (`AUTH_USER_MODEL`) — a single, central, project-level declaration, not one scattered per-app. This project's swappable-FK strings now follow that same shape literally: centralized in `config.settings.base_models`, rather than duplicated inside whichever app happens to consume a given target.

**Why this app follows it:** Centralizing avoids the same target string being declared — and potentially drifting — in every consuming app's own `app_settings.py`. `CRM_CUSTOMER = 'crm.Customer'` is one fact about the project's configuration; it should exist once. A consuming app's own `app_settings.py` still declares a `DefferedModel` field if it wants the _resolved class_ form for runtime use, but that field's `default` points _at_ the centrally-declared string rather than re-declaring it.

### Two distinct access modes for the same target: string vs. resolved class

**The pattern:** The exact same conceptual target (`"crm.Customer"`) needs to be consumed two structurally different ways depending on _when_ it's read: as a **plain string**, with zero app-registry dependency, when Django's migration machinery builds a dependency graph; and as a **resolved model class**, safe only after the app registry is fully ready, when application code wants to actually query it. This project keeps these as two separate declarations — the central plain string in `config.settings.base_models`, and a `DefferedModel` field in the consuming app's own `app_settings.py` — rather than one clever object trying to behave as both depending on context.

**Why this app follows it:** A single object that's "a string, but also lazily becomes a model class if you ask it the right way" makes an unsafe access pattern (triggering model resolution inside a migration file) look syntactically identical to a safe one. Two separate, narrowly-scoped declarations mean there's no ambiguous code path — reading the string form and reading the resolved form are visibly different calls, at visibly different locations, so a reviewer can tell which one a given line of code is doing just by looking at it.

### Explicit lifecycle hooks over implicit side effects

**The pattern:** Anything that must happen at a specific, guaranteed point in the Django startup lifecycle (like Constance field registration) is triggered from an explicit, single, well-documented hook — `core`'s own `AppConfig.ready()` — rather than as an incidental side effect of some unrelated import happening to occur.

**Why this app follows it:** An operation that "happens to work" because of _today's_ import order is not the same as an operation that's _guaranteed_ to work. Autodiscovery (a single `ready()`, on `core` itself, that scans every installed app for an `app_settings` module) removes the need for each app to remember to call a registration hook individually — `core` finds every app's settings on its own.

## Anti-patterns

**Merging the swappable-FK string and `DefferedModel` into one object.**
_What it looks like:_ A `str` subclass with an added `.model` property that lazily resolves via `apps.get_model()`, so the same attribute works as a string in `swappable_dependency()` _and_ as a model class elsewhere.
_Why it's wrong:_ It makes an unsafe call (`apps.get_model()` at migration-import time) _look_ identical, at the call site, to a safe one. It also violates interface segregation for no real gain — migration graph-building and application code want fundamentally different things from this value.
_Do instead:_ Keep the central plain string (in `config.settings.base_models`) and each consuming app's `DefferedModel` (in its own `app_settings.py`) as two separate, narrowly-named declarations, per "Two distinct access modes" above.

**Redeclaring the same swappable-FK string inside a consuming app's `app_settings.py`, instead of pointing at `config.settings.base_models`.**
_What it looks like:_ `CRM_CUSTOMER = "crm.Customer"` written directly inside `donation_management/app_settings.py`, `ledger/app_settings.py`, and so on — each app carrying its own copy of the same string.
_Why it's wrong:_ Now the same fact about the project's configuration exists in N places. Redirecting the target for the whole project means editing N files instead of one, and it's easy for one of them to be missed or to drift.
_Do instead:_ Declare it once, centrally, in `config.settings.base_models`; each consuming app's `DefferedModel` field points at that single source.

**Registering `Constance` fields as a side effect of `BaseSettings.__init__`.**
_What it looks like:_ `CRMSettings()`'s constructor directly calling registration logic, so simply instantiating the settings object performs registration.
_Why it's wrong:_ Instantiation happens whenever _something_ first imports `app_settings.py` — which could be early (via `models.py`) or arbitrarily late (via a view or task module not touched until the first matching request). There's no guarantee registration completes before something else needs the fully-assembled config.
_Do instead:_ Trigger registration from `core`'s own `AppConfig.ready()`, the one point in the lifecycle guaranteed to run after all `models.py` imports are done, before the app starts serving anything.

**A `Flag` type that caches its resolved value.**
_What it looks like:_ Adding an internal cache to `Flag.resolve()` "for performance," the same way `DefferedImport` caches its import.
_Why it's wrong:_ `django.test.override_settings` works by temporarily mutating `settings.<APP>_APP_SETTINGS` and restoring it afterward. If `Flag` cached its result, a test using `override_settings` would silently keep seeing the _pre-override_ value, because the cached copy would never get invalidated.
_Do instead:_ Leave `Flag` uncached — correctness under `override_settings` matters more than avoiding a dictionary lookup.

**A `.raw()`-equivalent that maintains its own name→descriptor dictionary.**
_What it looks like:_ A metaclass-built `_declared_settings` dict, consulted purely so a `.raw("FIELD_NAME")` helper has something to look a string up in.
_Why it's wrong:_ Python's own attribute lookup (`getattr(SomeSettingsClass, "FIELD_NAME")`) already does exactly this job, for free, using the class-level `__get__` branch (`instance is None`) that every `SettingType` already supports.
_Do instead:_ Implement any "look up a field by name string" helper using `getattr` on the class itself, falling back to Python's own `AttributeError` for unknown names.

## How

- **Models:** none — this app is pure Python infrastructure, no Django models of its own.
- **Swappable settings:** `core.app_settings` declares none of its own. The plain swappable-FK strings every consuming app targets now live centrally in `config.settings.base_models`, not inside this app and not inside any individual consumer's `app_settings.py`. A consuming app's own `app_settings.py` may still declare a `DefferedModel` field for runtime use, whose `default` points at the corresponding central string.
- **Contracts / checks:** an optional validation helper is meant to be wired into each _consuming_ app's own `checks.py` (following that app's existing `missing_attrs`-based convention), confirming every declared `DefferedImport`/`DefferedModel` field actually resolves — via Django's real checks framework (`@register()`), not a custom error-reporting path.
- **Migrations:** none in this app. It dictates how _other_ apps write migrations: any `swappable_dependency()` call reads the plain string directly from `config.settings.base_models` (or via a `.raw()`-style convenience, if the consuming app's `DefferedModel` wraps it), never touching a `DefferedModel` field at instance level from within a migration file.
- **Signals / side effects:** the one deliberate, contained side effect in this whole app is Constance registration, triggered from `core`'s own `AppConfig.ready()` (`backend/apps/core/apps.py`), which autodiscovers every installed app's `app_settings` module.
- **API surface:** none — not DRF-facing.
- **Gotchas:**
  - `DefferedImport`'s cache is process-global, keyed by the exact dotted-path string. Don't `importlib.reload()` a module whose target is cached — patch the target object directly in tests instead.
  - `Constance` field access bypasses the normal override-lookup path entirely once registered — `project_settings` only ever affects the _seed default_, never a value with an existing DB row.
  - `django.test.override_settings` affects `Flag` and `DefferedImport`/`DefferedModel` overrides, but has no effect on `Constance` — use `constance`'s own test utilities for that type instead.
  - **`core` is currently placed last in `INSTALLED_APPS`.** This is safe only as long as no other app's `AppConfig.ready()` reads a `Constance`-backed value — such a read would execute before `core`'s registration has run, and would fail. If that ever becomes necessary, `core` needs to move to _first_, not stay last — don't assume "last" is a permanent, self-justifying convention.

## Directory Structure

```
core/utils
├── app_settings/
│   ├── base.py             # SettingType, BaseSettingsMeta, BaseSettings
│   ├── types.py             # DefferedImport, DefferedModel, Flag, Constance
│   ├── registry.py           # register_constance_fields() — pure registration logic, called from apps.py
│   ├── validation.py          # optional helper for consuming apps' own checks.py
│   └── README.md              # this file                   # core's AppConfig.ready() — all core-related autodiscovery logic;
                                 core is intended to stay last in INSTALLED_APPS (see Gotchas)
```

## Miscellaneous

- **Testing notes:** `Flag` and `DefferedImport`/`DefferedModel` overrides are testable via standard `override_settings`; `Constance` requires its own DB-aware test setup instead.
