# Phase 8: CLI Scaffolder - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI tool that generates new projects from this template. Developer runs one interactive command, provides project name and feature selections, and gets a fully configured monorepo that passes all quality checks (lint, type-check, tests) out of the box.

Scope includes: project name transformation, feature toggles (platforms + AI module), file operations (copy/rename/replace), secret generation, and validation. Does NOT include: hosting the template in a registry, version management of the template itself, or post-generation project updates.

</domain>

<decisions>
## Implementation Decisions

### Prompting Flow

- **Locked:** Hybrid approach — Ask project name first, then show multi-select feature menu
- **Locked:** Require explicit project name (no default)
- **Locked:** Features default to "all included" — user unchecks what they don't want
- **Locked:** Re-prompt with clear error message on invalid input (don't exit CLI)
- **Claude's Discretion:** Validation rules for project names (what characters allowed, length limits)

### Project Naming and Transformation

- **Locked:** Prompt for output directory path during flow (don't assume current dir or auto-create)
- **Claude's Discretion:** Case transformation strategy (auto-detect and transform vs single canonical form)
- **Claude's Discretion:** Template replacement mechanism (placeholder markers vs hardcoded string search)
- **Claude's Discretion:** What gets renamed vs what keeps template references (foundation specs, app names, package names)

### Feature Selection Granularity

- **Locked:** Platform-level toggles — user can include/exclude: web app, mobile app, landing page, AI module
- **Locked:** All features included by default (web ✓, mobile ✓, landing ✓, AI ✓) — user unchecks to exclude
- **Locked:** Complete removal when platform excluded — delete directories, remove from workspaces, strip dependencies (no empty scaffolds)
- **Claude's Discretion:** Feature dependency handling (auto-enable dependencies vs block incompatible selections)

### Generation Validation and Rollback

- **Locked:** Run full quality gates on generated project — lint (ruff, eslint, prettier) + type-check (mypy, tsc) + tests (pytest, vitest)
- **Claude's Discretion:** When to run validation (after generation completes vs incremental during generation)
- **Claude's Discretion:** Validation failure handling (leave project with errors vs rollback vs ask user)
- **Claude's Discretion:** Partial generation failure handling (automatic rollback vs leave for debugging)

</decisions>

<specifics>
## Specific Ideas

**Quality guarantee:**

- User expectation: "Generated project should work immediately — no manual fixes needed"
- Running lint/type-check/tests ensures this guarantee

**Feature exclusion:**

- When mobile excluded: apps/mobile/ deleted, metro config removed, Expo deps stripped from root package.json
- When AI excluded: apps/api/apps/ai/ deleted, AI deps removed, celery config simplified (reference Phase 6 removal script)
- When landing excluded: apps/landing/ deleted, landing workspace removed

**Secret generation:**

- Django SECRET_KEY must be unique per generated project (not template default)
- Generate new secrets for any sensitive values in .env files

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 08-cli-scaffolder_
_Context gathered: 2026-02-17_
