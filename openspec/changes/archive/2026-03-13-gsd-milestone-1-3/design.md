## Context

Five capability specs exist in `openspec/specs/` from prior template work but predate the implementation decisions made during milestone v1.3 execution (phases 19–25). GSD planning documents (phase SUMMARY.md files, VERIFICATION.md, ROADMAP.md, and the milestone audit) contain the authoritative record of what was built and why, but that context lives only in `.planning/` — which is never copied to product repos scaffolded from this template.

This design sync writes the missing "what was decided and why" into the five relevant specs so they become self-contained and accurate.

## Goals / Non-Goals

**Goals:**

- Update five existing specs with implementation decisions from milestone 1.3
- Capture rationale for non-obvious choices (Resend over SendGrid, RequireRole returning False, Apple JWT endpoint, UserDeletionService orchestrator pattern)
- Document all 4 accumulated tech debt items so product developers are aware before extending these capabilities
- Keep each spec self-contained: a developer reading only the spec should understand the decision and could make consistent future choices without reading `.planning/`

**Non-Goals:**

- No code changes — this is documentation only
- Not capturing every line of implementation; only decisions with meaningful rationale
- Not creating new specs — only updating the five that correspond to shipped capabilities
- Not resolving tech debt — only documenting it; resolution is a future phase decision

## Decisions

### Decision 1: Update existing specs directly (not create delta spec files)

**Choice:** Write decisions into the main spec files under `openspec/specs/<capability>/spec.md` directly.

**Rationale:** The five capabilities are all new to v1.3 — their existing specs are placeholder or skeleton files with minimal content. There is no prior "truth" to protect via a delta. Writing directly is cleaner than a delta that is essentially the entire spec body.

**Alternative rejected:** Create delta specs under `openspec/changes/gsd-milestone-1-3/specs/<capability>/spec.md` and archive them. This is correct for update-to-established specs; however, since these specs are largely empty stubs from initial template setup, the delta would be indistinguishable from the spec itself. Direct update is appropriate here.

### Decision 2: Each spec gets an Implementation Decisions section

**Choice:** Add a clearly-labelled `## Implementation Decisions` section to each spec, listing decisions with rationale and alternatives-rejected.

**Rationale:** Separating decisions from requirements makes it easy for future developers to distinguish "what the system must do" (requirements) from "how it was built and why" (decisions). The decisions section can grow independently as new products extend these capabilities.

### Decision 3: Tech debt items live in the spec of the owning capability

**Choice:** Tech debt is documented in the spec for the capability where it was incurred, not in a separate shared location.

**Rationale:** A developer extending RBAC needs to know about the `AdminController` auth= gap when they read the RBAC spec — they should not need to cross-reference a separate tech debt registry.

### Decision 4: Document decisions in order of impact on product developers

Within each spec, decisions are ordered: (1) most likely to affect new product developers first, (2) edge cases and known gaps, (3) tech debt items last.

## Risks / Trade-offs

**Risk: Specs diverge from code over time** → Mitigation: Each decision includes enough rationale that future developers will recognise when a spec needs updating, rather than silently continuing with outdated assumptions.

**Risk: Tech debt items persist indefinitely** → Mitigation: Documenting them (rather than ignoring them) creates accountability. The `AdminController` auth= gap is explicitly called out so it is not treated as the "correct" pattern when developers add new controllers.

**Risk: Decision rationale becomes stale (e.g. anymail/SendGrid support may change)** → Mitigation: Rationale cites external facts with dates (e.g. "anymail dropped official SendGrid support June 2025") so future readers know the basis was time-bounded.
