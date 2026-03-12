---
phase: 17-dev-time-security-gates
plan: 03
subsystem: infra
tags: [bandit, pip-audit, django-debug-toolbar, detect-secrets, security, dev-tools]

# Dependency graph
requires:
  - phase: 17-01
    provides: test stubs (RED) for all 8 dev-gate behaviors
  - phase: 17-02
    provides: pre-commit hooks and CI security audit steps configured
provides:
  - bandit>=1.9.4 and pip-audit>=2.10.0 installed as uv dev dependencies
  - django-debug-toolbar>=6.2.0 installed as uv dev dependency
  - .secrets.baseline at repo root (1.5.0 format, 30 files scanned)
  - DDT in INSTALLED_APPS + MIDDLEWARE in development.py only
  - DDT URLs registered inside if settings.DEBUG guard in urls.py
  - All 8 test stubs in test_dev_gates.py turned GREEN
affects: [future phases that add new Python files (bandit scan), any debug/dev tooling]

# Tech tracking
tech-stack:
  added:
    - bandit 1.9.4 (dev dep — HIGH-severity Python security linter)
    - pip-audit 2.10.0 (dev dep — known-CVE dependency scanner)
    - django-debug-toolbar 6.2.0 (dev dep — Django request profiler, dev-only)
  patterns:
    - DDT installed in INSTALLED_APPS only via development.py list spread (not base.py)
    - DDT URL registration inside if settings.DEBUG guard with local import (prevents ImportError in CI)
    - detect-secrets baseline generated once via user Python env; maintained by pre-commit hook thereafter

key-files:
  created:
    - .secrets.baseline (repo root — detect-secrets baseline for all 30 files)
  modified:
    - apps/api/pyproject.toml (added bandit, pip-audit, django-debug-toolbar to dev group)
    - apps/api/uv.lock (updated lockfile with 22 new transitive deps)
    - apps/api/config/settings/development.py (DDT INSTALLED_APPS, MIDDLEWARE, INTERNAL_IPS)
    - apps/api/config/urls.py (debug_toolbar_urls() inside if settings.DEBUG)
    - apps/api/tests/core/test_dev_gates.py (all 8 stubs replaced with real assertions)

key-decisions:
  - "detect-secrets baseline generated with user Python installation (~/Library/Python/3x/bin/detect-secrets scan) — not available via uv run since it is a pre-commit-managed tool, not a uv dev dep"
  - "DDT import placed inside if settings.DEBUG block (from debug_toolbar.toolbar import debug_toolbar_urls) — prevents ImportError in CI which uses development settings but DDT is dev-group only"
  - "INTERNAL_IPS = ['127.0.0.1'] sufficient for local dev without custom SHOW_TOOLBAR_CALLBACK — default DDT callback checks INTERNAL_IPS, no Docker network complications for template use case"
  - "4 pre-existing test failures (billing services + middleware timing) confirmed out-of-scope — exist on base commit before Phase 17-03 changes"

patterns-established:
  - "Dev-only tools pattern: install in [dependency-groups].dev, import inside if settings.DEBUG, never in base.py or production.py"
  - "Test implementation pattern: subprocess.run for CLI tool availability + exit code checks; pathlib.Path for file-level settings isolation checks; Django test client for URL resolution"

requirements-completed: [DEV-01, DEV-02, DEV-03, DEV-06]

# Metrics
duration: 15min
completed: 2026-03-11
---

# Phase 17 Plan 03: Dev-Time Security Gates Implementation Summary

**bandit, pip-audit, django-debug-toolbar installed as dev deps; .secrets.baseline generated; all 8 dev-gate test stubs turned GREEN**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-11T22:30:00Z
- **Completed:** 2026-03-11T22:45:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Installed bandit 1.9.4, pip-audit 2.10.0, django-debug-toolbar 6.2.0 as uv dev dependencies
- Generated `.secrets.baseline` at repo root (30 files scanned, all known-safe dev credentials accepted)
- Configured DDT in `development.py` only using list-spread pattern; registered DDT URLs inside `if settings.DEBUG` guard
- Replaced all 8 `pytest.fail()` RED stubs in `test_dev_gates.py` with real assertions — all 8 pass GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dev deps and generate .secrets.baseline** - `465fa3d` (chore)
2. **Task 2: Configure DDT and turn all tests GREEN** - `2819c78` (feat)

## Files Created/Modified

- `.secrets.baseline` - detect-secrets baseline, repo root, 30 files scanned, version 1.5.0
- `apps/api/pyproject.toml` - bandit, pip-audit, django-debug-toolbar added to dev dependency group
- `apps/api/uv.lock` - updated lockfile (+22 transitive deps)
- `apps/api/config/settings/development.py` - DDT INSTALLED_APPS, MIDDLEWARE, INTERNAL_IPS block
- `apps/api/config/urls.py` - `debug_toolbar_urls()` under `if settings.DEBUG:` guard at end of file
- `apps/api/tests/core/test_dev_gates.py` - 8 real test implementations replacing RED stubs

## Decisions Made

- detect-secrets is managed by pre-commit's isolated virtualenv (not uv). The baseline was generated using `~/Library/Python/3x/bin/detect-secrets scan` — the system Python install where pre-commit stores it. No additional uv dep needed.
- DDT's `debug_toolbar_urls()` import is placed inside the `if settings.DEBUG:` block to prevent `ImportError` in CI environments. DDT is a dev-group dep only — not installed in CI test settings.
- 4 pre-existing test failures (3 billing service tests, 1 middleware timing) confirmed as out-of-scope. Verified by stashing Phase 17-03 changes and re-running — failures exist on the base commit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used system Python detect-secrets instead of uv run**

- **Found during:** Task 1 (generate .secrets.baseline)
- **Issue:** `uv run detect-secrets` fails — detect-secrets is not in uv dev deps; it is managed by pre-commit's isolated env. `pip install detect-secrets` via system pip also failed (pip not in PATH).
- **Fix:** Found `detect-secrets` binary at `~/Library/Python/3x/bin/detect-secrets` (installed when pre-commit set up the Yelp/detect-secrets hook env). Used that binary directly to scan repo root.
- **Files modified:** `.secrets.baseline` (created)
- **Verification:** `python3 -c "import json; json.load(open('.secrets.baseline'))"` exits 0; version: 1.5.0, files scanned: 30
- **Committed in:** 465fa3d (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Blocking issue in baseline generation path; resolved by finding the correct binary location. Outcome is identical — valid `.secrets.baseline` at repo root.

## Issues Encountered

- detect-secrets not available via `uv run` or system `pip`. Located via `~/Library/Python/3x/bin/` — the directory where pre-commit installs hook-managed tools. Used this binary directly.

## Next Phase Readiness

- Phase 17 fully complete — all 4 dev-time security gates operational (detect-secrets, bandit, pip-audit, django-debug-toolbar)
- Full test suite: 111 passed, 8 skipped (4 pre-existing billing/middleware failures are out-of-scope)
- No blockers for subsequent phases

---

_Phase: 17-dev-time-security-gates_
_Completed: 2026-03-11_

## Self-Check: PASSED

- FOUND: .secrets.baseline
- FOUND: apps/api/config/settings/development.py
- FOUND: apps/api/config/urls.py
- FOUND commit: 465fa3d (Task 1)
- FOUND commit: 2819c78 (Task 2)
