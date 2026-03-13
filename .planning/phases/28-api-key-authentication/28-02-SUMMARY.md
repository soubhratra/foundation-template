---
phase: 28-api-key-authentication
plan: 02
subsystem: auth
tags: [api-keys, django, sha256, security, migration]

# Dependency graph
requires:
  - phase: 28-01
    provides: RED test suite for api_keys (test_models.py, test_checks.py, conftest.py with fixtures)
  - phase: 27-outbound-webhooks
    provides: generate_secret() pattern and AppConfig+checks.py pattern used as reference
provides:
  - APIKey Django model with SHA-256 hash storage and generate_key() static method
  - apps/api_keys/ app registered in INSTALLED_APPS inside B2B_START/B2B_END markers
  - Initial migration creating api_keys_key table with three indexes
  - check_api_key_scopes manage.py check validator
  - API_KEY_PREFIX, API_KEY_RATE_LIMIT, API_KEY_SCOPES settings in base.py
affects: [28-03, 28-04, 29-org-api-keys]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SHA-256 hash-only storage for secrets — raw key never persisted to DB"
    - "secrets.token_hex(32) for 256-bit CSPRNG entropy"
    - "stored_prefix = API_KEY_PREFIX + first 8 chars of random for display identifier"
    - "AppConfig.ready() imports checks module — manage.py check integration pattern"

key-files:
  created:
    - apps/api/apps/api_keys/__init__.py
    - apps/api/apps/api_keys/apps.py
    - apps/api/apps/api_keys/models.py
    - apps/api/apps/api_keys/checks.py
    - apps/api/apps/api_keys/migrations/__init__.py
    - apps/api/apps/api_keys/migrations/0001_initial.py
  modified:
    - apps/api/config/settings/base.py

key-decisions:
  - "checks.py created alongside models.py in Task 1 (not Task 2) — AppConfig.ready() imports checks, which blocked migration generation until checks.py existed"
  - "API_KEY_PREFIX and API_KEY_RATE_LIMIT inline comments shortened to avoid ruff E501 — pragma comment split onto separate lines"

patterns-established:
  - "APIKey.generate_key() returns (raw_key, stored_prefix, key_hash) — same 3-tuple pattern as WebhookEndpoint.generate_secret()"
  - "B2B_START/B2B_END markers wrap both INSTALLED_APPS entry and settings block — consistent with webhooks pattern"

requirements-completed: [AKEY-01]

# Metrics
duration: 10min
completed: 2026-03-13
---

# Phase 28 Plan 02: api_keys App — Model, Migration, Settings, Startup Check Summary

**APIKey model with SHA-256 hash storage, 256-bit entropy generate_key(), and manage.py check validator — data foundation for API key authentication**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-13T12:40:00Z
- **Completed:** 2026-03-13T12:44:21Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- APIKey Django model with all required fields (UUID pk, user FK, prefix, key_hash, scopes, name, is_active, last_used_at, usage_count, created_at)
- generate_key() static method returning (raw_key, stored_prefix, key_hash) with 256-bit entropy via secrets.token_hex(32) and SHA-256 hashing
- Migration 0001_initial creating api_keys_key table with three indexes: key_hash (auth lookup), user+is_active (list keys), prefix (display)
- check_api_key_scopes manage.py validator with W001/W002/W003 warning IDs
- API_KEY_PREFIX, API_KEY_RATE_LIMIT, API_KEY_SCOPES settings added to base.py inside B2B_START/B2B_END markers
- 10/10 tests GREEN (test_models.py: 6, test_checks.py: 4), zero api_keys.\* manage.py check warnings

## Task Commits

Each task was committed atomically:

1. **Task 1: Create apps/api_keys/ app — model, migration, AppConfig** - `1b407b4` (feat)
2. **Task 2: Register app in INSTALLED*APPS and add API_KEY*\* settings** - `d83e44c` (feat)

## Files Created/Modified

- `apps/api/apps/api_keys/__init__.py` — Empty module init
- `apps/api/apps/api_keys/apps.py` — ApiKeysConfig with ready() importing checks
- `apps/api/apps/api_keys/models.py` — APIKey model with generate_key() static method
- `apps/api/apps/api_keys/checks.py` — check_api_key_scopes manage.py check validator
- `apps/api/apps/api_keys/migrations/__init__.py` — Empty migrations package init
- `apps/api/apps/api_keys/migrations/0001_initial.py` — Auto-generated initial migration
- `apps/api/config/settings/base.py` — Added apps.api*keys to INSTALLED_APPS and API_KEY*\* settings block

## Decisions Made

- checks.py had to be created before the migration could be generated — AppConfig.ready() imports checks at Django startup, so manage.py makemigrations would fail with ImportError otherwise. Both files are logically Task 1, and checks.py was included in Task 1's commit.
- Inline comments on API_KEY_PREFIX and API_KEY_RATE_LIMIT were shortened to avoid ruff E501 (>100 chars) when combined with `# pragma: allowlist secret` suffix. Comments moved to preceding lines.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] checks.py created in Task 1 commit (not Task 2)**

- **Found during:** Task 1 (migration generation)
- **Issue:** `uv run python manage.py makemigrations api_keys` failed with `ImportError: cannot import name 'checks' from 'apps.api_keys'` because AppConfig.ready() runs at Django startup
- **Fix:** Created checks.py before running makemigrations — included it in Task 1's commit since it was a prerequisite
- **Files modified:** apps/api/apps/api_keys/checks.py
- **Verification:** Migration generated successfully; tests pass
- **Committed in:** d83e44c (Task 2 commit — file committed when settings task was committed)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Blocking issue resolved without scope creep. checks.py content matches plan exactly.

## Issues Encountered

- ruff E501 on API_KEY_PREFIX and API_KEY_RATE_LIMIT lines — `# pragma: allowlist secret` suffix pushed lines past 100 chars. Resolved by moving comments to preceding lines.
- detect-secrets baseline updated automatically on first commit attempt — required `git add .secrets.baseline` on second attempt.

## Next Phase Readiness

- APIKey model and migration ready for Plan 28-03 (authentication backend + middleware)
- All 10 api_keys model/check tests GREEN
- manage.py check clean of api_keys.\* warnings
- generate_key() confirmed working: `ft_XXXXXXXX ft_XXXXXXXX 64` format verified

---

_Phase: 28-api-key-authentication_
_Completed: 2026-03-13_

## Self-Check: PASSED

- FOUND: apps/api/apps/api_keys/models.py
- FOUND: apps/api/apps/api_keys/checks.py
- FOUND: apps/api/apps/api_keys/migrations/0001_initial.py
- FOUND: apps/api/config/settings/base.py
- FOUND: commit 1b407b4 (Task 1)
- FOUND: commit d83e44c (Task 2)
