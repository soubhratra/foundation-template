# Phase 31: CLI Scaffolder Integration - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend `packages/create-foundation-app` to support B2B opt-in/opt-out: add the `--with b2b` flag, implement B2B block stripping and directory deletion, audit and fix any missing markers, and add a pytest CI test that verifies both the B2B-included and B2B-excluded scaffolds pass `manage.py check`.

Not in scope: adding new B2B_START/END markers to TypeScript/frontend files, changing how any other feature flag works, or modifying the B2B module itself.

</domain>

<decisions>
## Implementation Decisions

### Flag design

- **Opt-in**: `--with b2b` — B2B is excluded by default. Most projects don't need it; it's an enterprise add-on.
- **Interactive prompt**: B2B appears in the multiselect (`"B2B Module (Organizations, API Keys, Webhooks, Audit)"`) with an **unchecked default**. Consistent with all other optional features.
- **Flag behavior**: `--with b2b` auto-selects B2B and bypasses the interactive prompt item for B2B (same pattern as `--without billing` auto-deselects billing). Intent is authoritative — no confirmation needed.
- **Independence**: B2B and billing are fully independent. No warning if `--with b2b` without billing selected.

### Removal implementation

- **Hybrid approach**: two separate concerns, two mechanisms:
  1. **Generic marker stripper** in `transform.ts` — strips all `# B2B_START` / `# B2B_END` blocks from Python files when B2B is not selected. Reusable for any future marker-based feature. Python comment style only (`# B2B_START`, `# B2B_END`).
  2. **`removeB2BModule()`** in `remove.ts` — handles structural removal: delete B2B directories (`apps/api/apps/orgs/`, `apps/api/apps/api_keys/`, `apps/api/apps/webhooks/`, `apps/api/apps/audit/`), remove B2B pyproject.toml deps (`django-pghistory`, `django-hijack`) via explicit regex string matching (not markers — consistent with how billing/AI deps are removed).
- **Both run together**: `removeB2BModule()` runs first (deletes dirs, patches pyproject.toml), then marker stripper runs on all remaining Python files.
- **Blank line cleanup**: after stripping B2B blocks, collapse consecutive blank lines to max 1 in any modified file. Apply only to files that were actually changed.
- **pyproject.toml**: deps removed via explicit string matching — no B2B markers added to TOML files.

### Marker coverage

- **Trust but audit**: Trust that Phases 26-30 placed all necessary markers. Phase 31 execution audits by running `manage.py check` on the stripped output — that's the ground truth.
- **Fix in Phase 31**: If a missing or incorrect marker is found during execution, fix it in Phase 31 (don't fail and block; just add the marker and continue).
- **Unmatched marker warning**: If the stripper finds an unmatched `# B2B_START` or `# B2B_END` (i.e., a start without a matching end, or vice versa), print a warning with the file path and line number, but continue stripping. Useful for catching future marker placement bugs.

### CI validation test

- **Approach**: In-process simulation using pytest `tmp_path`. The test copies the template directory, calls the removal Python logic (via subprocess or direct Python functions), then runs `manage.py check` in the copy. Fast, self-contained, no CLI build required.
- **Test location**: `apps/api/tests/scaffolder/test_b2b_scaffold.py` — part of standard pytest suite, runs in CI.
- **Two tests**:
  - `test_scaffold_without_b2b`: applies removal, asserts `manage.py check` passes, then asserts all four negative conditions (see below).
  - `test_scaffold_with_b2b`: skips removal, asserts `manage.py check` passes with full B2B stack installed.
- **Assertions for `test_scaffold_without_b2b`**:
  1. No `# B2B_START` or `# B2B_END` markers remain in any file in the output
  2. `apps.orgs`, `apps.webhooks`, `apps.api_keys`, `apps.audit` absent from `INSTALLED_APPS` in settings
  3. B2B directories (`apps/orgs/`, `apps/api_keys/`, `apps/webhooks/`, `apps/audit/`) do not exist in the output
  4. `django-pghistory` and `django-hijack` absent from `pyproject.toml`

### Claude's Discretion

- Exact regex pattern for the marker stripper (handle indented markers, trailing whitespace, etc.)
- Whether `removeB2BModule()` calls the marker stripper internally or index.ts calls them in sequence
- Whether the test uses subprocess to run the TypeScript removal (built CLI) or a Python re-implementation of the removal logic
- Warning output format for unmatched markers (logger.warning vs p.log.warn)

</decisions>

<specifics>
## Specific Ideas

- The marker stripper should be designed as a standalone function (not B2B-specific) so future features can reuse it: `stripMarkerBlocks(content: string, markerName: string): string`. B2B would call it as `stripMarkerBlocks(content, "B2B")`.
- `--with b2b` follows the same CLI parsing pattern as `--without billing` — check `process.argv` before interactive prompts and adjust `initialValues` in the multiselect accordingly.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `src/transform.ts`: `replaceInFiles()` + `globby` pattern — the marker stripper follows the same file-scanning approach (find all `.py` files, read, transform, write)
- `src/remove.ts`: `removeAIModule()`, `removeBillingModule()` — exact same structure for `removeB2BModule()`: delete dirs, patch pyproject.toml deps, patch settings if needed
- `src/index.ts`: CLI flag parsing for `--without billing` (lines ~25-42) — `--with b2b` uses same `process.argv` approach; multiselect `initialValues` in `prompts.ts` controls defaults

### Established Patterns

- Feature flags parsed from `process.argv` BEFORE interactive prompts — flag overrides prompt selection
- `removeX()` functions: delete directory → patch pyproject.toml → patch settings (sequentially, throwing on unexpected errors, tolerating ENOENT)
- All feature removal happens in Step 4 of `main()`: `if (!config.features.includes("X")) { await removeX(config.outputDir) }`
- Validation runner already runs pnpm install + lint + type-check — `manage.py check` not currently included

### Integration Points

- `src/prompts.ts` → add `"b2b"` to `SelectedFeatures` type and multiselect options (unchecked default)
- `src/index.ts` → parse `--with b2b` flag, add `if (!config.features.includes("b2b")) { await removeB2BModule(config.outputDir) }` in Step 4
- `src/transform.ts` → add generic `stripMarkerBlocks()` function; call it from `removeB2BModule()` (or from index.ts after removal)
- `src/remove.ts` → add `removeB2BModule()` with dir deletion + pyproject.toml dep removal
- `apps/api/tests/scaffolder/test_b2b_scaffold.py` → new test file (new `scaffolder/` subdirectory under tests)

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

_Phase: 31-cli-scaffolder-integration_
_Context gathered: 2026-03-13_
