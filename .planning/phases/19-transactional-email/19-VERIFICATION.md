---
phase: 19-transactional-email
verified: 2026-03-12T10:59:04Z
status: passed
score: 12/12 must-haves verified
re_verification:
  previous_status: passed
  previous_score: 12/12
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 19: Transactional Email Verification Report

**Phase Goal:** Implement transactional email infrastructure — notifications Django app, send_email() utility, Celery task, four HTML templates, Django settings, and scaffolder --without email support.
**Verified:** 2026-03-12T10:59:04Z
**Status:** PASSED
**Re-verification:** Yes — confirming prior passed status against live codebase

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                       | Status   | Evidence                                                                                                        |
| --- | ------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| 1   | `notifications` Django app is discoverable by INSTALLED_APPS                                | VERIFIED | `apps/api/apps/notifications/apps.py` exports `NotificationsConfig`; `"apps.notifications"` in base.py line 118 |
| 2   | `send_email()` exists with correct signature and queues task via `transaction.on_commit()`  | VERIFIED | `utils.py` lines 22–52; `transaction.on_commit(enqueue)` at line 48; correct kwarg signature confirmed          |
| 3   | If the calling transaction rolls back, no Celery task is enqueued                           | VERIFIED | `transaction.on_commit()` semantics; `test_send_email_on_commit_rollback` — GREEN (9 passed live run)           |
| 4   | `send_email_task` renders template, inlines CSS via premailer, dispatches via EMAIL_BACKEND | VERIFIED | `tasks.py` lines 84–104; `transform(html_body, allow_network=False)` line 90; retry + dead-letter wired         |
| 5   | EMAIL_BACKEND auto-switches: Resend when RESEND_API_KEY set, console otherwise              | VERIFIED | `base.py` lines 419–423 conditional on `RESEND_API_KEY`; `development.py` has no EMAIL_BACKEND override         |
| 6   | All four concrete email templates start with `<!-- SUBJECT: ... -->` sentinel               | VERIFIED | First-line sentinel confirmed in welcome, password_reset, email_verification, invoice_ready templates           |
| 7   | `removeEmailModule()` exported from `remove.ts` and compiled into `dist/remove.js`          | VERIFIED | `src/remove.ts` line 585; `dist/remove.js` line 496 confirmed                                                   |
| 8   | `SelectedFeatures` type includes `"email"` and prompt has email option selected by default  | VERIFIED | `prompts.ts` lines 7–9, 80–85; `"email"` in `initialValues` array                                               |
| 9   | `index.ts` calls `removeEmailModule()` when email not in selected features                  | VERIFIED | `index.ts` lines 20, 129–130; guarded by `if (!config.features.includes("email"))`                              |
| 10  | All 9 notifications + scaffolder tests pass GREEN                                           | VERIFIED | Live run: `9 passed, 1 warning in 2.70s`                                                                        |
| 11  | `manage.py check` passes with no errors                                                     | VERIFIED | 3 warnings only (pre-existing allauth deprecations); grep for "ERROR" returned no output                        |
| 12  | development.py does NOT override EMAIL_BACKEND (auto-switch lives in base.py only)          | VERIFIED | Grep for `EMAIL_BACKEND` in `development.py` returned no matches                                                |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact                                                                              | Expected                                    | Status   | Details                                                                        |
| ------------------------------------------------------------------------------------- | ------------------------------------------- | -------- | ------------------------------------------------------------------------------ | ------------------------- |
| `apps/api/apps/notifications/__init__.py`                                             | package init                                | VERIFIED | exists                                                                         |
| `apps/api/apps/notifications/apps.py`                                                 | NotificationsConfig                         | VERIFIED | `name="apps.notifications"`, `label="notifications"`                           |
| `apps/api/apps/notifications/utils.py`                                                | `send_email()` public interface             | VERIFIED | 53 lines; `transaction.on_commit` + RuntimeError fallback; correct signature   |
| `apps/api/apps/notifications/tasks.py`                                                | `send_email_task` Celery shared_task        | VERIFIED | 139 lines; `@shared_task(bind=True, max_retries=3)`; premailer + observability |
| `apps/api/apps/notifications/templates/email/base.html`                               | base email layout                           | VERIFIED | exists                                                                         |
| `apps/api/apps/notifications/templates/email/welcome.html`                            | welcome email with SUBJECT sentinel         | VERIFIED | `<!-- SUBJECT: Welcome to {{ app_name                                          | default:"the app" }} -->` |
| `apps/api/apps/notifications/templates/email/password_reset.html`                     | password reset with SUBJECT sentinel        | VERIFIED | `<!-- SUBJECT: Reset your password -->`                                        |
| `apps/api/apps/notifications/templates/email/email_verification.html`                 | verification with SUBJECT sentinel          | VERIFIED | `<!-- SUBJECT: Verify your email address -->`                                  |
| `apps/api/apps/notifications/templates/email/invoice_ready.html`                      | invoice with SUBJECT sentinel               | VERIFIED | `<!-- SUBJECT: Your invoice is ready -->`                                      |
| `apps/api/apps/notifications/templates/account/email/password_reset_key_message.html` | allauth override                            | VERIFIED | exists                                                                         |
| `apps/api/apps/notifications/templates/account/email/email_confirmation_message.html` | allauth override                            | VERIFIED | exists                                                                         |
| `apps/api/config/settings/base.py`                                                    | EMAIL MODULE block + INSTALLED_APPS entries | VERIFIED | lines 117–118 INSTALLED_APPS; lines 414–432 EMAIL MODULE block with sentinel   |
| `apps/api/pyproject.toml`                                                             | django-anymail[resend] and premailer deps   | VERIFIED | lines 43–44                                                                    |
| `apps/api/.env.example`                                                               | RESEND_API_KEY and DEFAULT_FROM_EMAIL       | VERIFIED | lines 38–39                                                                    |
| `packages/create-foundation-app/src/remove.ts`                                        | `removeEmailModule()` function              | VERIFIED | line 585; exported; notifications dir deletion + base.py strip + .env cleanup  |
| `packages/create-foundation-app/src/prompts.ts`                                       | email in SelectedFeatures and multiselect   | VERIFIED | lines 7–9, 80–85; default-selected in initialValues                            |
| `packages/create-foundation-app/src/index.ts`                                         | removeEmailModule wired in feature removal  | VERIFIED | lines 20, 129–130                                                              |
| `packages/create-foundation-app/dist/remove.js`                                       | compiled CLI with removeEmailModule         | VERIFIED | line 496                                                                       |

---

### Key Link Verification

| From                  | To                              | Via                                               | Status | Details                                                                               |
| --------------------- | ------------------------------- | ------------------------------------------------- | ------ | ------------------------------------------------------------------------------------- |
| `utils.py`            | `tasks.send_email_task.delay()` | `transaction.on_commit()`                         | WIRED  | `transaction.on_commit(enqueue)` line 48; `enqueue()` calls `send_email_task.delay()` |
| `tasks.py`            | `premailer.transform()`         | direct call with `allow_network=False`            | WIRED  | `transform(html_body, allow_network=False)` line 90                                   |
| `tasks.py`            | `apps.core.observability`       | `get_observability_adapter().capture_exception()` | WIRED  | imported line 21; called line 120 on max retries                                      |
| `base.py`             | `RESEND_API_KEY` env var        | `env()` call with empty-string default            | WIRED  | `RESEND_API_KEY: str = env("RESEND_API_KEY", default="")` line 417                    |
| `base.py`             | `INSTALLED_APPS`                | sentinel-commented entries                        | WIRED  | both `anymail` and `apps.notifications` present with `# EMAIL MODULE` sentinel        |
| `index.ts`            | `removeEmailModule()`           | `if (!config.features.includes("email"))`         | WIRED  | lines 129–130                                                                         |
| `removeEmailModule()` | `apps/api/apps/notifications/`  | directory deletion                                | WIRED  | `join(outputDir, "apps/api/apps/notifications")` confirmed in remove.ts               |
| `removeEmailModule()` | `base.py EMAIL MODULE block`    | sentinel regex strip                              | WIRED  | dash-fenced block regex confirmed in remove.ts                                        |

---

### Requirements Coverage

| Requirement | Source Plans        | Description                                                                                              | Status    | Evidence                                                                                                                   |
| ----------- | ------------------- | -------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------------- |
| EMAIL-01    | 19-01, 19-02, 19-03 | Application can send transactional email with Resend backend, swappable via one Django setting           | SATISFIED | `anymail.backends.resend.EmailBackend` auto-switch in base.py; `send_email()` + `send_email_task` verified; tests GREEN    |
| EMAIL-02    | 19-01, 19-03        | Emails dispatched async via Celery using `transaction.on_commit()` to prevent race conditions            | SATISFIED | `transaction.on_commit(enqueue)` in utils.py line 48; `test_send_email_on_commit_rollback` passes GREEN                    |
| EMAIL-03    | 19-01, 19-03        | HTML email templates rendered server-side with inline CSS via premailer                                  | SATISFIED | `transform(html_body, allow_network=False)` in tasks.py line 90; `test_css_is_inlined` passes; 4 templates + base verified |
| EMAIL-04    | 19-01, 19-02        | Console backend default in development; Resend activates when RESEND_API_KEY set                         | SATISFIED | base.py conditional auto-switch; development.py has no EMAIL_BACKEND override; settings tests GREEN                        |
| EMAIL-05    | 19-01, 19-04        | `create-foundation-app --without email` removes all email module files cleanly; `manage.py check` passes | SATISFIED | `removeEmailModule()` in remove.ts and dist/remove.js; wired in index.ts; scaffolder removal test GREEN                    |

All 5 requirements SATISFIED. No orphaned requirements.

**Note on EMAIL-01 wording in REQUIREMENTS.md:** The requirement description mentions `EmailAdapter ABC` / `ResendAdapter` language, which is pre-discussion wording. The RESEARCH.md locked decision explicitly supersedes this: "No custom ABC layer — anymail IS the adapter layer; no EmailAdapter ABC on top." The implementation correctly follows the resolved design decision. This is not a gap.

---

### Anti-Patterns Found

None. Scan of all phase production artifacts (`utils.py`, `tasks.py`, `apps.py`, `remove.ts`, `prompts.ts`, `index.ts`) found:

- No TODO/FIXME/HACK/PLACEHOLDER comments
- No empty return stubs
- No console.log-only implementations
- No placeholder returns (`return null`, `return {}`, `return []`)

The 3 Django system check issues are pre-existing allauth deprecation warnings (not errors, not introduced by this phase).

---

### Human Verification Required

The following behaviors are correct programmatically but benefit from live validation:

#### 1. End-to-end email delivery via Resend

**Test:** Set `RESEND_API_KEY` to a live key, trigger `send_email()` from a Django shell or view, confirm email arrives in inbox.
**Expected:** Email delivered with correctly inlined CSS styles (no `<style>` blocks), correct subject line extracted from template sentinel.
**Why human:** Requires live Resend API credentials and inbox access; cannot be verified with locmem backend.

#### 2. Allauth template overrides in headless mode

**Test:** Register a new user via the allauth headless API flow, confirm the email verification email uses the custom `email_confirmation_message.html` template (not allauth's plain-text default).
**Expected:** Email uses the branded HTML template.
**Why human:** Requires a live allauth signup flow; headless mode email dispatch path is not exercised by unit tests.

#### 3. `create-foundation-app` interactive prompt shows email option

**Test:** Run `node packages/create-foundation-app/dist/index.js` interactively, confirm "Transactional Email" appears in the multi-select feature list checked by default.
**Expected:** "Transactional Email — Async email via Resend (anymail) with console fallback in dev" appears checked by default.
**Why human:** Interactive CLI prompt cannot be verified programmatically without a TTY.

---

### Summary

Phase 19 achieves its goal. All five EMAIL requirements are satisfied end-to-end. Re-verification against the live codebase confirms the prior passed verdict with no regressions detected.

Core findings:

- The `notifications` Django app is properly configured with `NotificationsConfig`. Both `anymail` and `apps.notifications` are in `INSTALLED_APPS` with sentinel comments enabling clean scaffolder removal.
- `send_email()` correctly defers dispatch to `transaction.on_commit()`. The RuntimeError fallback for test contexts (no DB connection) is present and correct.
- `send_email_task` uses `@shared_task(bind=True, max_retries=3)`, renders templates, inlines CSS with `premailer.transform(allow_network=False)`, extracts subjects from `<!-- SUBJECT: ... -->` sentinels, retries with exponential backoff, and routes to the observability dead-letter on max retries.
- All 4 concrete templates have first-line SUBJECT sentinels. Two allauth override templates exist.
- `base.py` EMAIL_BACKEND auto-switch is clean. `development.py` does NOT override `EMAIL_BACKEND`.
- `removeEmailModule()` is implemented, exported, compiled into dist, and wired into index.ts. The scaffolder removal test passes GREEN.
- 9 tests pass (live run: 2.70s). `manage.py check` produces 0 errors.

---

_Verified: 2026-03-12T10:59:04Z_
_Verifier: Claude (gsd-verifier)_
