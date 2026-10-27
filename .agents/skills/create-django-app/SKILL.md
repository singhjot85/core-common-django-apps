---
name: create-django-app
description: Scaffold, author, and wire a new modular Django app (or nested feature-app) following the host project's own conventions. Use when asked to create a new app, add a feature-app, scaffold models/admin/settings/apps.py, set up swappable models, per-app settings, or migration routing. Reads a per-project profile so it works in any Django repo.
---

# Create Django App

Generates a new Django app that follows **this repository's** conventions, not generic `startapp` defaults.
All project-specific values (paths, base classes, commands, migration routing) live in a **project profile**,
never in this file. Same skill, any repo.

## Workflow

### Phase 0 - Load or build the project profile (never skip)

1. Look for `project.profile.json` next to this SKILL.md (or pass `--profile <path>` to scripts).
2. If it exists, read it and go to Phase 1.
3. If it does not, **discover** the conventions before writing any code. See
   `references/project-profile.md` for the checklist (Makefile targets, an existing app to copy, settings
   registry file, migration routing, base model, admin site). Draft the profile, show it to the user,
   and save it only after they confirm. Do not guess silently.

### Phase 1 - Gather inputs (ask only what is missing)

| Input | Default |
| :-- | :-- |
| `app_label` (snake_case) | required |
| models (names only) | one model named after the app |
| location | `<apps_root>/<app_label>`; nested path => feature-app |
| tenancy scope (only if profile `tenancy` is set) | tenant/private |
| optional status field | off |

### Phase 2 - Preview, then scaffold

```bash
S=<skill_dir>/scripts
python $S/scaffold_app.py billing --models Plan Subscription --dry-run   # preview, writes nothing
python $S/scaffold_app.py billing --models Plan Subscription             # write
python $S/scaffold_app.py onboarding --path <apps_root>/users/features/onboarding   # feature-app
```

Rules the script enforces:
- Never overwrites an existing file (use `--force` only with explicit user consent).
- Only removes a generated `migrations/` dir if it contains nothing but `__init__.py`.
- Everything is derived from the profile; nothing is hard-coded.

### Phase 3 - Wire into the project (the script prints exact lines; apply them)

Add the app to the registry file named in the profile (`settings_registry_file`): app constant,
swappable model strings, installed-apps list, tenant/public list if applicable. Edit these by hand with the
Edit tool; do not regenerate the file.

### Phase 4 - Customize (the scaffold is a skeleton, not the product)

Replace placeholder fields in the abstract models, add real admin config, constants, API layer. Follow the
rules in `references/`:
- `references/swappable-models.md` - abstract/concrete split, getters, FK strings
- `references/app-settings.md` - per-app settings tiers (only if profile enables `app_settings`)
- `references/feature-apps.md` - nested apps: label uniqueness, settings key prefixing, migrations

### Phase 5 - Migrate, verify, test

1. Run the profile's `commands.makemigrations` (check the migration lands where routing expects it).
2. Run `python $S/check_app.py <app_dir> --profile <profile>`; fix every violation.
3. Run the profile's `commands.test`, then `commands.lint` if defined.
4. Report to the user: files created, lines added to the registry, migration path, test result.

## Quality checklist

- [ ] Profile was confirmed by the user (or already existed)
- [ ] `check_app.py` exits 0
- [ ] Migration file exists in the routed location (external mode) or in-app `migrations/` (in_app mode)
- [ ] App registered in the registry file, correct tenant/public list
- [ ] Label is unique across installed apps (feature-apps: prefixed with parent)
- [ ] No concrete-model imports outside `models.py` / migrations / tests (swappable mode)
- [ ] Tests created and passing

## Failure modes to avoid

- Copying conventions from memory of another repo. Always read the profile or discover.
- Running `startapp` and the scaffold script both; the script replaces `startapp`.
- Scaffolding placeholder fields and shipping them. Placeholders must be replaced in Phase 4.
- Deleting directories without checking contents.
