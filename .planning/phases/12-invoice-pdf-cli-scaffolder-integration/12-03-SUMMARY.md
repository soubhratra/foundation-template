---
phase: 12-invoice-pdf-cli-scaffolder-integration
plan: "03"
subsystem: testing
tags: [pytest, subprocess, cli, scaffolder, billing, nodejs, esm, fs-extra]

requires:
  - phase: 12-01
    provides: WeasyPrint invoice PDF generation endpoints
  - phase: 12-02
    provides: removeBillingModule() compiled to dist/remove.js; vitest suite green

provides:
  - apps/api/tests/test_scaffolder_billing_removal.py (SCAFF-04 pytest integration test)
  - Fixed ESM-compatible fs-extra imports in CLI source (remove.ts, rollback.ts, copy.ts)
  - Rebuilt CLI dist/ that works on Node.js v24

affects:
  - packages/create-foundation-app/src (fixed imports affect all CLI functionality)

tech-stack:
  added: []
  patterns:
    - Node.js subprocess with --input-type=module for ESM module function invocation without interactive TTY
    - fs-extra default import + destructuring pattern for Node.js v24 ESM compatibility

key-files:
  created:
    - apps/api/tests/test_scaffolder_billing_removal.py
  modified:
    - packages/create-foundation-app/src/remove.ts (fs-extra default import fix)
    - packages/create-foundation-app/src/rollback.ts (fs-extra default import fix)
    - packages/create-foundation-app/src/copy.ts (fs-extra default import fix)

key-decisions:
  - "CLI invoked via node --input-type=module inline script (not dist/index.js) because index.js requires interactive TTY; calling dist/remove.js directly still exercises compiled TypeScript"
  - "fs-extra named ESM imports replaced with default import + destructuring (import fse from 'fs-extra'; const { readFile, writeFile, remove } = fse;) to fix Node.js v24 CJS named-export synthesis removal"

patterns-established:
  - "SCAFF-04 pattern: pytest integration test calls compiled Node.js module via subprocess --input-type=module to avoid duplicating TypeScript logic in Python"

requirements-completed:
  - SCAFF-03
  - SCAFF-04

duration: 8min
completed: "2026-03-10"
---

# Phase 12 Plan 03: SCAFF-04 Integration Test Summary

**pytest integration test calls compiled dist/remove.js via Node.js subprocess, exercising actual TypeScript removeBillingModule() — all 7 billing-absence assertions GREEN; fixed ESM/CJS fs-extra incompatibility that broke CLI on Node.js v24.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-10T13:09:00Z
- **Completed:** 2026-03-10T13:12:22Z
- **Tasks:** 1 of 2 (Task 2 is checkpoint:human-verify — awaiting human)
- **Files modified:** 4

## Accomplishments

- Created `apps/api/tests/test_scaffolder_billing_removal.py` with 1 pytest test (SCAFF-04) that invokes the compiled CLI module via subprocess — all 7 billing-absence assertions GREEN
- Discovered and auto-fixed Node.js v24 ESM/CJS incompatibility in `fs-extra` imports across all CLI source files — the compiled CLI was entirely broken before this fix
- Full pytest suite (74 passed, 1 skipped) and vitest suite (7/7) remain GREEN after fixes

## Task Commits

Each task was committed atomically:

1. **Task 1: SCAFF-04 — pytest test invoking compiled CLI via subprocess** - `5ce71f5` (test)

Task 2 (human-verify checkpoint) is pending human approval.

## Files Created/Modified

- `apps/api/tests/test_scaffolder_billing_removal.py` — SCAFF-04 pytest integration test; uses `node --input-type=module` inline script to call `removeBillingModule()` from compiled `dist/remove.js` without requiring an interactive TTY
- `packages/create-foundation-app/src/remove.ts` — Fixed `import fse from "fs-extra"; const { readFile, writeFile, remove } = fse;`
- `packages/create-foundation-app/src/rollback.ts` — Fixed `import fse from "fs-extra"; const { remove, pathExists } = fse;`
- `packages/create-foundation-app/src/copy.ts` — Fixed `import fse from "fs-extra"; const fs = fse;`

## Decisions Made

1. **node --input-type=module inline script** — The full CLI (`dist/index.js`) requires interactive TTY for @clack/prompts (project name, feature selection, output dir). No `--output-dir` or `--non-interactive` flags exist. Instead, the test passes a Node.js inline ESM script via stdin to `node --input-type=module`, which imports and calls `removeBillingModule()` from the compiled `dist/remove.js`. This is still a subprocess over compiled TypeScript — any bug in the compiled output surfaces here.

2. **fs-extra default import** — Node.js v24 removed named-export synthesis for CJS modules in ESM context. `fs-extra` is CJS-only; `import { readFile } from 'fs-extra'` fails at module load. The fix: `import fse from 'fs-extra'; const { readFile, ... } = fse;`. The default export of fs-extra (its `module.exports`) contains all functions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CLI entirely broken on Node.js v24 due to fs-extra named ESM imports**

- **Found during:** Task 1 (attempting to invoke dist/remove.js via subprocess)
- **Issue:** `dist/remove.js`, `dist/rollback.js`, and `dist/copy.js` all use named imports from `fs-extra` (e.g., `import { readFile, writeFile, remove } from "fs-extra"`). Node.js v24 no longer synthesizes named exports for CJS modules in ESM context. All three dist files fail to load — the entire CLI is broken before the fix.
- **Fix:** Changed to default import + destructuring in the three source files: `import fse from "fs-extra"; const { readFile, writeFile, remove } = fse;`. Rebuilt CLI with `pnpm build`. Confirmed vitest suite (7/7) still GREEN.
- **Files modified:** `packages/create-foundation-app/src/remove.ts`, `packages/create-foundation-app/src/rollback.ts`, `packages/create-foundation-app/src/copy.ts`
- **Verification:** `node --input-type=module` import of `dist/remove.js` succeeds; pytest test passes; vitest 7/7 GREEN
- **Committed in:** `5ce71f5` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Auto-fix necessary for the CLI to be functional at all on Node.js v24. No scope creep — the fix is in the exact files that removeBillingModule() lives in.

## Issues Encountered

The plan's suggested subprocess approach (`node dist/index.js --without billing --output-dir {tmpdir} --non-interactive`) was not feasible — `dist/index.js` doesn't accept those flags; it's a fully interactive @clack/prompts flow. The fallback approach (calling `dist/remove.js` directly via `node --input-type=module`) achieves the same goal: the compiled TypeScript is exercised, any TypeScript bug in `removeBillingModule()` will surface here.

## Awaiting Human Verification

Task 2 is `checkpoint:human-verify`. Human must:

1. Run `cd apps/api && python -m pytest tests/ -q` — confirm all green
2. Start dev env and test invoice PDF download flow at `/billing`
3. Test scaffolder billing prompt (`node dist/index.js --skip-validation` — billing pre-checked)
4. Test `--without billing` flag (verify billing artifacts absent in scaffolded project)

## Next Phase Readiness

- Phase 12 automated tests complete — SCAFF-04 pytest test green, full suite clean
- Human checkpoint (Task 2) required before phase can be marked DONE
- After human approval: phase 12 complete, milestone v1.1 Billing & Payments done

## Self-Check: PASSED

- FOUND: `/Users/soubhratra/workspace/foundation-template/apps/api/tests/test_scaffolder_billing_removal.py`
- FOUND: `packages/create-foundation-app/src/remove.ts` (with fs-extra default import)
- FOUND: `packages/create-foundation-app/src/rollback.ts` (with fs-extra default import)
- FOUND: `packages/create-foundation-app/src/copy.ts` (with fs-extra default import)
- FOUND commit 5ce71f5: test(12-03): SCAFF-04 integration test + fix fs-extra ESM imports for Node 24

---

_Phase: 12-invoice-pdf-cli-scaffolder-integration_
_Completed: 2026-03-10 (partial — awaiting human-verify checkpoint)_
