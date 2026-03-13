## Context

GSD milestone v1.3 shipped 5 new capabilities across phases 19–25. The codebase has been fully implemented and verified (19/19 requirements satisfied, 25/25 phases complete). This change creates the OpenSpec specs that document those capabilities for future products scaffolded from the template.

No new code is written in this change — it is purely a documentation sync. The implementation already exists; the specs are the artifact.

Current spec coverage: `openspec/specs/` has specs for auth, billing, backend, frontend, observability, security, AI module, and infra. It has no specs for email, social auth, GDPR, RBAC, or entitlements.

## Goals / Non-Goals

**Goals:**

- Create 5 new capability spec files in `openspec/specs/`
- Document known tech debt inline in the relevant specs (not a separate file)
- Update `openspec/specs/auth/` to reflect social auth additions
- Ensure every spec is self-contained (rationale inline, no references to `.planning/`)

**Non-Goals:**

- Fixing tech debt (tracked in specs, not resolved here)
- Implementing the missing "Download my data" UI button
- Nyquist validation for phases 19–25 (separate concern: `/gsd:validate-phase`)
- Creating specs for capabilities already covered in v1.0–v1.2 baseline

## Decisions

**1. One spec directory per capability, not one monolithic spec**

Each capability gets `openspec/specs/<name>/spec.md`. This matches the existing spec layout (e.g., `openspec/specs/auth/`, `openspec/specs/billing/`) and allows capabilities to be independently read, modified, or omitted when a product doesn't need them.

Alternatives considered: single `v1.3-capabilities.md` file — rejected because it would be unnavigable and would mix unrelated concerns.

**2. Tech debt documented inline, not in a separate debt registry**

Each spec includes a `## Known Issues / Tech Debt` section listing gaps identified in the milestone audit. This makes the spec self-contained: a developer reading the RBAC spec sees the AdminController `auth=` gap right there, without consulting an external file.

Alternative: `openspec/specs/tech-debt.md` registry — rejected because it decouples the debt from the context where it's actionable.

**3. Auth spec receives a delta, not a full rewrite**

Social auth extends `openspec/specs/auth/` by adding a `social-auth` section. The existing session/JWT auth content is unchanged. This avoids false-positive "what changed?" confusion for downstream products.

**4. GDPR data export UI gap documented as known gap, not closed**

The milestone audit identified no "Download my data" button in `/settings`. This is non-critical (the API endpoint works). The spec documents it as a known gap with a recommended fix rather than blocking the sync.

**5. Spec structure: decisions first, patterns second, tech debt last**

Each spec follows: Overview → Architecture / Patterns → Configuration → Integration Points → Known Issues. This gives readers what they need to use the capability before surfacing caveats.

## Risks / Trade-offs

- **Specs may drift from code** → Mitigated by including specific file paths and class names in each spec so drift is detectable
- **Tech debt items may never get addressed** → Mitigated by including "Recommendation:" for each item so the fix is actionable when prioritized
- **Auth spec delta may conflict with future auth changes** → Low risk; the social auth section is additive only

## Migration Plan

1. Create `openspec/specs/transactional-email/spec.md`
2. Create `openspec/specs/social-auth/spec.md`
3. Create `openspec/specs/gdpr-compliance/spec.md`
4. Create `openspec/specs/rbac/spec.md`
5. Create `openspec/specs/feature-entitlements/spec.md`
6. Add social auth section to `openspec/specs/auth/spec.md` (or equivalent auth spec file)
7. Archive this change → specs merge into main `openspec/specs/` tree

No rollback needed — spec files are additive and not referenced by running code.

## Open Questions

- None. All capabilities are fully implemented and audited.
