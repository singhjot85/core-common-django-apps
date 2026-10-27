# Feature Apps (nested apps)

A feature-app lives under a parent domain (`<apps_root>/users/features/onboarding`) or at a custom path.
Use it for vendor-specific or optional functionality that host projects may include or exclude independently.

## Derivation (the scaffold does this; verify it)
Given `--path <apps_root>/users/features/onboarding`:
- Module path: dotted path from repo root: `core.apps.users.features.onboarding`
- **Label**: path parts below `apps_root`, minus `nested_container_dirs` (`features`, `providers`), joined by `_`
  -> `users_onboarding`. Override with `--label`.
- Settings key: `<PREFIX>_USERS_ONBOARDING_SETTINGS`
- Swappable keys: `USERS_ONBOARDING_<MODEL>_MODEL`
- Migrations: `<migrations.root>/users_onboarding/` (external mode)

## Rules
1. `label` must be unique across all installed apps; always parent-prefix nested apps.
2. `name` in `AppConfig` is the full dotted path; `label` is the short unique key.
3. Register the dotted path in the registry list; feature-apps are optional by design, so do not make the
   parent app import them.
4. The parent must not depend on the feature; the feature may depend on the parent's getters.
5. Same migration handling as top-level apps (see profile `migrations.mode`).

## Check after scaffolding
```bash
python manage.py check          # label collisions surface here
python <skill_dir>/scripts/check_app.py <app_dir> --profile <profile>
```
