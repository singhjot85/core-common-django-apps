---
name: backend-feature-lifecycle
description: Use for any new feature, new or changed model/task/cron/setting, behavior change, or refactor in this repo. Runs analysis, implementation, refactor and testing with an approval gate and a DB backup before execution, and routes to the other skills at the step that needs them.
---

# Backend feature lifecycle

Do not start a phase before the previous one is done. Never write implementation code in Phase 1.

Already loaded at session start: `vcs-workflow`, `graphify`. Load `ponytail` with this skill. Load the others below only at the step that names them. Precedence: AGENTS.md rules > this skill > `ponytail`. Ponytail decides how little code to write; it never skips a gate, the backup, tests, or docs.

## Skill routing (load at that step, not before)

| Step | Skill |
| --- | --- |
| Phase 1: choosing what to document or log | `backend-docs` |
| Phase 2: new app | `create-django-app` |
| Phase 2: fixtures or dev seed data | `add-seeder` |
| Phase 2/3: adding or changing docstrings | `backend-doc-string` |
| Phase 4: writing or running tests | `backend-pytest` |
| Phase 4: Readme / `docs/` updates | `backend-docs` |
| Branch, commit, PR | `vcs-workflow` |

## Phase 0: Orient
- Use `graphify` (`query`, `explain`, `path`) to find existing models, tasks, crons and patterns. Do not decide "existing vs new" from memory.
- Read the `Readme.md` of every app you will touch.
- Check `vcs-workflow` for the branch you should be on before changing anything.

## Phase 1: Analysis (the "what")
1. Create `docs/<feature-slug>/analysis.md` (agent-only; shape per `backend-docs`). Edit in place and compact each iteration; do not append.
2. Answer each item, or mark it N/A with a reason:
   - **Input and output:** input source and structure; output contract (DB, API response).
   - **Reuse vs new:** existing models, tasks, crons, patterns. Justify anything new.
   - **Database:** schema changes, expected queries, data volume per table.
   - **Caching, async, cron:** which are needed and why.
   - **Failure policy per case:** raise, roll back, or log only. Reuse exceptions from `core/utils/error_handling/exceptions.py`, then Django/DRF built-ins.
   - **Retries:** mechanism, max attempts, backoff, behavior on exhaustion.
   - **Logging:** level and context (IDs, schema name; never PII or secrets).
   - **Tenancy:** public or tenant schema; schema name passed explicitly to tasks; `transaction.atomic()` boundaries.
   - **Data:** what ships as production fixture vs dev seed JSON.
   - **Settings:** which go in the app's `app_settings.py`.
   - **Libraries vs utils:** if it is a reusable building block, it belongs in `core/libraries/`.
   - **Backup need:** does execution migrate schemas or mutate existing data?
   - **Docs impact:** which Readmes change.
3. Present a short summary plus the open points, each with your recommendation. **Stop and wait for approval.**

## Phase 2: Implementation (the "how")
Only after approval. If something is unclear, go back to Phase 1.

1. **Backup:** if the plan migrates or mutates data, run `make db-dump` first and note the filename.
2. New app: load `create-django-app`. Do not scaffold by hand.
3. Fail fast: validate at the top of functions and raise early. Cheap paths first. No N+1 (`select_related`/`prefetch_related`, `bulk_create`/`bulk_update`).
4. No unnecessary fallbacks (AGENTS.md rule 7): one definitive key, no silent defaults, no swallowing `try/except`.
5. Side effects only through `queue_task()` (AGENTS.md rule 2).
6. Data: fixtures vs seed JSON per the plan; load `add-seeder`.
7. Migrations: `make mm APP_LABEL=<app>`, then `make m` and `make ms`. If anything is stale, stop and report (AGENTS.md rule 10).
8. Docstrings: follow `backend-doc-string`.

## Phase 3: Refactor
Behavior must not change. Run tests before and after (add tests first if there are none).
- Find every caller of shared code (`graphify path`/`explain`, then grep). Fix root causes once.
- Single-responsibility functions. Extract a helper on the third real duplicate, not earlier.
- Keep public interfaces stable unless the plan says otherwise.

## Phase 4: Testing, docs, close-out
- **How** to write and run tests: `backend-pytest`. **What** to cover comes from the Phase 1 plan:
  - happy path;
  - each invalid-data case, asserting the exact exception;
  - retries and exhaustion;
  - post-commit side effects (fire on commit, never on rollback);
  - tenant isolation (data in tenant A is invisible from tenant B).
- Run the narrow `make` target while iterating, then `make t` before finishing.
- Docs: update module `Readme.md` files and the `docs/<slug>/analysis.md` log per `backend-docs`.
- `poetry run pre-commit run --all-files` until clean.
- `graphify update .`
- Commit and PR per `vcs-workflow`.
- Offer `ponytail-review` to the user. Do not run it unasked.

## Final report
What was built; tests added and what they cover; backup file taken; what was **not** checked; stale migration/DB issues waiting on the user; adjacent problems noticed but left alone.