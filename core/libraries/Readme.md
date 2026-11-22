# Core Libraries (`core.libraries`)

This directory contains standalone, reusable libraries that provide foundational capabilities across the framework and consuming host projects.

> [!NOTE]
> **Living Document:** This document is intentionally incomplete. It serves as our baseline architectural standard and will grow over time as we learn from design refinements and real-world edge cases.

---

## Core Library Principles

### 1. Zero App Coupling
- **Hard Rule:** Libraries must be completely decoupled from domain business apps.
- Never import from `core.apps.*` inside any library module.
- Domain models and configurations must be passed into library strategies dynamically (via getters, injected arguments, or dependency inversion).

### 2. No Unnecessary Fallback Ladders
- **Anti-pattern:** Avoid defensive fallback chains like `.get(a, .get(b, .get(c)))` or nested `getattr()` ladders.
- Every fallback or branching condition must be backed by a clear domain reason and rigorous analysis, not speculative assumptions or defensive guesswork.
- If a value or configuration is required, fail fast with a descriptive domain exception.

### 3. Isolated Library Tests
- Keep all library-level test suites within the library itself: `core/libraries/<library_name>/tests/`.
- App-level test suites (`core/tests/<app>/`) should test business domain behavior, not library internals.
- Library tests must emphasize high-value contract verification (DAG resolution, graph linking, idempotence, isolation) rather than trivial mock coverage.

### 4. Explicit Composition Over Inherited Metaclasses
- Favor explicit class attributes, strategy injection, and dependency inversion over complex metaclass inheritance (e.g., `method = GetorCreateObject(...)` instead of inner `Meta` classes).

---

## Active Libraries

| Library | Path | Role | Status |
| :--- | :--- | :--- | :--- |
| **Seeder** | [`core/libraries/seeder/`](./seeder/) | Declarative, dependency-driven database seeding and fixture engine with multi-tenant schema isolation. | Active / Migrated |
