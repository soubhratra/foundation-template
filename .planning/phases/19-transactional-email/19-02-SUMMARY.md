---
phase: 19-transactional-email
plan: "02"
subsystem: api
tags: [django, anymail, resend, email, premailer, notifications]

# Dependency graph
requires:
  - phase: 19-transactional-email
    provides: RED test stubs for all EMAIL requirements (plan 01)
provides:
  - notifications Django app scaffold (NotificationsConfig, empty __init__.py)
  - EMAIL MODULE settings block in base.py with conditional backend auto-switch
  - django-anymail[resend] and premailer installed as project dependencies
  - development.py cleaned of unconditional EMAIL_BACKEND override
  - RESEND_API_KEY and DEFAULT_FROM_EMAIL in .env.example
affects:
  - 19-03 (send_email implementation — depends on notifications app and settings)
  - 19-04 (scaffolder removeEmailModule regex targets EMAIL MODULE sentinel comments)

# Tech tracking
tech-stack:
  added: [django-anymail[resend]>=14.0, premailer>=3.10.0]
  patterns:
    - "EMAIL_BACKEND auto-switch: anymail when RESEND_API_KEY env var set, console backend when absent"
    - "Remove-sentinel comments on INSTALLED_APPS lines: # EMAIL MODULE — remove this line to exclude email"
    - "Module fence comments: # EMAIL MODULE / # END EMAIL MODULE for scaffolder regex targeting"

key-files:
  created:
    - apps/api/apps/notifications/__init__.py
    - apps/api/apps/notifications/apps.py
  modified:
    - apps/api/pyproject.toml
    - apps/api/config/settings/base.py
    - apps/api/config/settings/development.py
    - apps/api/.env.example

key-decisions:
  - "EMAIL_BACKEND auto-switch in base.py: if RESEND_API_KEY (truthy) use Resend, else console — removes dev-only override from development.py"
  - "Remove-sentinel comment pattern on INSTALLED_APPS lines enables scaffolder to strip email module cleanly"
  - "EMAIL MODULE fence uses dash-comment delimiters matching BILLING MODULE pattern — consistent with scaffolder removeEmailModule() regex"

patterns-established:
  - "Pattern 1: Module sentinel comments in INSTALLED_APPS allow scaffolder to strip entire module without touching other entries"
  - "Pattern 2: EMAIL_BACKEND auto-switch in base.py (not development.py) means a single code path handles all environments"
  - "Pattern 3: RESEND_API_KEY empty-string default enables zero-config local dev (console backend, no Resend account needed)"

requirements-completed: [EMAIL-01, EMAIL-04]

# Metrics
duration: 5min
completed: 2026-03-12
---

# Phase 19 Plan 02: Notifications App Scaffold and Email Settings Summary

**django-anymail[resend] wired into Django with conditional EMAIL_BACKEND auto-switch — Resend when RESEND_API_KEY set, console backend otherwise, with notifications app scaffold and scaffolder-compatible sentinel comments**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-12T03:18:00Z
- **Completed:** 2026-03-12T03:23:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `apps.notifications` Django app (NotificationsConfig with BigAutoField, label="notifications")
- Added `django-anymail[resend]>=14.0` and `premailer>=3.10.0` to pyproject.toml, installed in .venv
- Wired EMAIL MODULE settings block in base.py with auto-switch logic and scaffolder-compatible fences
- Removed unconditional `EMAIL_BACKEND` override from development.py — auto-switch now handles all environments
- Added `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` entries to `.env.example`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create notifications app scaffold and install dependencies** - `7009602` (feat)
2. **Task 2: Wire EMAIL MODULE settings block and clean development.py** - `00b40fc` (feat)

## Files Created/Modified

- `apps/api/apps/notifications/__init__.py` - Empty package init for notifications app
- `apps/api/apps/notifications/apps.py` - NotificationsConfig Django app config
- `apps/api/pyproject.toml` - Added django-anymail[resend]>=14.0 and premailer>=3.10.0
- `apps/api/config/settings/base.py` - EMAIL MODULE block + anymail/notifications in INSTALLED_APPS
- `apps/api/config/settings/development.py` - Removed unconditional EMAIL_BACKEND override
- `apps/api/.env.example` - Added RESEND_API_KEY and DEFAULT_FROM_EMAIL entries

## Decisions Made

- EMAIL_BACKEND auto-switch lives in base.py (not development.py) so all environments use one code path — dev with no key gets console backend automatically, prod with key gets Resend
- INSTALLED_APPS entries use `# EMAIL MODULE — remove this line to exclude email` sentinel matching the scaffolder's removeEmailModule() regex (same pattern as BILLING MODULE)
- EMAIL MODULE block delimited with dash-comment fences (`# ----` style) consistent with BILLING MODULE, OBSERVABILITY MODULE for pattern consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `python` command not found in shell (macOS default); used `.venv/bin/python` directly — resolved immediately
- Pre-commit `ruff-format` reformatted trailing whitespace on INSTALLED_APPS comment lines; restaged and committed cleanly on second attempt

## User Setup Required

None - no external service configuration required for this plan. RESEND_API_KEY is optional (empty = console backend in development).

## Next Phase Readiness

- notifications app registered in INSTALLED_APPS, settings wired — ready for Plan 03 (send_email() implementation and Celery task)
- `anymail` and `premailer` installed and importable in .venv
- RED test stubs from Plan 01 will remain red until Plan 03 implements the actual send logic

---

_Phase: 19-transactional-email_
_Completed: 2026-03-12_
