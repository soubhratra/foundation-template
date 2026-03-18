## Context

Five new capabilities were shipped in milestone v1.4 (phases 26–31) and one existing spec (`cli-scaffolder`) needs a new requirement. None of the five new capabilities have any OpenSpec spec yet — this sync creates them from scratch. The GSD phase CONTEXT.md files contain detailed implementation decisions that need to be captured in specs so scaffolded product repos inherit accurate, self-contained documentation.

This is a documentation-only sync (no code changes). The design covers how the six spec files will be structured and what decisions each must capture.

## Goals / Non-Goals

**Goals:**

- Create 5 new specs with requirements and implementation decisions (organization-model, outbound-webhooks, api-key-authentication, audit-logging, admin-backoffice)
- Add one ADDED requirement to the existing `cli-scaffolder` spec for the `--with b2b` flag
- Ensure every spec is self-contained: a developer reading only the spec understands both WHAT and WHY

**Non-Goals:**

- No code changes — documentation sync only
- Not specifying every implementation detail — only decisions with meaningful rationale for future product developers
- Not re-specifying capabilities already in other specs (billing, RBAC, email) even though B2B touches them

## Decisions

### Decision 1: Five new specs, one modified

All 5 B2B capabilities are genuinely new — no existing spec covers org models, webhooks, API keys, audit logging, or admin. Create from scratch with full requirements + implementation decisions sections.

`cli-scaffolder` already exists. Only SCAFF-01 (the `--with b2b` flag) is new. Use ADDED Requirements delta for that spec alone.

**Alternative rejected:** Putting all B2B in a single monolithic `b2b-module` spec. Individual specs allow product developers to reason about each capability independently, and mirror the per-domain structure already established for billing, rbac, email, etc.

### Decision 2: Each new spec gets both requirements AND implementation decisions inline

Unlike the milestone 1.3 sync (which added Implementation Decisions to specs that already had requirements), these specs are being created from scratch. Both sections are written together in the same file under `## ADDED Requirements` and `## Implementation Decisions`.

### Decision 3: Settings-dict pattern is a cross-cutting theme to document once per spec

Three B2B capabilities use the same settings-dict pattern (`BILLING_PLANS`-style): `WEBHOOK_EVENTS`, `API_KEY_SCOPES`, and the org entitlement cache. Each spec documents the rationale for this pattern in its own context rather than cross-referencing. The specs must be self-contained.

### Decision 4: "Shown once" security decisions documented prominently

Both webhook secret (Phase 27) and API key raw value (Phase 28) follow the "shown once at creation, never retrievable" pattern. Each respective spec documents this as a first-class security decision with rationale, since it affects product UI requirements (copy-to-clipboard affordance, warning banners).

### Decision 5: Org permission 404-vs-403 distinction is critical to document

`IsOrgMember` returns 404 (not 403) when the user is not a member of the org — this prevents org existence leakage. This is a non-obvious security decision that product developers will encounter when writing tests. It must be captured in the spec with rationale.

### Decision 6: B2B scaffolder flag is opt-in (not opt-out)

`--with b2b` is an additive flag (default excluded), unlike `--without email` which is a subtractive flag (default included). The cli-scaffolder ADDED requirement must reflect this distinction clearly, since it reverses the pattern used for all other optional modules.

## Risks / Trade-offs

**Risk: org-model spec is large** → The org model covers 7 requirements (ORG-01 through ORG-05, BILL-01, BILL-02). Mitigation: group into logical sections (Organization lifecycle, Membership & Roles, Invitation Flow, Per-Org Billing) with clear headings.

**Risk: B2B caps reference each other** → Audit logging references Organization/Membership/APIKey/WebhookEndpoint. Admin backoffice references AuditLog. These cross-references are documented in the specs as dependency statements rather than import paths, to keep specs stable as code evolves.

**Risk: cli-scaffolder ADDED requirement uses wrong delta format** → The existing cli-scaffolder spec has content in `## ADDED Requirements`. Adding a new `## ADDED Requirements` section in the delta would create a duplicate header at archive time. Mitigation: write the delta spec with a single new requirement block under `## ADDED Requirements` — the archive tool appends requirements, not entire sections.
