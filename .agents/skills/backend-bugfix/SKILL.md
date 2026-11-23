---
name: backend-bugfix
description: Use when existing behavior is wrong and the fix stays inside current models, tasks and interfaces (includes typos and small config fixes). Escalates to feature-lifecycle when the fix is bigger.
---

# Bug-fix flow

## Escalate to `backend-feature-lifecycle` (stop, say why, wait) if any is true
- Needs a new or changed model, migration, task, cron, or setting.
- Changes a public interface (signature, API contract, serializer fields).
- Root cause is a design flaw, or several fixes with real trade-offs exist.
- Touches more than one app or more than ~3 files.

Examples that stay here: wrong filter in a queryset, missing `select_related`, typo in a serializer field name, off-by-one in a retry counter, wrong default in `app_settings.py`.
Examples that escalate: adding a column to fix a report, changing an endpoint's response shape, rewriting how `queue_task` handles schemas.

If you cannot reproduce the bug or find the root cause after a reasonable attempt, stop and report what you found. Do not guess-fix.

## Steps
1. **Reproduce:** write a failing regression test first (real instances via factories; mock only external I/O). It must fail for the stated reason.
2. **Locate:** `graphify query`/`explain` (fallback: module `Readme.md`), then read only the lines it points to. Grep every caller of the function you will touch.
3. **Backup:** if verifying the fix requires running migrations or data commands on a DB you care about, `make db-dump` first.
4. **Fix the root cause once**, in shared code. No drive-by refactors, no scope beyond the bug. Fail fast, query discipline and `queue_task` rules still apply.
5. **Verify:** the new test passes; run `make t TEST_DIR=<touched app tests>`.
6. **Close out:** `poetry run pre-commit run --all-files`, then `graphify update .`. Update the app `Readme.md` only if documented behavior changed.

Stale migration or test DB at any point: stop and report (AGENTS.md rule 10). Never fix or recreate it.

## Final report
Root cause; the fix; the test added; what you did not check; adjacent issues noticed but deliberately left alone.