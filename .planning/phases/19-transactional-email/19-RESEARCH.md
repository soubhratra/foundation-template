# Phase 19: Transactional Email - Research

**Researched:** 2026-03-11
**Domain:** Django transactional email — django-anymail (Resend backend), premailer CSS inlining, Celery async dispatch, Django template-based HTML email
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Email library**: django-anymail as the single `EMAIL_BACKEND` — ALL Django email (Allauth + app emails) routes through it
- **ESP**: Resend as default backend (`anymail.backends.resend.EmailBackend`)
- **No custom ABC layer**: anymail IS the adapter layer; no `EmailAdapter` ABC on top
- **Application interface**: `send_email(to: str, template_name: str, context: dict)` in `notifications.utils`
- **Auto-switch logic**: if `RESEND_API_KEY` is set → ResendBackend; if absent → `django.core.mail.backends.console.EmailBackend`
- **Template location**: `apps/api/apps/notifications/templates/email/`
- **Subject extraction**: `{% block subject %}...{% endblock %}` inside each template; `send_email()` extracts before dispatch
- **Ships with four templates**: `welcome.html`, `password_reset.html`, `email_verification.html`, `invoice_ready.html`
- **Celery dispatch via `transaction.on_commit()`**: prevents email dispatch if triggering transaction rolls back
- **premailer for CSS inlining**: CSS inlined before handoff to anymail
- **structlog**: `email_queued` INFO event on enqueue with fields `{to, template_name, subject}`
- **Retry policy**: `autoretry_for=(Exception,)`, `max_retries=3`, `retry_backoff=True` — mirrors billing task exactly
- **Dead-letter**: CRITICAL log + `get_observability_adapter().capture_exception()`
- **ConsoleAdapter**: Django's built-in `django.core.mail.backends.console.EmailBackend` (not a custom class)
- **Scaffolder flag `--without email`**: removes `apps/api/apps/notifications/` + removes `anymail` from `INSTALLED_APPS` + removes deps
- **`manage.py check` must pass after removal**

### Claude's Discretion

- Exact `send_email()` function signature beyond `(to, template_name, context)` — e.g. `from_email`, `reply_to` optional kwargs
- premailer configuration details (CSS stripping, link handling)
- Whether to add plain-text fallback or HTML-only for now
- Internal template rendering implementation (how subject block is extracted)

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope
  </user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                        | Research Support                                                                                          |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| EMAIL-01 | Application can send a transactional email via `send_email()` with Resend as the default backend, swappable via one Django setting | django-anymail 14.0 Resend backend + settings pattern documented below                                    |
| EMAIL-02 | Emails are dispatched asynchronously via Celery tasks using `transaction.on_commit()` to prevent race conditions                   | Celery `shared_task` + `transaction.on_commit()` pattern from billing signals; no new Celery infra needed |
| EMAIL-03 | HTML email templates are rendered server-side with inline CSS (via `premailer`) for email client compatibility                     | `premailer.transform()` wraps the rendered HTML string before Django email construction                   |
| EMAIL-04 | A `ConsoleAdapter` is the default in development (no credentials needed); `ResendAdapter` activates when `RESEND_API_KEY` is set   | Auto-switch via `EMAIL_BACKEND` conditional in `base.py`; development.py already sets console backend     |
| EMAIL-05 | Running `create-foundation-app --without email` removes all email module files cleanly; `manage.py check` passes                   | `removeEmailModule()` in `remove.ts` mirrors `removeBillingModule()` pattern exactly                      |

</phase_requirements>

---

## Summary

Phase 19 builds the `notifications` Django app: a self-contained transactional email module with a single `send_email()` utility backed by django-anymail (Resend ESP). The architecture mirrors existing project patterns precisely — the adapter pattern from observability/billing, Celery retry pattern from billing tasks, and structlog from core observability.

The key integration surface is `EMAIL_BACKEND` in Django settings. django-anymail 14.0 (current stable) supports Resend natively. The `send_email()` function enqueues a Celery task via `transaction.on_commit()`, renders an HTML Django template, inlines CSS with `premailer.transform()`, then hands the prepared `EmailMessage` to anymail. No custom adapter class or ABC is needed — anymail's own `EmailBackend` IS the pluggable layer.

The scaffolder work (`--without email`) follows the same pattern as `removeBillingModule()` in `remove.ts`: delete the directory, strip from `INSTALLED_APPS`, remove the settings block, remove deps from `pyproject.toml`. The prompts and index need `"email"` added to the `SelectedFeatures` union and multi-select options.

**Primary recommendation:** Build as three sequential tasks — (1) notifications app + settings + deps, (2) `send_email()` utility + Celery task + four templates, (3) scaffolder `--without email` flag.

---

## Standard Stack

### Core

| Library        | Version                                         | Purpose                                     | Why Standard                                                                                                            |
| -------------- | ----------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| django-anymail | 14.0 (current stable, Dec 2025)                 | Django `EMAIL_BACKEND` abstraction for ESPs | Supports 14 ESPs including Resend; single setting swap for provider change; handles Allauth + app emails uniformly      |
| premailer      | 3.10.0 (last release Aug 2021, still most-used) | CSS block → inline `style=""` attributes    | Most widely used Python CSS inliner; lxml-based; `transform(html)` one-liner; no actively-maintained alternative exists |
| Resend ESP     | — (cloud API)                                   | Production email delivery                   | Project-level decision; anymail 14.0 has native Resend backend; SendGrid explicitly dropped as out-of-scope             |

### Supporting

| Library                                          | Version | Purpose                         | When to Use                                                                    |
| ------------------------------------------------ | ------- | ------------------------------- | ------------------------------------------------------------------------------ |
| `django.core.mail.backends.console.EmailBackend` | stdlib  | Dev/test email output to stdout | When `RESEND_API_KEY` absent; no install needed                                |
| celery (already installed)                       | 5.6.2+  | Async task dispatch             | Already running; `send_email_task` integrates without new broker/worker config |
| structlog (already installed)                    | 25.5.0+ | Structured log events           | `email_queued` INFO line; already configured in project                        |

### Installation

```bash
# In apps/api/pyproject.toml — add to [project] dependencies:
"django-anymail[resend]>=14.0",
"premailer>=3.10.0",
```

Note: `[resend]` extra is required if using anymail webhooks with Resend signature validation (installs `svix`). For send-only (no webhooks in this phase), plain `django-anymail>=14.0` is sufficient. Recommend `[resend]` for forward-compatibility.

---

## Architecture Patterns

### Recommended Project Structure

```
apps/api/apps/notifications/
├── __init__.py
├── apps.py                         # NotificationsConfig
├── tasks.py                        # send_email_task (Celery shared_task)
├── utils.py                        # send_email() public interface
└── templates/
    └── email/
        ├── base.html               # base layout: logo placeholder, {% block content %}, footer
        ├── welcome.html            # post-signup welcome
        ├── password_reset.html     # Allauth password_reset_key override
        ├── email_verification.html # Allauth email_confirmation override
        └── invoice_ready.html      # billing: invoice PDF ready
```

### Pattern 1: Settings Auto-Switch (EMAIL-04)

**What:** `EMAIL_BACKEND` is set conditionally in `base.py` based on `RESEND_API_KEY` presence.
**When to use:** Applied once in base.py; not repeated per-environment.

```python
# apps/api/config/settings/base.py

# ---------------------------------------------------------------------------
# EMAIL MODULE
# ---------------------------------------------------------------------------
RESEND_API_KEY: str = env("RESEND_API_KEY", default="")

EMAIL_BACKEND = (
    "anymail.backends.resend.EmailBackend"
    if RESEND_API_KEY
    else "django.core.mail.backends.console.EmailBackend"
)

ANYMAIL = {
    "RESEND_API_KEY": RESEND_API_KEY,
}

DEFAULT_FROM_EMAIL: str = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")
# ---------------------------------------------------------------------------
# END EMAIL MODULE
# ---------------------------------------------------------------------------
```

**Critical:** `development.py` currently overrides `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` unconditionally. After this phase, that line in `development.py` should be **removed** — the base.py auto-switch handles it. Development will continue to use console backend (no `RESEND_API_KEY` set). This avoids the override breaking production settings inheritance if the key is set in a staging env that shares development.py.

### Pattern 2: send_email() → on_commit → Celery Task (EMAIL-01, EMAIL-02)

**What:** `send_email()` is the only public interface. It queues a Celery task via `transaction.on_commit()`.
**When to use:** All application code calls `send_email()`. Never call the task directly.

```python
# apps/api/apps/notifications/utils.py
import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)


def send_email(
    to: str,
    template_name: str,
    context: dict,
    *,
    from_email: str | None = None,
    reply_to: str | None = None,
) -> None:
    """Queue a transactional email via Celery after the current transaction commits.

    Email is never sent if the triggering transaction rolls back.
    No-op (console log) in development when RESEND_API_KEY is absent.
    """
    from apps.notifications.tasks import send_email_task

    def enqueue() -> None:
        send_email_task.delay(
            to=to,
            template_name=template_name,
            context=context,
            from_email=from_email,
            reply_to=reply_to,
        )
        logger.info(
            "email_queued",
            to=to,
            template_name=template_name,
        )

    transaction.on_commit(enqueue)
```

### Pattern 3: Celery Task with CSS Inlining (EMAIL-02, EMAIL-03)

**What:** `send_email_task` renders the Django template, extracts subject, inlines CSS with premailer, dispatches.
**When to use:** Only called from `send_email()` via `transaction.on_commit()`.

```python
# apps/api/apps/notifications/tasks.py
import structlog
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from premailer import transform

logger = structlog.get_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def send_email_task(
    self,
    to: str,
    template_name: str,
    context: dict,
    from_email: str | None = None,
    reply_to: str | None = None,
) -> None:
    """Render and dispatch a transactional email.

    Renders the template, extracts subject from {% block subject %},
    inlines CSS with premailer, then dispatches via the configured EMAIL_BACKEND.
    Retries up to 3 times with exponential backoff on any exception.
    """
    import random
    from django.conf import settings
    from apps.core.observability import get_observability_adapter

    try:
        # Render full template (includes subject block)
        html_with_subject = render_to_string(f"email/{template_name}", context)

        # Extract subject from rendered content (implementation detail — see Pitfalls)
        subject, html_body = _extract_subject(html_with_subject)

        # Inline CSS using premailer
        html_inlined = transform(html_body, allow_network=False)

        msg = EmailMessage(
            subject=subject,
            body=html_inlined,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=[to],
            reply_to=[reply_to] if reply_to else None,
        )
        msg.content_subtype = "html"
        msg.send()

    except Exception as exc:
        retries = self.request.retries
        countdown = (2 ** retries) + random.uniform(-1, 1)  # noqa: S311

        if retries >= self.max_retries:
            logger.critical(
                "email_dispatch_failed_max_retries",
                to=to,
                template_name=template_name,
                error=str(exc),
                exc_info=True,
            )
            get_observability_adapter().capture_exception(exc, {
                "task": "send_email_task",
                "to": to,
                "template_name": template_name,
            })
            return

        logger.warning(
            "email_dispatch_retrying",
            to=to,
            template_name=template_name,
            attempt=retries + 1,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=countdown) from exc
```

### Pattern 4: Subject Extraction from Template Block

**What:** Subject is rendered as part of the template, then stripped from the HTML body.
**Approach (Claude's discretion):** Render template twice — once with a `{% block subject %}` context to extract subject text, once for body. Or render once and parse. Recommended approach: use Django's template engine directly with a subject-only render pass.

```python
def _extract_subject(full_html: str) -> tuple[str, str]:
    """Extract subject from <!-- SUBJECT: ... --> sentinel or strip the block.

    Recommended implementation: render the template with a custom context
    that captures the subject block's output, then render again without it.
    Simplest reliable approach:
    - In the template, add a hidden <div id="email-subject">...</div> at the top
    - `_extract_subject` finds that div, extracts text, strips it from html_body

    Alternative: render template twice using Django template context with
    `render_to_string(template, {**context, "_subject_only": True})` and
    template block checking — but this requires template cooperation.

    SIMPLEST: Use BeautifulSoup-free approach with a sentinel comment.
    Template convention: first line is <!-- SUBJECT: {subject text} -->
    Parsed by splitting on newline and stripping the first line.
    """
    ...
```

**Decision for Claude's discretion:** The simplest reliable pattern is a `<!-- SUBJECT: ... -->` HTML comment on the first line of each template's rendered output. This avoids a second render pass and has no library dependency beyond string parsing.

### Pattern 5: Allauth Template Overrides

**What:** Allauth looks for email templates at `account/email/` path. Override by creating templates at that path inside `notifications/templates/`.

```
apps/api/apps/notifications/templates/
├── account/
│   └── email/
│       ├── password_reset_key_message.html   # overrides allauth password reset
│       └── email_confirmation_message.html   # overrides allauth verification
└── email/
    ├── base.html
    ├── welcome.html
    ├── password_reset.html     # our styled version (included above by allauth path)
    ├── email_verification.html
    └── invoice_ready.html
```

**Note:** Allauth's headless mode sends emails via Django's standard `send_mail()` / `EmailMultiAlternatives`. When `anymail.backends.resend.EmailBackend` is `EMAIL_BACKEND`, ALL outgoing email including allauth's goes through Resend automatically. No allauth-specific adapter configuration is needed.

**Allauth template path:** `account/email/password_reset_key_message.html` and `account/email/email_confirmation_message.html`. These templates use allauth's subject/body block conventions — check allauth 65.x source for exact block names if overriding.

### Pattern 6: INSTALLED_APPS Order (EMAIL-01)

`anymail` must appear in `INSTALLED_APPS` BEFORE app-specific apps that use it. Convention: add both `anymail` and `apps.notifications` after `apps.billing`:

```python
INSTALLED_APPS = [
    # ... existing entries ...
    "apps.billing",  # BILLING MODULE — remove this line to exclude billing
    "anymail",       # EMAIL MODULE — remove this line to exclude email
    "apps.notifications",  # EMAIL MODULE — remove this line to exclude email
]
```

### Anti-Patterns to Avoid

- **Calling `send_email()` outside a database transaction context:** `transaction.on_commit()` is a no-op when called outside an atomic block (autocommit mode). Wrap signal handlers or service functions in `transaction.atomic()` if needed. Test for this explicitly.
- **Sending email synchronously inside an HTTP view:** Violates EMAIL-02. Always go through `send_email()`.
- **Using `settings.EMAIL_BACKEND` string check as feature-flag:** Don't `if settings.EMAIL_BACKEND == "..."` in app code. `send_email()` is the single interface.
- **Calling `premailer.transform()` with `allow_network=True` (default):** Will attempt HTTP requests for external stylesheets during task execution. Always pass `allow_network=False`.
- **`EMAIL_BACKEND` override in `development.py` after this phase:** Remove the existing `EMAIL_BACKEND = "...console..."` line from `development.py` — the auto-switch in `base.py` replaces it.

---

## Don't Hand-Roll

| Problem                                 | Don't Build               | Use Instead                                   | Why                                                                                                                             |
| --------------------------------------- | ------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| ESP abstraction (swap Resend → Mailgun) | Custom `EmailAdapter` ABC | django-anymail `EMAIL_BACKEND` setting        | anymail handles 14 ESPs; all existing Django/allauth email flows through one setting; hand-rolled ABC duplicates anymail's work |
| CSS inlining for email clients          | Custom HTML parser        | `premailer.transform()`                       | Email client CSS support is a solved, complex problem; lxml-based, handles cascading and specificity correctly                  |
| Retry/backoff for email delivery        | Custom retry loop         | Celery `autoretry_for` + `retry_backoff=True` | Already battle-tested in billing tasks; exponential backoff with jitter built in                                                |
| Subject extraction from templates       | Template inheritance hack | `<!-- SUBJECT: ... -->` sentinel convention   | Simple, readable, no second render pass, no template engine bypass                                                              |

---

## Common Pitfalls

### Pitfall 1: `transaction.on_commit()` No-Op in Autocommit Mode

**What goes wrong:** `send_email()` is called from code running in autocommit mode (not inside `transaction.atomic()`). Django's `on_commit()` fires immediately when there's no active transaction — this actually works correctly (callback runs after the current "transaction" which is each statement). But the semantics change: there's no rollback protection.
**Why it happens:** Not all service code wraps in `transaction.atomic()`. Signal handlers, management commands, and background tasks often run in autocommit.
**How to avoid:** Document that `send_email()` is safe in both modes. The EMAIL-02 requirement (no email if transaction rolls back) is only relevant when called inside `transaction.atomic()`. Add a note in `utils.py` docstring.
**Warning signs:** Email sent even when the calling view returns an error response after the `send_email()` call.

### Pitfall 2: premailer Fetches External CSS by Default

**What goes wrong:** `premailer.transform(html)` without `allow_network=False` will attempt to fetch any `<link rel="stylesheet" href="https://...">` tags via HTTP during Celery task execution. This is a network call from a task worker, adds latency, and can fail in isolated environments.
**Why it happens:** premailer defaults to `allow_network=True`.
**How to avoid:** Always call `transform(html, allow_network=False)`. Use only inline `<style>` blocks or `style=""` attributes in email templates — no external stylesheet links.
**Warning signs:** Slow email tasks; network errors in Celery logs.

### Pitfall 3: Allauth Template Override Path Mismatch

**What goes wrong:** Allauth email templates not overridden because the file is at the wrong path. Allauth 65.x looks for templates in `account/email/` relative to any template directory. The `notifications` app's `templates/` directory must be discovered by Django's template loader.
**Why it happens:** `APP_DIRS = True` in TEMPLATES settings (which this project uses) automatically scans each app's `templates/` directory. As long as `apps.notifications` is in `INSTALLED_APPS` BEFORE `allauth` or at least before template resolution, the override works.
**How to avoid:** Place allauth overrides at `notifications/templates/account/email/` (matching allauth's lookup path). Verify `APP_DIRS = True` in settings.
**Warning signs:** Allauth still sending plain-text or unbranded emails in development.

### Pitfall 4: `development.py` EMAIL_BACKEND Override Conflict

**What goes wrong:** After this phase adds auto-switch logic to `base.py`, the existing `EMAIL_BACKEND = "...console..."` line in `development.py` always overrides — so setting `RESEND_API_KEY` in a staging environment that inherits from `development.py` would still use the console backend.
**Why it happens:** `development.py` imports `*` from `base.py` then overwrites `EMAIL_BACKEND` unconditionally.
**How to avoid:** Remove `EMAIL_BACKEND` line from `development.py` as part of this phase. The base.py auto-switch is sufficient.

### Pitfall 5: Task Serialization — Context Dict Must Be JSON-Serializable

**What goes wrong:** `send_email_task.delay(context={"user": user_obj})` fails because Django model instances are not JSON-serializable.
**Why it happens:** Celery serializes task arguments as JSON by default.
**How to avoid:** Document in `send_email()` docstring: all `context` dict values must be JSON-serializable primitives. Callers extract `user.email`, `user.name`, etc. before calling `send_email()`.
**Warning signs:** `kombu.exceptions.EncodeError` or `TypeError: Object of type User is not JSON serializable` in Celery logs.

### Pitfall 6: `on_commit` + `ATOMIC_REQUESTS` Interaction

**What goes wrong:** When Django's `ATOMIC_REQUESTS = True` is set (not currently in this project), every HTTP request is wrapped in a transaction. `on_commit` fires after the response is returned — which means the Celery task is enqueued after the HTTP response. This is correct behavior but can surprise developers expecting immediate enqueueing.
**How to avoid:** Not an issue for this project (no `ATOMIC_REQUESTS`). Document as a known consideration in the `send_email()` docstring.

---

## Code Examples

Verified patterns from official sources and existing project code:

### anymail Resend Backend Configuration

```python
# Source: https://anymail.dev/en/stable/esps/resend/ (anymail 14.0 docs)
# apps/api/config/settings/base.py

EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

ANYMAIL = {
    "RESEND_API_KEY": "re_...",  # pragma: allowlist secret
    # Optional for webhook validation only:
    # "RESEND_SIGNING_SECRET": "whsec_...",  # pragma: allowlist secret
}
```

### premailer CSS Inlining

```python
# Source: https://pypi.org/project/premailer/ (premailer 3.10.0)
from premailer import transform

html = """
<html><head>
<style>h1 { color: #333; font-size: 24px; }</style>
</head><body><h1>Hello</h1></body></html>
"""
inlined = transform(html, allow_network=False)
# Result: <h1 style="color: #333; font-size: 24px;">Hello</h1>
```

### Celery Task: Retry Pattern (mirrors billing/tasks.py)

```python
# Source: apps/api/apps/billing/tasks.py (existing project code)
@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def send_email_task(self, ...):
    try:
        # ... dispatch email ...
    except Exception as exc:
        retries = self.request.retries
        countdown = (2 ** retries) + random.uniform(-1, 1)  # noqa: S311
        if retries >= self.max_retries:
            logger.critical("email_dispatch_failed_max_retries", ...)
            get_observability_adapter().capture_exception(exc, {...})
            return
        raise self.retry(exc=exc, countdown=countdown) from exc
```

### transaction.on_commit() Pattern

```python
# Pattern: standard Django pattern for post-commit hooks
# Django docs: https://docs.djangoproject.com/en/5.1/topics/db/transactions/#django.db.transaction.on_commit
from django.db import transaction

def send_email(to, template_name, context, ...):
    def enqueue():
        send_email_task.delay(to=to, template_name=template_name, context=context)
    transaction.on_commit(enqueue)
```

### Scaffolder `--without email` Pattern (mirrors removeBillingModule)

```typescript
// Source: packages/create-foundation-app/src/remove.ts (existing pattern)
export async function removeEmailModule(outputDir: string): Promise<void> {
  // 1. Delete apps/api/apps/notifications/ directory
  // 2. Remove "anymail" from INSTALLED_APPS in base.py
  // 3. Remove "apps.notifications" from INSTALLED_APPS in base.py
  // 4. Remove EMAIL MODULE settings block from base.py
  // 5. Remove django-anymail and premailer deps from pyproject.toml
  // 6. Remove RESEND_API_KEY env var from .env.example
}
```

---

## State of the Art

| Old Approach                    | Current Approach                       | When Changed                                        | Impact                                                                                                                                                      |
| ------------------------------- | -------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SendGrid as default anymail ESP | Resend as default                      | June 2025 (anymail dropped official SendGrid tests) | SendGrid works but is officially "no longer tested" in anymail 14.0; Resend is the recommended replacement                                                  |
| Separate `EmailAdapter` ABC     | django-anymail `EMAIL_BACKEND` setting | This phase design decision                          | anymail provides the abstraction; no custom ABC needed                                                                                                      |
| `django-premailer` template tag | Direct `premailer.transform()` call    | Ongoing preference                                  | `django-premailer` (0.2.0, 2021) adds Django-specific template tag overhead; direct `premailer.transform()` in the Celery task is simpler and more explicit |

**Deprecated/outdated:**

- SendGrid via anymail: "no longer tested" as of anymail 14.0; still functional but use Resend instead
- `inlinestyler`: unmaintained; author recommends premailer

---

## Open Questions

1. **premailer maintenance status**
   - What we know: Last release was August 2021. Still functional, still the only actively-used Python CSS inliner. No security issues. lxml-based.
   - What's unclear: Whether premailer will receive future updates or break with Python 3.13+
   - Recommendation: Use premailer 3.10.0 as decided. Monitor for `cssutils` deprecation warnings (premailer depends on it). If it breaks, `transform()` call is isolated in `send_email_task.py` — easy to swap.

2. **Subject extraction implementation**
   - What we know: Locked decisions say `{% block subject %}` at top of template; `send_email()` extracts before dispatch. Two approaches: (a) `<!-- SUBJECT: ... -->` sentinel comment, (b) render template twice with `_subject_only=True` context flag.
   - What's unclear: Planner must pick one approach.
   - Recommendation: Use `<!-- SUBJECT: ... -->` sentinel as the first rendered line. Template structure: first rendered line is `<!-- SUBJECT: {subject} -->`, remaining HTML is body. `_extract_subject(html)` splits on first `\n` and strips the comment markers. Zero dependencies, no second render pass.

3. **Allauth template override verification**
   - What we know: Allauth 65.x email template paths are `account/email/password_reset_key_message.html` and `account/email/email_confirmation_message.html`.
   - What's unclear: Exact block names in allauth 65.x headless mode email templates for HTML override.
   - Recommendation: At implementation time, inspect allauth 65.x source or official docs for the exact template names and any required context variables.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                        |
| ------------------ | ------------------------------------------------------------ |
| Framework          | pytest + pytest-django (existing)                            |
| Config file        | `apps/api/pyproject.toml` ([tool.pytest.ini_options])        |
| Quick run command  | `cd apps/api && python -m pytest tests/notifications/ -x -q` |
| Full suite command | `cd apps/api && python -m pytest --tb=short -q`              |

### Phase Requirements → Test Map

| Req ID   | Behavior                                                                    | Test Type   | Automated Command                                                                 | File Exists? |
| -------- | --------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------- | ------------ |
| EMAIL-01 | `send_email()` enqueues Celery task; task dispatches via anymail            | unit        | `pytest tests/notifications/test_utils.py::test_send_email_queues_task -x`        | Wave 0       |
| EMAIL-01 | Auto-switch: console backend when no `RESEND_API_KEY`; anymail when key set | unit        | `pytest tests/notifications/test_settings.py::test_email_backend_selection -x`    | Wave 0       |
| EMAIL-02 | `send_email()` does NOT enqueue if transaction rolls back                   | unit        | `pytest tests/notifications/test_utils.py::test_send_email_on_commit_rollback -x` | Wave 0       |
| EMAIL-03 | CSS is inlined in rendered HTML before dispatch                             | unit        | `pytest tests/notifications/test_tasks.py::test_css_is_inlined -x`                | Wave 0       |
| EMAIL-04 | No `RESEND_API_KEY` → console backend; no error raised                      | unit        | `pytest tests/notifications/test_settings.py::test_no_api_key_uses_console -x`    | Wave 0       |
| EMAIL-05 | `removeEmailModule()` leaves clean project; `manage.py check` passes        | integration | `pytest tests/test_scaffolder_email_removal.py -x`                                | Wave 0       |

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/notifications/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest --tb=short -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/notifications/__init__.py` — package init
- [ ] `tests/notifications/test_utils.py` — covers EMAIL-01, EMAIL-02
- [ ] `tests/notifications/test_tasks.py` — covers EMAIL-03
- [ ] `tests/notifications/test_settings.py` — covers EMAIL-01, EMAIL-04
- [ ] `tests/test_scaffolder_email_removal.py` — covers EMAIL-05; mirrors `test_scaffolder_billing_removal.py`

---

## Sources

### Primary (HIGH confidence)

- `anymail.dev/en/stable/esps/resend/` — Resend backend configuration, ANYMAIL settings dict, EMAIL_BACKEND dotted path (anymail 14.0)
- `anymail.dev/en/stable/` — Supported ESPs list, anymail 14.0 current version confirmed
- Existing project code: `apps/api/apps/billing/tasks.py` — Celery retry pattern (verbatim reference)
- Existing project code: `apps/api/apps/core/observability.py` — Adapter pattern (verbatim reference)
- Existing project code: `apps/api/config/settings/base.py` — Settings structure, INSTALLED_APPS, existing EMAIL_BACKEND in development.py
- Existing project code: `packages/create-foundation-app/src/remove.ts` — `removeBillingModule()` pattern (verbatim reference for `removeEmailModule()`)
- Existing project code: `packages/create-foundation-app/src/prompts.ts` — `SelectedFeatures` union type and multi-select structure

### Secondary (MEDIUM confidence)

- `pypi.org/project/premailer/` — Version 3.10.0 confirmed, `transform()` API, `allow_network` option, maintenance status note (last release Aug 2021)
- `pypi.org/project/django-anymail/` — Version 14.0 confirmed (Dec 2025 release)

### Tertiary (LOW confidence)

- WebSearch for premailer alternatives 2025 — confirmed no actively-maintained alternative exists; premailer remains the standard despite sponsorship note

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — anymail 14.0 current stable confirmed; Resend backend confirmed; premailer API confirmed
- Architecture: HIGH — mirrors existing project patterns exactly; no novel patterns introduced
- Pitfalls: HIGH — based on actual code analysis of existing settings and billing/observability patterns
- Scaffolder work: HIGH — remove.ts pattern understood completely; prompts.ts type union pattern known

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (anymail stable; premailer frozen at 3.10.0)
