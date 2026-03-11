## Context

Milestone v1.1 execution produced 31 implementation decisions captured in `.planning/STATE.md`. The original design proposal (`2026-03-07-payment-and-billing`) documented intent, not actuality. This change is a documentation-only sync: copy finalized decisions into the live specs so they serve as self-contained source of truth for future developers and AI agents.

No code changes. No migrations. No dependency updates.

## Goals / Non-Goals

**Goals:**

- Reflect all 31 v1.1 implementation decisions in their canonical spec files
- Make each spec self-contained (rationale inline, no `.planning/` references required)
- Create `billing-cli-scaffolder/spec.md` as a new spec that did not exist before v1.1

**Non-Goals:**

- Restructuring or rewriting existing spec sections
- Documenting v1.0 decisions (already synced)
- Retroactive changes to code or configuration

## Decisions

**Decision: Update existing specs in-place, not via replacement**
Each spec gets a new "Implementation Notes" or decision-tagged section appended to the relevant requirement. This preserves the existing BDD scenario structure while adding the rationale that emerged during execution.

**Decision: New spec for `billing-cli-scaffolder`**
The billing removal capability (`removeBillingModule()`) is distinct from the general CLI scaffolder spec (`foundation/cli-scaffolder.md`). It has billing-specific block patterns, flag behavior, and Node.js compatibility constraints. A separate spec under `openspec/specs/billing-cli-scaffolder/spec.md` keeps concerns separated.

**Decision: Source of truth is STATE.md decisions, not SUMMARY.md files**
The 31 decisions are already distilled and finalized in STATE.md. Reading SUMMARY.md files for additional context is unnecessary for this sync.

## Risks / Trade-offs

- **Risk:** Some decisions may duplicate content already implied by the original spec scenarios → Mitigation: Add decisions only where they add rationale not already present; skip if redundant.
- **Risk:** `billing-cli-scaffolder` spec may overlap with `foundation/cli-scaffolder.md` → Mitigation: Scope it strictly to billing removal; cross-reference the foundation spec for general scaffolder patterns.

## Migration Plan

1. Update `openspec/specs/stripe-billing/spec.md`
2. Update `openspec/specs/billing-ui/spec.md`
3. Create `openspec/specs/billing-cli-scaffolder/spec.md`
4. Archive this change via `/opsx:archive gsd-milestone-v1-1-sync`

No rollback needed — additive documentation changes only.
