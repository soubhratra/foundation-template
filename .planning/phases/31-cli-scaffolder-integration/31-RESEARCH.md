# Phase 31: CLI Scaffolder Integration - Research

**Researched:** 2026-03-13
**Domain:** TypeScript CLI scaffolder extension + Python pytest CI validation
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Flag design**

- Opt-in: `--with b2b` — B2B is excluded by default
- Interactive prompt: B2B appears in multiselect (`"B2B Module (Organizations, API Keys, Webhooks, Audit)"`) with unchecked default
- `--with b2b` auto-selects B2B and bypasses the prompt item; no confirmation needed
- B2B and billing are fully independent

**Removal implementation**

- Hybrid approach: generic `stripMarkerBlocks()` in `transform.ts` + `removeB2BModule()` in `remove.ts`
- `stripMarkerBlocks(content: string, markerName: string): string` — Python comment style only (`# B2B_START`, `# B2B_END`)
- `removeB2BModule()` deletes: `apps/api/apps/orgs/`, `apps/api/apps/api_keys/`, `apps/api/apps/webhooks/`, `apps/api/apps/audit/`
- `removeB2BModule()` removes pyproject.toml deps: `django-pghistory`, `django-hijack` — via explicit regex matching (same pattern as billing/AI)
- `removeB2BModule()` runs first, then marker stripper runs on all remaining Python files
- Blank line cleanup: collapse consecutive blank lines to max 1 in modified files only
- pyproject.toml deps removed via explicit string matching — no B2B markers in TOML

**Marker coverage**

- Trust but audit: Phase 31 execution audits by running `manage.py check` on stripped output
- Fix missing markers in Phase 31 if found
- Unmatched marker warning: print file path + line number, then continue (no abort)

**CI validation test**

- In-process simulation using pytest `tmp_path`
- Test location: `apps/api/tests/scaffolder/test_b2b_scaffold.py`
- Two tests: `test_scaffold_without_b2b` and `test_scaffold_with_b2b`
- `test_scaffold_without_b2b` assertions:
  1. No `# B2B_START` or `# B2B_END` markers remain in any file
  2. `apps.orgs`, `apps.webhooks`, `apps.api_keys`, `apps.audit` absent from `INSTALLED_APPS`
  3. B2B directories do not exist in output
  4. `django-pghistory` and `django-hijack` absent from `pyproject.toml`

### Claude's Discretion

- Exact regex pattern for the marker stripper (handle indented markers, trailing whitespace, etc.)
- Whether `removeB2BModule()` calls the marker stripper internally or `index.ts` calls them in sequence
- Whether the test uses subprocess to run the TypeScript removal (built CLI) or a Python re-implementation of the removal logic
- Warning output format for unmatched markers (`logger.warning` vs `p.log.warn`)

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope.
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                                 | Research Support                                                                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SCAFF-01 | `--with b2b` flag in `create-foundation-app`; all B2B code uses `# B2B_START`/`# B2B_END` markers; removal produces clean `manage.py check` | Marker inventory below identifies one unmatched marker to fix; CLI patterns in `remove.ts` and `index.ts` fully established; test pattern from `test_scaffolder_billing_removal.py` is directly reusable |

</phase_requirements>

---

## Summary

Phase 31 is an extension to `packages/create-foundation-app` — a TypeScript CLI package. All patterns needed already exist in the codebase. The `removeAIModule()`, `removeBillingModule()`, and similar functions in `remove.ts` provide exact templates for `removeB2BModule()`. The `--without billing` / `--without observability` flag parsing in `index.ts` (lines 44-58) provides the exact pattern for `--with b2b`. The `promptFeatures()` multiselect in `prompts.ts` shows where to add the B2B option.

The most important pre-execution finding is a **confirmed unmatched `# B2B_START` marker** in `apps/api/config/settings/base.py` at line 670. The `WEBHOOK_EVENTS`, `WEBHOOK_DELIVERY_RETENTION_DAYS`, `WEBHOOK_CIRCUIT_BREAKER_THRESHOLD`, `API_KEY_PREFIX`, `API_KEY_RATE_LIMIT`, and `API_KEY_SCOPES` settings block has an opening `# B2B_START` at line 670 but no `# B2B_END` before the next `# B2B_START` at line 698. The block needs a `# B2B_END` inserted at approximately line 697 (after `API_KEY_SCOPES` closes). This is a Phase 31 fix as specified in CONTEXT.md.

The CI test should use the same subprocess-over-compiled-dist pattern established by `test_scaffolder_billing_removal.py` — this exercises the actual TypeScript logic rather than re-implementing it in Python. The decision between subprocess and Python re-implementation is Claude's discretion; existing tests consistently use subprocess.

**Primary recommendation:** Copy the `removeBillingModule()` structure for `removeB2BModule()`; add `stripMarkerBlocks()` as a new standalone function in `transform.ts` called at the end of `removeB2BModule()`; fix the one unmatched marker in `base.py`; add the B2B option to `prompts.ts` (unchecked default); wire `--with b2b` flag parsing in `index.ts` (opt-in guard, opposite polarity from `--without` flags).

---

## Standard Stack

### Core (already in project, no installs needed)

| Library          | Version      | Purpose                                        | Why Standard                                      |
| ---------------- | ------------ | ---------------------------------------------- | ------------------------------------------------- |
| `globby`         | existing dep | Glob file scanner for Python file discovery    | Already used in `transform.ts` `replaceInFiles()` |
| `fs-extra`       | existing dep | `readFile`, `writeFile`, `remove` for file ops | Already used across `remove.ts`                   |
| `@clack/prompts` | existing dep | multiselect, log.warn, spinner                 | Already used in `index.ts` and `prompts.ts`       |
| `pytest`         | existing dep | Test runner for CI scaffold test               | Already the project test framework                |

### No New Dependencies

This phase adds zero new npm or Python packages. All tools are already installed.

---

## Architecture Patterns

### Recommended Project Structure Changes

```
packages/create-foundation-app/src/
├── transform.ts        # ADD: stripMarkerBlocks() function
├── remove.ts           # ADD: removeB2BModule() function
├── prompts.ts          # MODIFY: add "b2b" to SelectedFeatures type + multiselect option
└── index.ts            # MODIFY: --with b2b flag parsing + removal call in Step 4

apps/api/tests/scaffolder/
└── test_b2b_scaffold.py  # NEW: two tests (with/without B2B)

apps/api/config/settings/base.py
└── # FIX: add missing # B2B_END at ~line 697
```

### Pattern 1: Opt-in Flag Parsing (opposite polarity from --without)

The existing pattern handles opt-out (`--without billing`). B2B is opt-in (`--with b2b`). The difference: existing code reads prompt result then filters OUT flagged features. For B2B, the prompt default is unchecked, so `--with b2b` must filter IN.

```typescript
// Existing pattern in index.ts (lines 44-78) for reference:
const withoutBillingFlag = withoutArgs.includes("--without-billing");
const features = rawFeatures.filter((f) => !(withoutBillingFlag && f === "billing"));

// New pattern for --with b2b (opt-in):
const withB2bFlag =
  (withIdx !== -1 && withArgs[withIdx + 1] === "b2b") || withArgs.includes("--with-b2b");
// B2B not added to initialValues in prompts.ts, so it's unchecked by default.
// If --with b2b flag present, add "b2b" to the features array after prompts:
const features = [...rawFeatures, ...(withB2bFlag && !rawFeatures.includes("b2b") ? ["b2b"] : [])];
```

### Pattern 2: Feature Removal in index.ts Step 4

```typescript
// Existing pattern (index.ts ~line 118-141):
if (!config.features.includes("billing")) {
  await removeBillingModule(config.outputDir);
}

// B2B follows same guard — B2B is removed unless explicitly selected:
if (!config.features.includes("b2b")) {
  await removeB2BModule(config.outputDir);
}
```

### Pattern 3: removeB2BModule() Structure

Follow `removeBillingModule()` exactly. The B2B removal is simpler (no web app files to touch):

```typescript
export async function removeB2BModule(outputDir: string): Promise<void> {
  // 1. Delete four B2B app directories (ENOENT-tolerant)
  for (const dir of ["orgs", "api_keys", "webhooks", "audit"]) {
    await remove(join(outputDir, `apps/api/apps/${dir}`));
  }
  // 2. Remove B2B deps from pyproject.toml (same regex as billing/AI deps)
  //    Targets: "django-pghistory>=...", "django-hijack>=..."
  // 3. Run stripMarkerBlocks on all *.py files in outputDir
}
```

### Pattern 4: stripMarkerBlocks() Generic Function

The marker stripper is standalone and reusable. Python comment markers use `# MARKER_START` / `# MARKER_END` style. The regex must handle:

- Leading whitespace (markers may be indented inside `if` blocks, list literals, dicts)
- Trailing comment text after the marker (e.g., `# B2B_START — hijack signal handlers`)
- The entire line including the newline

**Regex approach:**

```typescript
// Source: derived from existing pattern in remove.ts line 292 (BILLING_START/END removal)
export function stripMarkerBlocks(content: string, markerName: string): string {
  // Matches: optional whitespace + "# MARKER_START" + optional trailing text + newline
  // through: optional whitespace + "# MARKER_END" + optional trailing text + newline
  // The [\s\S]*? is non-greedy to handle multiple blocks
  const regex = new RegExp(
    `[ \\t]*# ${markerName}_START[^\\n]*\\n[\\s\\S]*?[ \\t]*# ${markerName}_END[^\\n]*\\n`,
    "g",
  );
  return content.replace(regex, "");
}
```

**Blank line collapse (after stripping):**

```typescript
// Apply only to content that was actually changed:
if (stripped !== content) {
  stripped = stripped.replace(/\n{3,}/g, "\n\n");
}
```

**Unmatched marker warning:**

```typescript
// After stripping, scan for orphaned markers:
const remaining = stripped.match(/[ \t]*# B2B_(START|END)[^\n]*/g);
if (remaining) {
  logger.warning(`Unmatched B2B marker in ${filePath}: ${remaining.join(", ")}`);
}
```

### Pattern 5: SelectedFeatures Type Extension (prompts.ts)

```typescript
// Current (line 7-9):
export type SelectedFeatures = Array<
  "web" | "mobile" | "landing" | "ai" | "billing" | "observability" | "email" | "social-auth"
>;

// New (add "b2b"):
export type SelectedFeatures = Array<
  | "web"
  | "mobile"
  | "landing"
  | "ai"
  | "billing"
  | "observability"
  | "email"
  | "social-auth"
  | "b2b"
>;
```

B2B option in multiselect — NOT added to `initialValues` array (unchecked by default):

```typescript
{
  value: "b2b",
  label: "B2B Module (Organizations, API Keys, Webhooks, Audit)",
},
```

### Pattern 6: CI Test Structure

Follow `test_scaffolder_billing_removal.py` exactly. That file:

- Uses `tmp_path` fixture to copy relevant source files
- Invokes the compiled `dist/remove.js` via Node.js subprocess using `--input-type=module`
- Asserts artifacts are absent from the copied directory
- Has `@pytest.mark.skipif(not CLI_DIST_REMOVE.exists(), ...)` guard
- Lives in `apps/api/tests/` (root level, not a subdirectory)

**New location:** `apps/api/tests/scaffolder/test_b2b_scaffold.py` (new `scaffolder/` subdirectory)

This requires `apps/api/tests/scaffolder/__init__.py` to exist (empty file) for pytest to discover it.

**Test 1: test_scaffold_without_b2b**

```python
# Source: mirrors test_scaffolder_billing_removal.py
def test_scaffold_without_b2b(tmp_path: Path) -> None:
    # 1. Copy ALL relevant template files to tmp_path:
    #    - apps/api/config/settings/ (base.py, development.py)
    #    - apps/api/config/urls.py
    #    - apps/api/apps/orgs/, api_keys/, webhooks/, audit/
    #    - apps/api/pyproject.toml
    # 2. Run removeB2BModule() via Node.js subprocess on tmp_path
    # 3. Assert four negative conditions (from CONTEXT.md decisions)
```

**Test 2: test_scaffold_with_b2b**

```python
def test_scaffold_with_b2b(tmp_path: Path) -> None:
    # 1. Copy full template to tmp_path (all B2B dirs present)
    # 2. Run manage.py check in the copy (subprocess)
    # 3. Assert returncode == 0
    # Note: requires Django + B2B deps to be installed in the test environment
    # — these are already installed (tests run in apps/api/ venv)
```

### Anti-Patterns to Avoid

- **Re-implementing TypeScript removal in Python:** Existing scaffolder tests use subprocess over compiled dist. Re-implementing logic in Python would allow TypeScript bugs to pass silently. Use subprocess like `test_scaffolder_billing_removal.py`.
- **Greedy regex for marker blocks:** Using `[\s\S]*` (greedy) instead of `[\s\S]*?` (non-greedy) would collapse multiple B2B blocks into one match, stripping everything between the first `B2B_START` and the last `B2B_END`.
- **Applying blank line collapse globally:** Only apply `\n{3,}` → `\n\n` to files actually modified by stripping. Avoids touching unrelated files.
- **Adding "b2b" to initialValues in prompts.ts:** B2B must be unchecked by default (opt-in). Adding it to `initialValues` would make it checked by default, breaking the opt-in design.
- **Assuming `django-unfold` is B2B-only:** `unfold` and `unfold.contrib.filters` are in `INSTALLED_APPS` outside any B2B marker. They are NOT removed when B2B is excluded — the admin theme is unconditional.

---

## Don't Hand-Roll

| Problem                                    | Don't Build                          | Use Instead                                    | Why                                                                 |
| ------------------------------------------ | ------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------- |
| File glob scanning                         | Custom `fs.readdir` recursive walker | `globby` (already in `transform.ts`)           | Already used; handles gitignore, dotfiles, `node_modules` exclusion |
| Python file discovery for marker stripping | Separate glob implementation         | Reuse `globby` pattern from `replaceInFiles()` | Consistent approach, tested                                         |
| Subprocess invocation in tests             | Custom subprocess wrapper            | Python stdlib `subprocess.run`                 | Same pattern in all 4 existing scaffolder tests                     |

---

## Common Pitfalls

### Pitfall 1: Unmatched B2B_START at base.py Line 670

**What goes wrong:** The marker stripper finds `# B2B_START` at line 670 but the next token is another `# B2B_START` at line 698 (not a `# B2B_END`). The non-greedy regex `[\s\S]*?` will NOT match across two `_START` markers — it looks for `_END`. The block from line 670 to ~697 (`WEBHOOK_EVENTS`, `WEBHOOK_DELIVERY_RETENTION_DAYS`, `WEBHOOK_CIRCUIT_BREAKER_THRESHOLD`, `API_KEY_PREFIX`, `API_KEY_RATE_LIMIT`, `API_KEY_SCOPES`) will NOT be stripped. `manage.py check` on the B2B-excluded scaffold will fail because `apps.webhooks` is absent but `WEBHOOK_EVENTS` still references it conceptually.

**Root cause:** Missing `# B2B_END` after `API_KEY_SCOPES` closes at line 697 in `base.py`.

**How to avoid:** Phase 31 execution must add `# B2B_END` at line 697 (after `}` closing `API_KEY_SCOPES`) before running tests.

**Warning signs:** The unmatched marker warning from `stripMarkerBlocks()` will fire for this file, flagging line 670 as orphaned.

**Verification:** After fix, `grep -c "B2B_START" base.py` and `grep -c "B2B_END" base.py` should return the same count.

### Pitfall 2: manage.py check Requires Full Django Environment

**What goes wrong:** `test_scaffold_with_b2b` calls `manage.py check` on the real template source — not a copy. This requires all B2B dependencies (`django-pghistory`, `django-hijack`) to be installed in the active Python environment.

**Root cause:** These packages ARE installed (they're in `apps/api/pyproject.toml`), so the test runs fine in the standard `uv sync` environment.

**How to avoid:** Ensure the test runs with `cwd=apps/api/` or uses the same `.venv` as the template. No extra setup needed — the test environment already has B2B deps installed.

### Pitfall 3: Marker Regex Indentation Handling

**What goes wrong:** Markers appear at different indentation levels: some are at column 0 (`# B2B_START` in `admin.py`), some are indented 4 spaces (inside `INSTALLED_APPS` list), some are indented 12 spaces (inside `UNFOLD` dict inside `SIDEBAR` inside `navigation`).

**Root cause:** Python files have markers inside list literals, dict values, and function bodies.

**How to avoid:** Use `[ \t]*` (not `^`) at the start of the marker regex pattern to match any leading horizontal whitespace. Do NOT anchor with `^` unless using the `m` flag with `[ \t]*`.

**Confirmed marker locations (by depth):**

- Column 0: `apps/api_keys/admin.py:1`, `apps/orgs/admin.py:1`, `apps/audit/admin.py:1`, `apps/webhooks/admin.py:1`, `apps/accounts/permissions.py:42`, `config/settings/base.py:670`, `config/settings/base.py:698`
- Indented 4: `config/settings/base.py:100,125,146,153,337`, `config/urls.py:170`
- Indented 8: `apps/audit/models.py:11`, `apps/audit/apps.py:13`, `apps/audit/middleware.py:33`
- Indented 12: `config/settings/base.py:523` (inside UNFOLD.SIDEBAR.navigation)
- Inside billing: `apps/billing/tasks.py:156,237` (B2B_START/END within billing app — these directories are kept if billing is selected but B2B is not)

### Pitfall 4: billing/tasks.py Has B2B Markers — Directory Not Deleted

**What goes wrong:** `apps/billing/tasks.py` contains `# B2B_START` blocks at lines 156 and 237. `removeB2BModule()` only deletes `orgs/`, `api_keys/`, `webhooks/`, `audit/` — it does NOT delete `billing/`. So `stripMarkerBlocks()` must run on `billing/tasks.py` even though the billing directory is kept.

**Root cause:** The B2B module added org-billing integration code (OrgCustomer entitlement) inside the billing app.

**How to avoid:** The marker stripper runs on ALL Python files in the output directory (not just the B2B app directories). This is the correct behavior — after `removeB2BModule()` deletes the B2B dirs, the stripper scans everything remaining. `billing/tasks.py` will be included in the glob scan.

### Pitfall 5: --with Flag Polarity vs --without Flag

**What goes wrong:** All existing flags are `--without X` (opt-out). B2B is `--with X` (opt-in). The existing code in `index.ts` parses `--without` from `process.argv` and uses the flag to REMOVE features from the prompt result. For `--with b2b`, the logic inverts: B2B is not in `initialValues` (unchecked), so `--with b2b` must ADD it to the feature list rather than filter it out.

**How to avoid:** Parse a separate `withIdx` (looking for `"--with"` not `"--without"`) and add `"b2b"` to features post-prompt rather than filtering.

---

## Code Examples

### Full Marker Inventory (Verified via grep)

Files containing `# B2B_START` / `# B2B_END` markers (as of Phase 30 completion):

```
apps/api/config/settings/base.py       — 8 START, 7 END  ← UNMATCHED (fix required)
apps/api/config/urls.py                — 1 START, 1 END
apps/api/apps/api_keys/admin.py        — 1 START, 1 END  (whole file is B2B block)
apps/api/apps/orgs/admin.py            — 1 START, 1 END  (whole file is B2B block)
apps/api/apps/audit/models.py          — 1 START, 1 END
apps/api/apps/audit/apps.py            — 1 START, 1 END
apps/api/apps/audit/admin.py           — 1 START, 1 END  (whole file is B2B block)
apps/api/apps/audit/middleware.py      — 1 START, 1 END
apps/api/apps/accounts/permissions.py  — 1 START, 1 END
apps/api/apps/webhooks/admin.py        — 1 START, 1 END  (whole file is B2B block)
apps/api/apps/billing/tasks.py         — 2 START, 2 END  (org-billing integration)
```

**Files safe to delete entirely (whole file is B2B marker):**

- `apps/api_keys/admin.py` — deleted with the directory
- `apps/orgs/admin.py` — deleted with the directory
- `apps/audit/admin.py` — deleted with the directory
- `apps/webhooks/admin.py` — deleted with the directory

**Files requiring marker stripping after directory deletion:**

- `apps/api/config/settings/base.py` — multiple B2B blocks survive (dirs deleted, file kept)
- `apps/api/config/urls.py` — hijack URL block
- `apps/api/apps/audit/models.py` — survives: whole `audit/` dir deleted, no stripping needed
- `apps/api/apps/audit/apps.py` — survives: whole `audit/` dir deleted, no stripping needed
- `apps/api/apps/audit/middleware.py` — survives: whole `audit/` dir deleted, no stripping needed
- `apps/api/apps/accounts/permissions.py` — `staff_can_hijack_regular_users` function
- `apps/api/apps/billing/tasks.py` — OrgCustomer entitlement blocks

### pyproject.toml B2B Deps (Verified via grep)

```toml
# Lines 46-48 in apps/api/pyproject.toml:
"django-pghistory>=3.9.2",
"django-unfold>=0.84.0",   # NOT removed — admin theme is unconditional
"django-hijack>=3.7.6",
```

Removal targets: `django-pghistory` and `django-hijack` only.
`django-unfold` stays (not B2B-specific, used for admin theme unconditionally).

### Test Subprocess Pattern (from test_scaffolder_billing_removal.py)

```python
inline_script = (
    f"import {{ removeB2BModule }} from '{CLI_DIST_REMOVE}';\n"
    f"await removeB2BModule('{tmp_path}');\n"
)
result = subprocess.run(
    ["node", "--input-type=module"],
    input=inline_script,
    capture_output=True,
    text=True,
    timeout=60,
    cwd=str(PROJECT_ROOT / "packages/create-foundation-app"),
)
assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
```

---

## State of the Art

| Old Approach                                      | Current Approach                        | Notes                                                   |
| ------------------------------------------------- | --------------------------------------- | ------------------------------------------------------- |
| No B2B opt-in                                     | `--with b2b` flag (Phase 31)            | First opt-in flag; all others are opt-out               |
| Marker-free removal (directories + regex patches) | Hybrid: dir deletion + marker stripping | Billing uses pure regex; B2B adds marker-based approach |

---

## Open Questions

1. **Should `test_scaffold_with_b2b` run `manage.py check` against the live template or a tmp_path copy?**
   - What we know: The billing removal test copies only billing-relevant files to tmp_path. For `test_scaffold_with_b2b`, `manage.py check` needs the full Django project (settings, all apps).
   - What's unclear: Whether a partial copy (all B2B files) is sufficient or if full template copy is required.
   - Recommendation: Copy the full `apps/api/` directory to `tmp_path` for the `manage.py check` test. This is the safest approach and avoids subtle "missing file" Django startup errors.

2. **Does the marker stripper need to handle files that are entirely a B2B block (admin.py files)?**
   - What we know: `apps/api_keys/admin.py`, `apps/orgs/admin.py`, `apps/audit/admin.py`, `apps/webhooks/admin.py` are wholly wrapped in `# B2B_START` / `# B2B_END`. Their containing directories are deleted by `removeB2BModule()`.
   - What's unclear: If the stripper runs after directory deletion, these files won't exist — no problem. If the stripper runs before deletion, stripping would leave an empty file.
   - Recommendation: Run `removeB2BModule()` (directory deletion) first, then stripper. Confirmed by CONTEXT.md: "Both run together: `removeB2BModule()` runs first."

---

## Validation Architecture

### Test Framework

| Property           | Value                                                               |
| ------------------ | ------------------------------------------------------------------- |
| Framework          | pytest (existing in `apps/api/`)                                    |
| Config file        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest.ini_options]` |
| Quick run command  | `cd apps/api && pytest tests/scaffolder/ -x`                        |
| Full suite command | `cd apps/api && pytest`                                             |

### Phase Requirements to Test Map

| Req ID   | Behavior                                                              | Test Type    | Automated Command                                                         | File Exists? |
| -------- | --------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------- | ------------ |
| SCAFF-01 | B2B removal produces clean scaffold (no markers, no orphaned imports) | integration  | `pytest tests/scaffolder/test_b2b_scaffold.py -x`                         | ❌ Wave 0    |
| SCAFF-01 | B2B-included scaffold passes `manage.py check`                        | integration  | `pytest tests/scaffolder/test_b2b_scaffold.py::test_scaffold_with_b2b -x` | ❌ Wave 0    |
| SCAFF-01 | CLI flag `--with b2b` wires correctly through `index.ts`              | manual smoke | `node dist/index.js --with b2b` (interactive)                             | N/A — manual |

### Sampling Rate

- **Per task commit:** `cd apps/api && pytest tests/scaffolder/ -x`
- **Per wave merge:** `cd apps/api && pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/scaffolder/__init__.py` — empty, enables pytest discovery of subdirectory
- [ ] `apps/api/tests/scaffolder/test_b2b_scaffold.py` — covers SCAFF-01

---

## Sources

### Primary (HIGH confidence)

- Direct source code inspection: `packages/create-foundation-app/src/remove.ts` — `removeBillingModule()` pattern verified
- Direct source code inspection: `packages/create-foundation-app/src/index.ts` — flag parsing pattern (lines 44-58) verified
- Direct source code inspection: `packages/create-foundation-app/src/prompts.ts` — `SelectedFeatures` type and `initialValues` pattern verified
- Direct source code inspection: `packages/create-foundation-app/src/transform.ts` — `replaceInFiles()` + globby pattern verified
- Direct source code inspection: `apps/api/tests/test_scaffolder_billing_removal.py` — subprocess test pattern verified
- `grep -n "B2B_START\|B2B_END"` on all API Python files — unmatched marker at base.py:670 confirmed

### Secondary (MEDIUM confidence)

- `grep -n "django-unfold"` in settings/base.py — confirms unfold is not B2B-gated (lines 98-99 outside any marker block)
- `grep` on pyproject.toml lines 46-48 — confirms exact dep names and version constraints for removal regex

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all tools are existing project dependencies; no new installs
- Architecture: HIGH — all patterns are direct copies of working code in the same repository
- Pitfalls: HIGH — unmatched marker confirmed by grep; polarity inversion documented from source

**Research date:** 2026-03-13
**Valid until:** Indefinite (no external dependencies; all evidence is in-repo source code)
