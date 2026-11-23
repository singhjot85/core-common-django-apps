---
name: backend-docs
description: Use when a change alters documented behavior, when creating a new app or module, or when writing or editing any Readme.md or docs/ file. Defines what documentation exists, where it lives, and how short it must be. Docstrings are handled by backend-doc-string.
---

# Backend documentation

Goal: an agent or developer who reads one Readme understands the module's role and public surface in under two minutes. Short and accurate beats long and complete.

## Where things live
| What | Where | Audience |
| --- | --- | --- |
| Module/app overview | `Readme.md` next to the code | humans and agents |
| Function/class contracts | docstrings (use `backend-doc-string`) | developers |
| Feature analysis and decisions | `docs/<feature-slug>/analysis.md` | agents only (working memory) |

Never put human-facing docs in `docs/`. Never put analysis logs in a Readme.

## When to update
- New app, model, setting, manager helper, endpoint, task, or cron: update that module's `Readme.md` in the same change.
- Behavior change or fix that makes the Readme wrong: fix the Readme in the same change.
- Nothing documented changed: do not touch the docs.
- A Readme with only `TODO` is worse than none. Fill it or delete it.

## Readme shape (target 40-100 lines)
1. **Purpose:** 2-3 sentences, the module's architectural role and what it does not do.
2. **Models:** one line each, with relationships and swappable key.
3. **Settings:** keys, type, default, where they come from (`Settings`/`Constance`/`Configuration`).
4. **Public API:** endpoints (prefix and verbs), getters, manager helpers, tasks/crons.
5. **Gotchas:** non-obvious behavior only (schema placement, ordering constraints, async behavior).

## Style
- No code dumps: never paste whole classes or boilerplate. A snippet only for a non-obvious integration pattern, max ~10 lines.
- Describe behavior, not implementation. If the Readme restates the code line by line, delete the repetition.
- Tables for lists of models, settings or endpoints. Prose for the why.
- Link to other Readmes instead of repeating them.
- Remove superseded statements; do not append "update:" notes. History belongs in git.

## `docs/<feature-slug>/analysis.md`
Edit in place and compact each iteration (see `backend-feature-lifecycle`). It is the agent's memory of decisions and open points, not a changelog.

## Check before finishing
- Every statement in the Readme is still true (names, endpoints, settings keys exist).
- No `TODO` stubs left behind.
- No duplicated content between Readme and docstrings.