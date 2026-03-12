# Phase 19: Transactional Email - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a `notifications` Django app that provides async transactional email via django-anymail (Resend backend). Includes: `send_email()` utility, HTML templates with inline CSS via `premailer`, auto-switching between Resend and Django console based on `RESEND_API_KEY`, and a `--without email` scaffolder flag that removes the notifications app cleanly.

Creating, sending, or tracking marketing/newsletter emails is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Allauth email routing

- django-anymail acts as the single `EMAIL_BACKEND` — ALL Django email routes through it (Allauth verification, password reset, magic link, and custom app emails)
- No split backend config; one setting controls all outgoing email
- Auto-switch based on env var: if `RESEND_API_KEY` is set → `anymail.backends.resend.EmailBackend`; if absent → `django.core.mail.backends.console.EmailBackend`
- No custom `EmailAdapter` ABC layer on top of anymail — anymail IS the adapter layer
- Application interface: `send_email(to: str, template_name: str, context: dict)` single function in `notifications.utils` (analogous to `get_observability_adapter()` pattern)

### Template structure

- Templates live at: `apps/api/apps/notifications/templates/email/`
- Base template (`base.html`): minimal — app name/logo placeholder at top, `{% block content %}` in middle, unsubscribe/legal footer at bottom; no opinionated colors or branding
- Subject defined inside each template: `{% block subject %}...{% endblock %}` at top of file; `send_email()` extracts it before dispatch (renders template twice or strips block separately)
- Ships with four example templates:
  - `welcome.html` — post-signup welcome
  - `password_reset.html` — Allauth password reset override
  - `email_verification.html` — Allauth email verification override
  - `invoice_ready.html` — billing module: invoice PDF ready notification

### Celery task dispatch

- `send_email()` queues a Celery task via `transaction.on_commit()` — email never sent if the triggering transaction rolls back (EMAIL-02)
- premailer inlines CSS before handing off to anymail (EMAIL-03)
- structlog emits `email_queued` INFO event on task enqueue: fields = `{to, template_name, subject}`

### Failure & retry policy

- Retry: `autoretry_for=(Exception,)`, `max_retries=3`, `retry_backoff=True` (exponential: 2^attempt seconds) — mirrors billing task pattern exactly
- No special handling for HTTP 429 — exponential backoff naturally covers it
- After max retries exhausted: log at CRITICAL level + call `get_observability_adapter().capture_exception()` — visible in PostHog error tracking; no silent drops

### ConsoleAdapter behavior

- `ConsoleAdapter` = Django's built-in `django.core.mail.backends.console.EmailBackend` (not a custom class)
- Outputs full rendered MIME message to stdout — developer sees exactly what will be sent in production
- structlog INFO line also emitted on dispatch regardless of backend (`email_queued`)

### Scaffolder flag

- `--without email`: removes `apps/api/apps/notifications/` directory entirely + removes `anymail` from `INSTALLED_APPS` and requirements
- `EMAIL_BACKEND` defaults to Django's console backend when notifications app is absent — Allauth emails still work via Django default
- `manage.py check` must pass clean after removal (EMAIL-05)

### Claude's Discretion

- Exact `send_email()` function signature beyond `(to, template_name, context)` — e.g. `from_email`, `reply_to` optional kwargs
- premailer configuration details (CSS stripping, link handling)
- Whether to add `--text-body` plain-text fallback or HTML-only for now
- Internal template rendering implementation (how subject block is extracted)

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/billing/adapters.py` (`PaymentAdapter` ABC): structural blueprint for adapter pattern — not reused directly but informs EmailAdapter design
- `apps/core/observability.py` (`ObservabilityAdapter`, `get_observability_adapter()`): exact pattern for `get_email_adapter()` / adapter factory utility
- `apps/billing/tasks.py` (`process_stripe_event`): `autoretry_for`, `max_retries=3`, `retry_backoff`, dead-letter CRITICAL log — copy this retry pattern verbatim
- Celery infrastructure: `shared_task`, Redis broker, `django_celery_results` — already running, notifications tasks integrate without new config

### Established Patterns

- Adapter pattern: ABC with one concrete implementation, `get_adapter()` factory reading from Django settings — apply same to email
- Celery retry pattern: `autoretry_for=(Exception,), max_retries=3, retry_backoff=True` — use without modification
- structlog: already configured with JSON output and `request_id` propagation — `send_email()` should use `structlog.get_logger(__name__)`
- `transaction.on_commit()`: used in billing signals — apply same pattern for email dispatch

### Integration Points

- `INSTALLED_APPS` in `config/settings/base.py`: add `anymail` + `notifications` (removed by `--without email`)
- `ANYMAIL` settings block in `base.py`: `SENDGRID_API_KEY → RESEND_API_KEY` env var
- `EMAIL_BACKEND` setting: auto-switched in `base.py` based on `RESEND_API_KEY` presence
- Allauth email templates: override by placing templates in `notifications/templates/` at paths Allauth looks for (e.g. `account/email/password_reset_key_message.html`)
- CLI scaffolder (`create-foundation-app`): add `--without email` flag analogous to `--without billing` / `--without observability`

</code_context>

<specifics>
## Specific Ideas

No specific references or "I want it like X" moments — open to standard approaches for template rendering and anymail configuration.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 19-transactional-email_
_Context gathered: 2026-03-11_
