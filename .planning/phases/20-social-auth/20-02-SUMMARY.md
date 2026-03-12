---
phase: 20-social-auth
plan: "02"
subsystem: auth
tags: [social-auth, allauth, oauth, google, github, apple, django-settings]

# Dependency graph
requires:
  - phase: 20-01
    provides: RED test stubs for test_social_settings.py and test_social_adapter.py
provides:
  - _configure_social_providers() pure function in base.py for conditional Google/GitHub/Apple registration
  - SOCIAL AUTH MODULE sentinel block in base.py (mirrors EMAIL MODULE pattern)
  - FoundationSocialAccountAdapter in apps/accounts/social_adapter.py blocking relay email auto-connect
affects:
  - 20-03
  - 20-04
  - 20-05

# Tech tracking
tech-stack:
  added: []
  patterns:
    - SOCIAL AUTH MODULE sentinel block (dash-fenced, inline comments) — consistent with BILLING MODULE and EMAIL MODULE scaffolder removal patterns
    - Pure function _configure_social_providers(env_dict) for testable conditional provider registration without settings reload
    - bool(super().can_authenticate_by_email()) wrapping for consistent bool return type across real Django and MagicMock test environments

key-files:
  created:
    - apps/api/apps/accounts/social_adapter.py
  modified:
    - apps/api/config/settings/base.py

key-decisions:
  - "Google and GitHub registration requires both client_id AND secret — not just id alone"
  - "APPLE_PRIVATE_KEY base64 decode has graceful fallback to raw string (covers test PEM values and production base64-encoded keys)"
  - "bool() wrapping of super().can_authenticate_by_email() ensures consistent True/False return type — allauth returns provider app setting value directly which is a MagicMock in unit tests"

patterns-established:
  - "SOCIAL AUTH MODULE: _configure_social_providers(env_dict) pure function pattern — call at module load time, also importable for direct unit tests without Django settings reload"
  - "Adapter can_authenticate_by_email: use bool(super()...) wrapper to normalize allauth's raw settings value return"

requirements-completed: [SOCIAL-01, SOCIAL-02, SOCIAL-04]

# Metrics
duration: 5min
completed: 2026-03-12
---

# Phase 20 Plan 02: Social Auth Settings and Relay Email Adapter Summary

**SOCIAL AUTH MODULE block in base.py with conditional Google/GitHub/Apple provider registration via pure function, plus FoundationSocialAccountAdapter blocking Apple relay email auto-connect**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-12T12:05:28Z
- **Completed:** 2026-03-12T12:10:09Z
- **Tasks:** 2
- **Files modified:** 3 (base.py, social_adapter.py, .secrets.baseline)

## Accomplishments

- Added SOCIAL AUTH MODULE sentinel block to base.py with `_configure_social_providers()` pure function that conditionally registers Google, GitHub, and Apple providers based on environment variables
- Added `socialaccount_login_error` redirect URL to `HEADLESS_FRONTEND_URLS` for allauth social error flow
- Created `FoundationSocialAccountAdapter` that blocks `@privaterelay.appleid.com` addresses from triggering email-based account auto-connect

## Task Commits

Each task was committed atomically:

1. **Task 1: SOCIAL AUTH MODULE settings block in base.py** - `a1c8abb` (feat)
2. **Task 2: FoundationSocialAccountAdapter in social_adapter.py** - `8bcfedd` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `apps/api/config/settings/base.py` - Added socialaccount_login_error to HEADLESS_FRONTEND_URLS and SOCIAL AUTH MODULE block with \_configure_social_providers() pure function, SOCIALACCOUNT_ADAPTER, and related settings
- `apps/api/apps/accounts/social_adapter.py` - New file: FoundationSocialAccountAdapter overriding can_authenticate_by_email to block Apple relay addresses

## Decisions Made

- Google and GitHub registration requires both `client_id` AND `secret` to be set (not just id alone). The plan specified `if google_id:` but the existing test `test_google_provider_absent_when_only_client_id_set` requires the condition to check both.
- `APPLE_PRIVATE_KEY` base64 decode uses a try/except fallback that stores the raw string if decoding fails. This covers both production (base64-encoded PEM) and test (raw PEM string) scenarios.
- `bool(super().can_authenticate_by_email(login, email))` wrapping added to normalize allauth's return value. Allauth returns the raw provider app setting value directly, which is a MagicMock in unit tests using `MagicMock()` for sociallogin. The `bool()` wrapper ensures the test assertion `result is True` passes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Google/GitHub provider registration condition**

- **Found during:** Task 1 (SOCIAL AUTH MODULE settings block)
- **Issue:** Plan specified `if google_id:` but test `test_google_provider_absent_when_only_client_id_set` requires provider to NOT be registered when only client_id is set (missing secret). Single-condition check would fail this test.
- **Fix:** Changed to `if google_id and google_secret:` for Google and `if github_id and github_secret:` for GitHub
- **Files modified:** apps/api/config/settings/base.py
- **Verification:** All 9 test_social_settings.py tests pass
- **Committed in:** a1c8abb (Task 1 commit)

**2. [Rule 1 - Bug] Added graceful base64 decode fallback for APPLE_PRIVATE_KEY**

- **Found during:** Task 1 — test `test_apple_provider_registered_with_credentials` passes a raw PEM string, not base64-encoded
- **Issue:** Plain `_base64.b64decode(apple_pk_b64).decode()` raised UnicodeDecodeError on raw PEM strings
- **Fix:** Wrapped decode in try/except, fallback to raw string value
- **Files modified:** apps/api/config/settings/base.py
- **Verification:** test_apple_provider_registered_with_credentials passes
- **Committed in:** a1c8abb (Task 1 commit)

**3. [Rule 1 - Bug] Wrapped super() return in bool() for consistent adapter return type**

- **Found during:** Task 2 — `test_real_email_can_auto_connect` uses `assert result is True` but allauth returns provider app setting value directly
- **Issue:** With MagicMock sociallogin, `super().can_authenticate_by_email()` returns a MagicMock (truthy but not `True`). `result is True` fails.
- **Fix:** `return bool(super().can_authenticate_by_email(login, email))` — normalizes to Python bool
- **Files modified:** apps/api/apps/accounts/social_adapter.py
- **Verification:** All 4 test_social_adapter.py tests pass including test_real_email_can_auto_connect
- **Committed in:** 8bcfedd (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 × Rule 1 - Bug)
**Impact on plan:** All fixes required for tests to pass GREEN. No scope creep — fixes address mismatches between plan code and pre-written RED tests.

## Issues Encountered

None beyond the auto-fixed deviations above.

## User Setup Required

None - no external service configuration required for this plan. Social provider credentials (GOOGLE_CLIENT_ID, etc.) are optional — providers only activate when credentials are present in environment.

## Next Phase Readiness

- SOCIAL AUTH MODULE settings block is wired and tested — Google/GitHub/Apple providers conditionally registered
- FoundationSocialAccountAdapter is registered via SOCIALACCOUNT_ADAPTER setting
- Ready for plan 20-03 (Apple native token verification endpoint) and 20-04 (Next.js social auth UI)
- SOCIALACCOUNT_ADAPTER setting points to the adapter at `apps.accounts.social_adapter.FoundationSocialAccountAdapter`

---

_Phase: 20-social-auth_
_Completed: 2026-03-12_
