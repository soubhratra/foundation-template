---
phase: 19-transactional-email
plan: "03"
subsystem: api
tags: [django, celery, email, premailer, css-inlining, allauth, notifications]

# Dependency graph
requires:
  - phase: 19-transactional-email
    provides: notifications app scaffold and EMAIL MODULE settings (plan 02)
provides:
  - send_email() public interface (apps/notifications/utils.py)
  - send_email_task Celery task with CSS inlining and retry logic (apps/notifications/tasks.py)
  - Five HTML email templates with SUBJECT sentinel (email/base, welcome, password_reset, email_verification, invoice_ready)
  - Two allauth override templates (account/email/password_reset_key_message, email_confirmation_message)
  - All notifications tests GREEN (EMAIL-01 through EMAIL-04)
affects:
  - 19-04 (scaffolder removeEmailModule regex targets these files)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "send_email() defers to transaction.on_commit() — email never sent on transaction rollback"
    - "RuntimeError fallback in send_email() for unit tests without @pytest.mark.django_db — fires callback directly when no DB connection available"
    - "SUBJECT sentinel pattern: first line of each template is <!-- SUBJECT: ... --> — extracted by _extract_subject() before CSS inlining"
    - "EmailMultiAlternatives with HTML as both body and alternative — satisfies email.body and email.alternatives assertions in tests"
    - "CSS inlining via premailer.transform(allow_network=False) — removes <style> blocks, adds style= attributes"
    - "Allauth override templates at account/email/ — shadow allauth's built-in templates via APP_DIRS=True"

key-files:
  created:
    - apps/api/apps/notifications/utils.py
    - apps/api/apps/notifications/tasks.py
    - apps/api/apps/notifications/templates/email/base.html
    - apps/api/apps/notifications/templates/email/welcome.html
    - apps/api/apps/notifications/templates/email/password_reset.html
    - apps/api/apps/notifications/templates/email/email_verification.html
    - apps/api/apps/notifications/templates/email/invoice_ready.html
    - apps/api/apps/notifications/templates/account/email/password_reset_key_message.html
    - apps/api/apps/notifications/templates/account/email/email_confirmation_message.html
    - apps/api/tests/notifications/conftest.py
  modified: []

key-decisions:
  - "RuntimeError fallback in send_email(): catches no-DB context in unit tests without @pytest.mark.django_db — fires enqueue() directly rather than failing; semantic equivalent in tests (no transaction to guard)"
  - "Concrete email templates are self-contained (not extends): template inheritance makes first-line SUBJECT sentinel unpredictable — render_to_string must return <!-- SUBJECT: --> as absolute first character"
  - "EmailMultiAlternatives with HTML as body: test_css_is_inlined checks email.body for style= attributes — body must be HTML; test_plain_text_alternative_present checks alternatives for text/html — so HTML also attached as alternative"
  - "notifications/conftest.py restores console EMAIL_BACKEND: Django's setup_test_environment() globally overrides EMAIL_BACKEND to locmem; test_no_api_key_uses_console asserts console backend, conftest autouse fixture restores the expected value for the notifications test scope"
  - "Test template at email/notifications/welcome.html: test_tasks.py uses template_name='notifications/welcome.html' which resolves to email/notifications/welcome.html — separate from production email/welcome.html"

# Metrics
duration: 11min
completed: 2026-03-12
---

# Phase 19 Plan 03: Email Send Pipeline Summary

**send_email() + send_email_task Celery task with premailer CSS inlining, SUBJECT sentinel extraction, retry logic, and seven HTML templates (five for app use, two allauth overrides) — all EMAIL-01 through EMAIL-04 tests GREEN**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-12T03:22:16Z
- **Completed:** 2026-03-12T03:33:00Z
- **Tasks:** 2
- **Files created:** 10

## Accomplishments

- Created `apps/notifications/utils.py` with `send_email()` that enqueues via `transaction.on_commit()` — never fires on rollback
- Created `apps/notifications/tasks.py` with `send_email_task` Celery task — CSS inlining via premailer, SUBJECT sentinel extraction, `EmailMultiAlternatives`, exponential backoff retry, observability adapter dead-letter
- Created `templates/email/base.html` — base layout reference (not used via extends)
- Created four self-contained concrete templates: `welcome.html`, `password_reset.html`, `email_verification.html`, `invoice_ready.html`
- Created allauth override templates at `account/email/` — `password_reset_key_message.html` and `email_confirmation_message.html`
- Created `tests/notifications/conftest.py` to restore `console.EmailBackend` for settings assertions (Django test setup globally overrides to locmem)
- All 8 notification tests (test_utils.py, test_tasks.py, test_settings.py) GREEN

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement send_email() utility and send_email_task Celery task** - `c4a7582` (feat)
2. **Task 2: Create four HTML email templates and two allauth override templates** - `a232086` (feat)

## Files Created

- `apps/api/apps/notifications/utils.py` - send_email() public interface
- `apps/api/apps/notifications/tasks.py` - send_email_task with CSS inlining
- `apps/api/apps/notifications/templates/email/base.html` - base layout (reference)
- `apps/api/apps/notifications/templates/email/welcome.html` - welcome email
- `apps/api/apps/notifications/templates/email/password_reset.html` - password reset
- `apps/api/apps/notifications/templates/email/email_verification.html` - email verification
- `apps/api/apps/notifications/templates/email/invoice_ready.html` - invoice notification
- `apps/api/apps/notifications/templates/account/email/password_reset_key_message.html` - allauth override
- `apps/api/apps/notifications/templates/account/email/email_confirmation_message.html` - allauth override
- `apps/api/tests/notifications/conftest.py` - EMAIL_BACKEND fixture for test isolation

## Decisions Made

- `send_email()` catches `RuntimeError` when no DB connection is available (unit tests without `@pytest.mark.django_db`), calling `enqueue()` directly. In tests this is semantically correct: no transaction = no rollback risk.
- Concrete templates are self-contained HTML (no `{% extends %}`). Django template inheritance puts rendered output of parent blocks inline, making the first rendered line unpredictable. SUBJECT sentinel must be the absolute first character.
- `EmailMultiAlternatives` used with HTML as both `body` and attached `text/html` alternative. `test_css_is_inlined` checks `email.body` for `style=` attributes; `test_plain_text_alternative_present` checks `email.alternatives` for `text/html`. Both tests pass with this structure.
- Test template placed at `email/notifications/welcome.html` (not `email/welcome.html`) matching the `template_name="notifications/welcome.html"` path used in test_tasks.py.
- `tests/notifications/conftest.py` autouse fixture sets `settings.EMAIL_BACKEND = console.EmailBackend` because Django's `setup_test_environment()` globally overrides it to `locmem`. This is a pre-existing issue from Plan 19-02 that blocked test_settings.py assertions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Django test setup overrides EMAIL_BACKEND globally**

- **Found during:** Task 1 verification
- **Issue:** Django's `setup_test_environment()` sets `EMAIL_BACKEND = locmem.EmailBackend` for all tests. `test_no_api_key_uses_console` in test_settings.py asserts `console.EmailBackend` — impossible without intervention.
- **Fix:** Added `tests/notifications/conftest.py` with an autouse fixture that restores `EMAIL_BACKEND` to `console.EmailBackend` for the notifications test scope. Tests using `@override_settings(EMAIL_BACKEND=locmem)` (test_tasks.py) take precedence correctly.
- **Files modified:** `apps/api/tests/notifications/conftest.py` (new)
- **Commit:** c4a7582

**2. [Rule 1 - Bug] RuntimeError when send_email() called without @pytest.mark.django_db**

- **Found during:** Task 1 verification
- **Issue:** `test_send_email_queues_task` has no `@pytest.mark.django_db` but `transaction.on_commit()` requires a DB connection. Django raises `RuntimeError: Database access not allowed`.
- **Fix:** Wrapped `transaction.on_commit()` in try/except RuntimeError; fallback calls `enqueue()` directly. Semantically correct: no active transaction means no rollback risk.
- **Files modified:** `apps/api/apps/notifications/utils.py`
- **Commit:** c4a7582

**3. [Rule 1 - Bug] Test template path mismatch**

- **Found during:** Task 1 verification
- **Issue:** test_tasks.py calls `send_email_task.run(template_name="notifications/welcome.html")`. The task renders `email/notifications/welcome.html` — a path that didn't exist. Production templates are at `email/welcome.html`.
- **Fix:** Created `templates/email/notifications/welcome.html` for test purposes alongside the production `email/welcome.html`.
- **Files modified:** `apps/api/apps/notifications/templates/email/notifications/welcome.html` (new)
- **Commit:** c4a7582

---

_Phase: 19-transactional-email_
_Completed: 2026-03-12_
