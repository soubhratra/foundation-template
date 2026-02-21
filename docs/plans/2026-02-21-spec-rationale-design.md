# Design: Self-Contained Spec Rationale

**Date:** 2026-02-21
**Status:** Approved

## Problem

Foundation specs (`openspec/specs/foundation/`) are copied to every new product scaffolded by the CLI. But:

1. Every spec ends with a `## References` section pointing to `.planning/research/*.md` files — which are **explicitly excluded** from scaffolded products (`copy.ts` line 47: `ig.add(".planning")`). These are dead links in any new product repo.

2. One critical architectural decision — `pnpm node-linker=hoisted` (required for Metro/Expo compatibility) — exists only in MEMORY.md, not in any spec.

3. The Turborepo+Python pitfall (what breaks if you treat Django as a real pnpm workspace) is documented thoroughly in `.planning/research/PITFALLS.md` but only as a thin constraint note in `architecture.md`.

## Decision

**Approach A: Self-Contained Spec Enrichment.** Surgical edits only — plug the real gaps, don't rewrite what's already good.

## Changes

### `openspec/specs/foundation/architecture.md`

1. Add `pnpm node-linker=hoisted` under "Workspace Configuration Patterns":
   - **What:** `.npmrc` setting `node-linker=hoisted`
   - **Why:** Metro bundler (Expo) cannot resolve packages from pnpm's default symlink strategy. Hoisted layout puts all modules flat in `node_modules/` where Metro finds them.
   - **Rejected:** default pnpm symlink strategy — silently fails with Metro, produces difficult-to-debug "cannot find module" errors at bundle time.

2. Expand the "Django is a pnpm workspace for task orchestration only" constraint:
   - Add "What breaks if you skip this" note from PITFALLS.md (Turborepo cache miss every CI run, Python tests re-run on every push despite no changes).

3. Replace `## References` with self-contained note.

### All other foundation specs (5 files)

`stack.md`, `auth.md`, `api-contracts.md`, `ai-stack.md`, `conventions.md`:

- Replace `## References` section (dead `.planning/` links) with a self-contained note.

### `CLAUDE.md`

Add "Self-Contained Specs Rule" under the OpenSpec Rules section:

- Specs must include what + why + alternatives rejected.
- Never reference `.planning/` as rationale source — excluded from scaffolded products.
- Applies equally to product-specific specs in `openspec/specs/[domain]/`.

## Scope

- 7 files modified (6 foundation specs + CLAUDE.md)
- All changes are additive or substitutions — no existing rationale removed
- `architecture.md` gets the most content; the other 5 specs only get a References fix
