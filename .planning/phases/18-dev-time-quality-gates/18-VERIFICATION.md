---
phase: 18-dev-time-quality-gates
verified: 2026-03-11T12:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run git commit with a non-conventional message (e.g. 'wip stuff')"
    expected: "Pre-commit rejects the commit with a 'conventional-pre-commit' error message"
    why_human: "commit-msg hook requires `pre-commit install --hook-type commit-msg` to be run first; cannot verify local hook activation programmatically"
  - test: "Introduce a function with McCabe complexity > 10 and attempt `git commit`"
    expected: "ruff pre-commit hook rejects the commit with a C901 error"
    why_human: "Verifying the full pre-commit + ruff gate chain requires a live working tree with a staged violation; automated test only confirms config is present"
---

# Phase 18: Dev-Time Quality Gates Verification Report

**Phase Goal:** Install dev-time quality gates: N+1 detection (nplusone autouse fixture), conventional commit enforcement (commitlint pre-commit hook), API contract fuzzing (schemathesis CI job), and cyclomatic complexity gate (ruff McCabe). All gates must be wired and verifiable.
**Verified:** 2026-03-11T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                         | Status   | Evidence                                                                                                                                                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | nplusone is installed as a runtime dep and an autouse fixture raises immediately on the first N+1 detected    | VERIFIED | `nplusone>=1.0` in `[project.dependencies]` line 42; `_nplusone_guard` autouse fixture in conftest.py line 119; uses `_LazyLoadProfiler` context manager (raise-immediately mode)                            |
| 2   | `@allow_lazy_load` annotation suppresses NPlusOneError for that test only                                     | VERIFIED | `allow_lazy_load` decorator defined in conftest.py lines 89-109; `nplusone.ext.pytest` synthetic module registered in sys.modules; `test_nplusone_allow_annotation_suppresses_error` passes GREEN            |
| 3   | `conventional-pre-commit` hook is in `.pre-commit-config.yaml` on the `commit-msg` stage                      | VERIFIED | Lines 47-51 of `.pre-commit-config.yaml`; `stages: [commit-msg]` confirmed; rev v3.4.0 pinned                                                                                                                |
| 4   | `[tool.ruff.lint.mccabe]` with `max-complexity = 10` is in `apps/api/pyproject.toml`                          | VERIFIED | Lines 81-82 of pyproject.toml; `select = ["E", "F", "C90"]` in `[tool.ruff.lint]` makes C90 explicit; `uv run ruff check . --select C90` executes and detects violations                                     |
| 5   | Existing ruff CI step picks up C90 automatically — no ci.yml changes needed                                   | VERIFIED | `ci.yml` line 60: `uv run ruff check .` reads pyproject.toml which now includes C90; ruff pre-commit hook uses only `--fix` (no `--select` override), inheriting C90 from config                             |
| 6   | All 6 tests in test_quality_gates.py pass GREEN                                                               | VERIFIED | `uv run pytest tests/core/test_quality_gates.py -v` shows 6 passed, 0 failed, 0 errors                                                                                                                       |
| 7   | A schemathesis CI job exists as a fourth top-level job alongside api, web, and mobile                         | VERIFIED | `python3 -c "import yaml; ..."` confirms jobs: `['api', 'web', 'mobile', 'schemathesis']`                                                                                                                    |
| 8   | The schemathesis job starts manage.py runserver, waits for it, then runs schemathesis run with `--checks all` | VERIFIED | ci.yml lines 209-241: runserver in background, wget poll loop (30 attempts × 2s), `schemathesis run` with `--checks all`, `--exclude-path` flags, `--hypothesis-max-examples 30`, `--max-response-time 5000` |
| 9   | schemathesis is installed as a dev dep in pyproject.toml                                                      | VERIFIED | `schemathesis>=3.39` in `[dependency-groups].dev` (line 58 of pyproject.toml); actual resolved version 4.12.0 in uv.lock                                                                                     |

**Score:** 9/9 truths verified

---

## Required Artifacts

| Artifact                                    | Plan        | Status   | Details                                                                                                                                                                      |
| ------------------------------------------- | ----------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/tests/core/test_quality_gates.py` | 18-01/18-02 | VERIFIED | Exists; substantive (6 real assertions, not stubs); wired to conftest.py via `_nplusone_guard` fixture and to pyproject.toml/pre-commit-config via file-read assertions      |
| `apps/api/conftest.py`                      | 18-02       | VERIFIED | Contains `nplusone` (line 50+); `_nplusone_guard` autouse fixture at line 119; `allow_lazy_load` decorator; synthetic `nplusone.ext.pytest` module registered in sys.modules |
| `apps/api/pyproject.toml`                   | 18-02/18-03 | VERIFIED | `nplusone>=1.0` in runtime deps; `schemathesis>=3.39` in dev group; `[tool.ruff.lint]` with C90; `[tool.ruff.lint.mccabe]` with `max-complexity = 10`                        |
| `.pre-commit-config.yaml`                   | 18-02       | VERIFIED | `conventional-pre-commit` v3.4.0 with `stages: [commit-msg]`; ruff hook uses `--fix` only (inherits C90 from pyproject.toml)                                                 |
| `.github/workflows/ci.yml`                  | 18-03       | VERIFIED | Fourth job `schemathesis` present; postgres service, migrations, runserver background start, wget poll, `schemathesis run --checks all` with three `--exclude-path` flags    |

---

## Key Link Verification

| From                                        | To                                       | Via                                                                              | Status | Details                                                                                                                                                                   |
| ------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/conftest.py`                      | `apps/api/pyproject.toml`                | nplusone imported in conftest — must be installed in runtime deps                | WIRED  | `import nplusone.ext.django.patch` + `from nplusone.core import ...` in conftest; `nplusone>=1.0` in `[project.dependencies]`                                             |
| `.pre-commit-config.yaml`                   | `commit-msg` stage                       | `conventional-pre-commit` hook only runs on commit message                       | WIRED  | `stages: [commit-msg]` confirmed at line 51                                                                                                                               |
| `apps/api/pyproject.toml`                   | `.github/workflows/ci.yml`               | `uv run ruff check .` in ci.yml picks up `[tool.ruff.lint.mccabe]` automatically | WIRED  | `select = ["E", "F", "C90"]` in pyproject.toml; ci.yml line 60 runs `uv run ruff check .` (no `--select` override); ruff detects C901 violations as confirmed by live run |
| `.github/workflows/ci.yml schemathesis job` | `http://localhost:8000/api/openapi.json` | manage.py runserver starts in background; wget polls until ready                 | WIRED  | Lines 209-230 of ci.yml: runserver background, wget loop, final wget guard; `schemathesis run http://127.0.0.1:8000/api/openapi.json` at line 235                         |
| `.github/workflows/ci.yml schemathesis job` | `apps/api/pyproject.toml`                | `uv run schemathesis` — schemathesis must be installed as dev dep                | WIRED  | `uv sync` in CI installs all groups; `schemathesis>=3.39` in dev group                                                                                                    |

---

## Requirements Coverage

| Requirement | Source Plan(s) | Description                                                                                                                                       | Status    | Evidence                                                                                                                                                                                          |
| ----------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEV-04      | 18-01, 18-02   | N+1 query regressions fail the backend test suite via `nplusone` auto-detecting pytest fixture (raises on detected N+1 unless explicitly allowed) | SATISFIED | `_nplusone_guard` autouse fixture in conftest.py; `_LazyLoadProfiler` raises `NPlusOneError` immediately; `@allow_lazy_load` decorator for intentional N+1s; 3 tests GREEN                        |
| DEV-05      | 18-03          | API contract regressions are caught in CI via `schemathesis` property-based fuzzing against the OpenAPI spec on the Django test server            | SATISFIED | `schemathesis` job in ci.yml as fourth top-level job; `--checks all`; webhook/health/auth paths excluded; schemathesis 4.12.0 installed as dev dep                                                |
| DEV-07      | 18-02          | Non-conventional commits are blocked at commit time via `commitlint` pre-commit hook enforcing the Conventional Commits spec                      | SATISFIED | `conventional-pre-commit` v3.4.0 in `.pre-commit-config.yaml` with `stages: [commit-msg]`; 10-type allowlist (feat/fix/docs/refactor/test/chore/perf/ci/build/revert)                             |
| DEV-08      | 18-02          | Code complexity exceeding McCabe max=10 is blocked by ruff in pre-commit + CI                                                                     | SATISFIED | `[tool.ruff.lint.mccabe]` with `max-complexity = 10`; `select = ["E", "F", "C90"]` enables C90 rules; ruff pre-commit hook and CI step both read pyproject.toml; live run confirms gate is active |

All four requirements are marked `[x]` (complete) in `.planning/REQUIREMENTS.md` and the phase mapping table shows all four assigned to Phase 18 with status "Complete". No orphaned requirements found.

---

## Anti-Patterns Found

| File                                             | Line | Pattern                                                                              | Severity | Impact                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------ | ---- | ------------------------------------------------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/test_scaffolder_observability_removal.py` | 38   | C901 McCabe complexity 15 > 10 (`test_remove_observability_cleans_all_touch_points`) | Info     | Pre-existing from Phase 14 (commit b056a06). Logged in `deferred-items.md`. Does not block phase 18 goal — this violation predates the C90 gate and is acknowledged as out of scope. Recommended fix: refactor into smaller test methods or add `# noqa: C901` with documented justification. |

No stub patterns, no TODO/FIXME/PLACEHOLDER markers, no empty return implementations found in phase 18 modified files.

---

## Implementation Deviations Noted

The implementation diverged from the plan in two ways that are substantive but correct:

**1. nplusone 1.0.0 has no pytest plugin.** The plan referenced `nplusone.ext.pytest.allow_lazy_load` and an `nplusone` pytest fixture that do not exist in v1.0.0. The implementation correctly replaced these with a custom `_LazyLoadProfiler` context manager and `allow_lazy_load` decorator in conftest.py, and registered a synthetic `nplusone.ext.pytest` module in sys.modules for import compatibility. The functional contract (raise immediately on N+1, suppress with decorator) is fully satisfied.

**2. `_nplusone_guard` uses `request` not `nplusone` as fixture argument.** The plan specified `def _nplusone_guard(nplusone):` (injecting nplusone's plugin fixture). The implementation uses `def _nplusone_guard(request):` to check for the `_allow_lazy_load` attribute on the test function and conditionally activates `_LazyLoadProfiler`. This is the correct approach given the absence of a native pytest plugin; the behavior is equivalent and all tests pass.

Both deviations were documented in the 18-02 SUMMARY.md under "Decisions Made."

---

## Human Verification Required

### 1. Conventional Commit Hook Local Enforcement

**Test:** In the repo directory, ensure `pre-commit install --hook-type commit-msg` has been run, then attempt: `git commit --allow-empty -m "wip stuff"`
**Expected:** The commit is rejected with a message referencing `conventional-pre-commit` and explaining the commit message does not follow Conventional Commits format.
**Why human:** The commit-msg hook requires the extra `--hook-type commit-msg` installation step. CI verification is pending an actual CI run. Cannot programmatically verify that a developer's local working copy has both `pre-commit install` and `pre-commit install --hook-type commit-msg` configured.

### 2. McCabe Complexity Gate End-to-End

**Test:** Add a function with complexity > 10 (e.g., a function with 11 nested conditions) to any Python file in `apps/api/`, stage it, and attempt `git commit`.
**Expected:** The ruff pre-commit hook rejects the commit with `C901` error identifying the function as too complex.
**Why human:** Confirming the full pre-commit + ruff gate pipeline requires a live staged violation. The automated check confirms `select = ["E", "F", "C90"]` is configured and `uv run ruff check . --select C90` detects violations, but the end-to-end pre-commit hook path needs a human test with a real violation.

---

## Gaps Summary

No gaps. All four requirements (DEV-04, DEV-05, DEV-07, DEV-08) are implemented, wired, and verified by passing tests. All 5 artifacts exist with substantive implementations. All 5 key links are wired. The one anti-pattern found (pre-existing C901 in Phase 14 test code) is documented, out of scope, and does not block phase 18 goal achievement.

Two human verification items are flagged for end-to-end smoke testing of the commit-msg hook and the McCabe pre-commit gate, but these do not constitute gaps — the underlying configurations are confirmed correct in the codebase.

---

_Verified: 2026-03-11T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
