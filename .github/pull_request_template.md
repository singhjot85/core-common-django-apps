## What and why
<!-- One paragraph: the behavior change and the reason. Link the issue or docs/<slug>/analysis.md. -->

## Type
- [ ] Bug fix
- [ ] Feature
- [ ] Refactor (no behavior change)

## Impact on host projects
- [ ] No public interface change
- [ ] Changes models, settings keys, API contract, or task signatures (describe below, host projects must adapt)
- [ ] Needs host migrations (`make mm` output reviewed)
    - Host migration commands(if needed):
    <!-- Example: `make mm APP_LABEL=users`, `make mm APP_LABEL=crm`, ... -->

## Data and safety
- [ ] DB backup taken before running migrations or seeders (`make db-dump`)
- [ ] Production data ships as fixtures; dev-only data as seed JSON
- [ ] No secrets or PII logged

## Quality gates
- [ ] Tests added or updated, run via `make t`
- [ ] Tenant isolation covered where tenant data is touched
- [ ] `poetry run pre-commit run --all-files` is clean
- [ ] App `Readme.md` updated if documented behavior changed
- [ ] `graphify update .` run

## Not checked / risks
<!-- What this PR does not cover. -->