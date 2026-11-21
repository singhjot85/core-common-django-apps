# Core Django Apps Agent Context & Knowledge Base (`docs/`)

> [!IMPORTANT]
> **Agent Context Only**: The files in `docs/` are structured specifically for **AI agent context**, historical memory, feature design decisions, and technical specifications.
>
> **Human & Developer Documentation**: Architecture guides, setup guides, and human-readable operational documentation stay directly alongside the code as `Readme.md` files (e.g., root [`Readme.md`](../Readme.md) and app-level `Readme.md` files inside [`core/apps/`](../core/apps/)).

---

## 1. Directory Structure Standards

Every feature, subsystem, or architectural initiative has its own dedicated directory under `docs/`. When future agents work on a task, they must consult and update the corresponding feature directory:

```text
docs/
├── Readme.md                          # Root index & agent operating guidelines (this file)
├── <feature_slug>/                    # Dedicated per-feature directory
│   ├── analysis.md                    # Phase 1 analysis, scope, tradeoffs, queries, and decisions
│   └── <topic_or_roadmap>.md          # Technical specifications, state machines, and migration plans
```

### File Conventions for Agents

1. **`analysis.md`**:
   - Created during **Phase 1 (Analysis)** of any multi-file feature or refactor.
   - Answers: input source, output contract, caching needs, async/Celery requirements, database queries, and failure handling.
   - Edited in place — never appended with redundant conversational logs.
2. **Per-feature Specialized Specs**:
   - Deep architectural roadmaps, regex dictionaries, or migration playbooks belong in named markdown files within the feature folder.

---

## 2. Feature Directory Index

| Directory | Feature Domain | Key Documents & Agent Context |
|---|---|---|
| [`users_and_auth/`](./users_and_auth/) | Authentication & User Management | [API URLs & Template Views](./users_and_auth/api-urls-and-template-views.md), [Authenticated Shell & Modular Login](./users_and_auth/authenticated-view-and-modular-login.md), [OTP Signup Flow](./users_and_auth/otp-signup-flow-corrections.md), [Post-Login Forwarding](./users_and_auth/landing-page-routing-post-login.md) |
| [`integrations/`](./integrations/) | Third-Party Integrations Engine | [Integrations Architecture](./integrations/analysis.md) (multi-tenant provider adapters, email, SMS, and credentials manager) |
| [`configurations/`](./configurations/) | Dynamic Configuration & Labels | [Template Labels & Seeders](./configurations/database-label-configuration-and-seeder.md) (database configuration records, multi-language fixtures) |
| [`templates/`](./templates/) | Core Jinja2 Template System | [Login Page & Dynamic Forms](./templates/login-page-and-form-templates.md), [Template Accessibility & Escaping Fixes](./templates/template-fixes.md) |

---

## 3. Rules for AI Agents

1. **Check Existing Context**: Before authoring new endpoints or services, search `docs/<feature>/` and existing app models/services to prevent duplicate implementations.
2. **Keep Docs Clean**: Do not pollute `docs/` with root-level scratch files. Every new document must be placed into a feature-specific directory.
3. **Synchronize Human Docs**: When modifying functionality, update the relevant `Readme.md` in the feature codebase alongside updating the agent context in `docs/`.
