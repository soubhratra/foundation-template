---
phase: 19-transactional-email
verified: 2026-03-11T00:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 19: Transactional Email Verification Report

**Phase Goal:** Add a complete transactional email system to the Foundation Template: a `notifications` Django app with `send_email()` utility + Celery task + HTML templates, and a `--without email` CLI flag in `create-foundation-app`.
**Verified:** 2026-03-11
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                       | Status   | Evidence                                                                                                                    |
| --- | ------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1   | `notifications` Django app is discoverable by INSTALLED_APPS                                | VERIFIED | `apps/api/apps/notifications/apps.py` with `NotificationsConfig`; `"apps.notifications"` in base.py INSTALLED_APPS line 118 |
| 2   | `send_email()` exists with correct signature and queues task via `transaction.on_commit()`  | VERIFIED | `utils.py` line 22–52; `transaction.on_commit(enqueue)` at line 48                                                          |
| 3   | If the calling transaction rolls back, no Celery task is enqueued                           | VERIFIED | `transaction.on_commit()` semantics + test `test_send_email_on_commit_rollback` passes GREEN                                |
| 4   | `send_email_task` renders template, inlines CSS via premailer, dispatches via EMAIL_BACKEND | VERIFIED | `tasks.py` lines 84–104; `transform(html_body, allow_network=False)` at line 90                                             |
| 5   | EMAIL_BACKEND auto-switches: Resend when RESEND_API_KEY set, console otherwise              | VERIFIED | `base.py` lines 419–425; conditional expression with `RESEND_API_KEY` env var                                               |
| 6   | `development.py` no longer unconditionally overrides EMAIL_BACKEND                          | VERIFIED | No `EMAIL_BACKEND` found in `development.py`                                                                                |
| 7   | All four concrete email templates start with `<!-- SUBJECT: ... -->` sentinel               | VERIFIED | `welcome.html`, `password_reset.html`, `email_verification.html`, `invoice_ready.html` first line confirmed                 |
| 8   | `removeEmailModule()` exported from `remove.ts` and compiled into `dist/remove.js`          | VERIFIED | `src/remove.ts` line 585 exports `removeEmailModule`; `dist/remove.js` line 496 confirms compiled                           |
| 9   | `SelectedFeatures` type includes `"email"` and prompt has email option selected by default  | VERIFIED | `prompts.ts` lines 8, 80, 85                                                                                                |
| 10  | `index.ts` calls `removeEmailModule()` when email not in selected features                  | VERIFIED | `index.ts` lines 20, 129–130                                                                                                |
| 11  | All 9 notification + scaffolder tests pass GREEN                                            | VERIFIED | `pytest tests/notifications/ tests/test_scaffolder_email_removal.py` → `9 passed, 1 warning in 2.59s`                       |
| 12  | `manage.py check` passes with no errors                                                     | VERIFIED | 3 warnings only (pre-existing allauth deprecations out of scope); no ERRORS                                                 |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact                                                                              | Expected                                    | Status   | Details                                                                                                                             |
| ------------------------------------------------------------------------------------- | ------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/notifications/__init__.py`                                             | package init                                | VERIFIED | exists                                                                                                                              |
| `apps/api/apps/notifications/apps.py`                                                 | NotificationsConfig                         | VERIFIED | `name="apps.notifications"`, `label="notifications"`                                                                                |
| `apps/api/apps/notifications/utils.py`                                                | `send_email()` public interface             | VERIFIED | 53 lines; exports `send_email`; `transaction.on_commit` + RuntimeError fallback                                                     |
| `apps/api/apps/notifications/tasks.py`                                                | `send_email_task` Celery shared_task        | VERIFIED | 139 lines; `@shared_task(bind=True, max_retries=3)`; premailer CSS inlining; observability dead-letter                              |
| `apps/api/apps/notifications/templates/email/base.html`                               | base email layout                           | VERIFIED | exists                                                                                                                              |
| `apps/api/apps/notifications/templates/email/welcome.html`                            | welcome email with SUBJECT                  | VERIFIED | first line `<!-- SUBJECT: Welcome to ... -->`                                                                                       |
| `apps/api/apps/notifications/templates/email/password_reset.html`                     | password reset with SUBJECT                 | VERIFIED | first line `<!-- SUBJECT: Reset your password -->`                                                                                  |
| `apps/api/apps/notifications/templates/email/email_verification.html`                 | verification with SUBJECT                   | VERIFIED | first line `<!-- SUBJECT: Verify your email address -->`                                                                            |
| `apps/api/apps/notifications/templates/email/invoice_ready.html`                      | invoice with SUBJECT                        | VERIFIED | first line `<!-- SUBJECT: Your invoice is ready -->`                                                                                |
| `apps/api/apps/notifications/templates/account/email/password_reset_key_message.html` | allauth override                            | VERIFIED | exists                                                                                                                              |
| `apps/api/apps/notifications/templates/account/email/email_confirmation_message.html` | allauth override                            | VERIFIED | exists                                                                                                                              |
| `apps/api/config/settings/base.py`                                                    | EMAIL MODULE block + INSTALLED_APPS entries | VERIFIED | lines 117–118 (INSTALLED_APPS); lines 415–431 (EMAIL MODULE block)                                                                  |
| `apps/api/pyproject.toml`                                                             | django-anymail[resend] and premailer deps   | VERIFIED | lines 43–44                                                                                                                         |
| `apps/api/.env.example`                                                               | RESEND_API_KEY and DEFAULT_FROM_EMAIL       | VERIFIED | lines 38–39                                                                                                                         |
| `packages/create-foundation-app/src/remove.ts`                                        | `removeEmailModule()` function              | VERIFIED | line 585; exported; includes notifications dir deletion, INSTALLED_APPS stripping, EMAIL MODULE block removal, .env.example cleanup |
| `packages/create-foundation-app/src/prompts.ts`                                       | email in SelectedFeatures and multiselect   | VERIFIED | lines 8, 80, 82, 85                                                                                                                 |
| `packages/create-foundation-app/src/index.ts`                                         | removeEmailModule wired in feature removal  | VERIFIED | lines 20, 129–130                                                                                                                   |
| `packages/create-foundation-app/dist/remove.js`                                       | compiled CLI with removeEmailModule         | VERIFIED | line 496                                                                                                                            |

---

### Key Link Verification

| From                  | To                              | Via                                                         | Status | Details                                                                                  |
| --------------------- | ------------------------------- | ----------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `utils.py`            | `tasks.send_email_task.delay()` | `transaction.on_commit()`                                   | WIRED  | `transaction.on_commit(enqueue)` at line 48; `enqueue()` calls `send_email_task.delay()` |
| `tasks.py`            | `premailer.transform()`         | direct call with `allow_network=False`                      | WIRED  | `transform(html_body, allow_network=False)` at line 90                                   |
| `tasks.py`            | `apps.core.observability`       | `get_observability_adapter().capture_exception()`           | WIRED  | imported at line 21; called at line 120 on max retries                                   |
| `base.py`             | `RESEND_API_KEY` env var        | `env()` call with empty-string default                      | WIRED  | `RESEND_API_KEY: str = env("RESEND_API_KEY", default="")` at line 417                    |
| `base.py`             | `INSTALLED_APPS`                | anymail + apps.notifications entries with sentinel comments | WIRED  | both entries present with `# EMAIL MODULE — remove this line to exclude email` sentinel  |
| `index.ts`            | `removeEmailModule()`           | `if (!config.features.includes("email"))`                   | WIRED  | lines 129–130                                                                            |
| `removeEmailModule()` | `apps/api/apps/notifications/`  | directory deletion                                          | WIRED  | `join(outputDir, "apps/api/apps/notifications")` in remove.ts                            |
| `removeEmailModule()` | `base.py EMAIL MODULE block`    | sentinel regex strip                                        | WIRED  | regex `# EMAIL MODULE / # END EMAIL MODULE` dash-fenced block removal                    |

---

### Requirements Coverage

| Requirement | Source Plan         | Description                                                                                    | Status    | Evidence                                                                                                                                    |
| ----------- | ------------------- | ---------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| EMAIL-01    | 19-01, 19-02, 19-03 | Application can send transactional email with Resend backend, swappable via one Django setting | SATISFIED | `anymail.backends.resend.EmailBackend` in base.py auto-switch; `send_email()` + `send_email_task` implementation; tests GREEN               |
| EMAIL-02    | 19-01, 19-03        | Emails dispatched async via Celery using `transaction.on_commit()` to prevent race conditions  | SATISFIED | `transaction.on_commit(enqueue)` in utils.py; `test_send_email_on_commit_rollback` passes                                                   |
| EMAIL-03    | 19-01, 19-03        | HTML email templates rendered server-side with inline CSS via premailer                        | SATISFIED | `transform(html_body, allow_network=False)` in tasks.py; `test_css_is_inlined` passes; 4 concrete templates + base exist                    |
| EMAIL-04    | 19-01, 19-02        | Console backend default in development; Resend activates when RESEND_API_KEY set               | SATISFIED | base.py auto-switch conditional; `test_email_backend_selection` and `test_no_api_key_uses_console` pass; development.py no longer overrides |
| EMAIL-05    | 19-01, 19-04        | `create-foundation-app --without email` removes all email module files cleanly                 | SATISFIED | `removeEmailModule()` in remove.ts and dist/remove.js; wired in index.ts; `test_scaffolder_email_removal.py` passes GREEN                   |

All 5 requirements SATISFIED. No orphaned requirements.

---

### Commits Verified

All 9 commits documented in SUMMARYs confirmed present in git history:

| Commit    | Plan  | Description                                                 |
| --------- | ----- | ----------------------------------------------------------- |
| `b23435f` | 19-01 | test: RED stubs EMAIL-01/02/03                              |
| `5dad8b3` | 19-01 | test: RED stubs EMAIL-01/04/05                              |
| `7009602` | 19-02 | feat: notifications app scaffold and email deps             |
| `00b40fc` | 19-02 | feat: EMAIL MODULE settings block and dev cleanup           |
| `c4a7582` | 19-03 | feat: send_email() utility and send_email_task              |
| `a232086` | 19-03 | feat: HTML email templates and allauth overrides            |
| `35f430b` | 19-04 | test: failing tests for removeEmailModule() (RED)           |
| `6ae7c46` | 19-04 | feat: implement removeEmailModule() in remove.ts            |
| `c049a03` | 19-04 | feat: wire removeEmailModule() into prompts.ts and index.ts |

---

### Anti-Patterns Found

None. Scan of all phase artifacts (`utils.py`, `tasks.py`, `apps.py`, `remove.ts`, `prompts.ts`, `index.ts`) found:

- No TODO/FIXME/HACK/PLACEHOLDER comments
- No empty return stubs (`return null`, `return {}`, `return []`)
- No console.log-only implementations

The 3 Django system check issues are pre-existing allauth deprecation warnings (not errors, not introduced by this phase).

---

### Human Verification Required

The following behaviors are correct programmatically but benefit from live validation in a staging environment:

#### 1. End-to-end email delivery via Resend

**Test:** Set `RESEND_API_KEY` to a live key, trigger `send_email()` from a Django shell or view, confirm email arrives in inbox.
**Expected:** Email delivered with correctly inlined CSS styles (no `<style>` blocks), correct subject line extracted from template sentinel.
**Why human:** Requires live Resend API credentials and inbox access; can't be verified with locmem backend.

#### 2. Allauth template overrides in headless mode

**Test:** Register a new user via the allauth headless API flow, confirm the email verification email uses the custom `email_confirmation_message.html` template (not allauth's default).
**Expected:** Email uses the branded HTML template, not allauth's plain-text default.
**Why human:** Requires a live allauth signup flow; headless mode email dispatch path is not exercised by the unit tests.

#### 3. `create-foundation-app` interactive prompt shows email option

**Test:** Run `node packages/create-foundation-app/dist/index.js` interactively, confirm "Transactional Email" appears in the multi-select feature list with correct hint text and pre-selected.
**Expected:** "Transactional Email — Async email via Resend (anymail) with console fallback in dev" appears checked by default.
**Why human:** Interactive CLI prompt cannot be verified programmatically without a TTY.

---

### Summary

Phase 19 achieved its goal. All five EMAIL requirements are satisfied end-to-end:

- The `notifications` Django app is a properly installed Django app with `NotificationsConfig`.
- `send_email()` correctly defers dispatch to `transaction.on_commit()` — rollback safety is real (tested and passing).
- `send_email_task` performs CSS inlining via premailer, extracts subjects from template sentinels, retries with exponential backoff, and routes to the observability dead-letter on max retries.
- All 4 concrete email templates are self-contained HTML with first-line SUBJECT sentinels; 2 allauth override templates exist.
- The EMAIL_BACKEND auto-switch in `base.py` is clean — console backend in dev with no key, Resend in production.
- `removeEmailModule()` is implemented, exported, compiled, and wired into the scaffolder prompt and removal pipeline.
- 9 tests pass across the full notifications + scaffolder test suites.
- No errors from `manage.py check` (3 pre-existing allauth deprecation warnings are out of scope).

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
