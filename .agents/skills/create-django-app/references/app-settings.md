# Per-App Settings (profile: `app_settings` not null)

Applies only when the project has a descriptor-based settings engine. The names below
(`Settings`, `Constance`, `Configuration`) come from the profile's `app_settings.tiers`; use only the tiers
the project actually provides, and confirm exact constructor arguments by reading the engine's source
or an existing `app_settings.py` before authoring non-trivial settings.

## Tiers (choose by how fast the value must change)

| Tier | Storage / lifecycle | Use for |
| :-- | :-- | :-- |
| `Settings` | Code or host settings; change = deploy | Import paths, classes, page sizes, timeouts |
| `Constance` | DB-backed, admin-editable, instant | Feature flags, thresholds, rate limits |
| `Configuration` | Versioned JSON in DB, cached per tenant | Business rules, fee tables, workflows |

Decision rule: if an operator should change it without a deploy, not `Settings`. If it is structured/versioned
data, `Configuration`. Otherwise `Settings`.

## Rules
1. `app_settings.py` defines the class only. **Never instantiate it there.** The singleton
   (`app_settings = XSettings()`) is created in the app's `__init__.py`. Reason: avoids import cycles and
   keeps descriptors from resolving before apps are ready.
2. `SETTINGS_KEY` is the first class attribute. Feature-apps prefix it with the parent domain
   (`<PREFIX>_USERS_ONBOARDING_SETTINGS`) to avoid collisions.
3. Descriptors get `__set_name__` after the class body; in validation/errors use
   `getattr(self, "app_settings_key", None)`.
4. No defensive `getattr` chains across settings; access descriptors directly.
5. Host overrides go in the host's settings under the `SETTINGS_KEY` dict.
6. Constance key convention (if applicable): `SETTINGS_KEY` minus `_SETTINGS`, plus `_<NAME>`, upper-case.

## Scaffold defaults
The scaffold emits one example per available tier plus a swappable-model import setting when
`import_data_type` is configured. Delete examples you do not need; keep real ones documented via `help_text`.
