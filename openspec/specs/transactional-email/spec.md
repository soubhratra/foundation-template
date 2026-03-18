# Transactional Email

> Defines the pluggable email system: `django-anymail[resend]` with auto-switch backend (Resend when `RESEND_API_KEY` is set, console otherwise), async Celery dispatch on transaction commit, HTML templates with `premailer` CSS inlining, and scaffolder opt-out.

## Overview

Transactional email uses `django-anymail` with Resend as the default ESP. The backend selection is automatic at startup in `base.py`: if `RESEND_API_KEY` is present, the Resend backend activates; otherwise the console backend is used. This means no manual configuration change is needed between local dev and production — set the env var, deploy, and email works.

All outbound email is dispatched via a Celery task enqueued inside `transaction.on_commit()`, preventing emails from firing if the triggering transaction rolls back (e.g., welcome email during a user creation that later fails). HTML templates use `premailer` for CSS inlining at render time with `allow_network=False`.

The email system lives in `apps/api/apps/notifications/` and is gated behind `# EMAIL MODULE` / `# END EMAIL MODULE` scaffolder markers for opt-out removal.

## Requirements

### Requirement: Pluggable Email Adapter with Auto-Switch Backend

The system SHALL implement transactional email through a pluggable adapter pattern using `django-anymail[resend]` with automatic backend selection based on environment variables.

#### Scenario: Resend backend activated when API key is set

- **WHEN** `RESEND_API_KEY` is set to a non-empty string in the environment
- **THEN** `EMAIL_BACKEND` SHALL be `"anymail.backends.resend.EmailBackend"`
- **AND** `ANYMAIL` settings SHALL include `{"RESEND_API_KEY": RESEND_API_KEY}`

#### Scenario: Console backend used in local development

- **WHEN** `RESEND_API_KEY` is absent or empty
- **THEN** `EMAIL_BACKEND` SHALL be `"django.core.mail.backends.console.EmailBackend"`
- **AND** no Resend account or credentials are required to run locally

#### Scenario: Backend switch is automatic at startup

- **WHEN** the Django application starts
- **THEN** the backend selection logic SHALL execute in `config/settings/base.py` (not `development.py`)
- **AND** no manual override SHALL be required per environment

### Requirement: Async Email Dispatch via Celery on Transaction Commit

All outbound emails SHALL be dispatched asynchronously via a Celery task that is enqueued only after the database transaction commits.

#### Scenario: Email enqueued after transaction commit

- **WHEN** `send_email(template_name, context, to_email)` is called inside a database transaction
- **THEN** `send_email_task.delay()` SHALL be called inside `transaction.on_commit()`
- **AND** the email SHALL NOT be sent if the transaction rolls back

#### Scenario: Unit test fallback without database context

- **WHEN** `send_email()` is called without an active database connection (unit test context without `@pytest.mark.django_db`)
- **THEN** the `on_commit` callback SHALL fire directly (no transaction wrapper)
- **AND** the semantic behavior SHALL be equivalent for test assertions

### Requirement: HTML Email Templates with Premailer CSS Inlining

Email templates SHALL be HTML files with CSS inlined at send time using `premailer`, with the subject extracted from a sentinel comment in the template.

#### Scenario: CSS is inlined before sending

- **WHEN** a template is rendered
- **THEN** `premailer.transform(html, allow_network=False)` SHALL be called
- **AND** `<style>` blocks SHALL be removed from the rendered output
- **AND** inline `style=` attributes SHALL be added to HTML elements

#### Scenario: Subject extracted from template sentinel comment

- **WHEN** a template begins with `<!-- SUBJECT: <subject text> -->`
- **THEN** `_extract_subject()` SHALL parse and return that text as the email subject
- **AND** the sentinel comment SHALL be the absolute first character in the rendered template

#### Scenario: Allauth transactional emails use custom templates

- **WHEN** allauth sends a password reset or email verification email
- **THEN** the system SHALL use templates at `notifications/templates/account/email/` to shadow allauth's built-in templates
- **AND** templates SHALL be discovered via `APP_DIRS=True` in `TEMPLATES` settings

### Requirement: Notifications App Structure

The email system SHALL live in `apps/api/apps/notifications/` as a standalone Django app.

#### Scenario: App is registered in INSTALLED_APPS with scaffolder sentinel

- **WHEN** the notifications app is active
- **THEN** `"apps.notifications"` SHALL appear in `INSTALLED_APPS` with inline comment `# EMAIL MODULE`
- **AND** `"anymail"` SHALL appear in `INSTALLED_APPS` with inline comment `# EMAIL MODULE`
- **AND** all email-related settings SHALL be wrapped in `# EMAIL MODULE` / `# END EMAIL MODULE` fence comments for scaffolder removal

#### Scenario: Core email templates ship with the template

- **WHEN** the template is scaffolded (email module included)
- **THEN** the following templates SHALL exist under `apps/api/apps/notifications/templates/email/`:
  - `base.html` — base layout
  - `welcome.html`
  - `password_reset.html`
  - `email_verification.html`
  - `invoice_ready.html`

### Requirement: CLI Scaffolder Opt-Out via --without email

The `create-foundation-app` CLI SHALL support removing the email module via a `--without email` flag, or an interactive prompt selection.

#### Scenario: removeEmailModule() strips all email artifacts

- **WHEN** `--without email` is selected during scaffolding
- **THEN** `removeEmailModule(outputDir)` SHALL:
  - Delete `apps/api/apps/notifications/` directory
  - Strip `"anymail"` and `"apps.notifications"` lines from `INSTALLED_APPS`
  - Remove the `# EMAIL MODULE` / `# END EMAIL MODULE` settings block from `base.py`
  - Remove `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` from `.env.example`

#### Scenario: Email is selected by default in interactive prompt

- **WHEN** the user runs the CLI without flags
- **THEN** "Transactional Email" SHALL appear as a pre-selected option in the features multi-select prompt

## Implementation Decisions

### Why Resend (not SendGrid) as the default ESP

`django-anymail` dropped official SendGrid support. Resend is the recommended replacement: it has first-class anymail support, a generous free tier, and a clean API. `django-anymail[resend]` is the declared dependency; `RESEND_API_KEY` is the activation environment variable.

**Alternative rejected:** SendGrid — anymail's official removal makes it a maintenance liability for a template that needs to work out of the box without manual configuration.

**Alternative rejected:** Mailgun, SES — equally valid ESPs but require more credential setup (domain verification, IAM roles). Resend works immediately with just an API key.

### Why ConsoleAdapter as the default (not a development SMTP server)

No credentials, no Docker service, no external dependency. Every developer can run the template locally and see email output in the terminal on day one. The auto-switch logic lives in `base.py` (not `development.py`) so staging environments with no `RESEND_API_KEY` set also fall back safely.

**Alternative rejected:** MailHog / Mailpit Docker service — useful for end-to-end email testing but adds a mandatory service to the Docker Compose stack; deferred to product-specific choice.

### Why `transaction.on_commit()` for Celery enqueue

Enqueuing a Celery task inside `on_commit()` prevents a race condition where the task fires before the triggering database transaction commits (e.g., a welcome email task dispatched during user creation that reads the user record before it is visible to other connections). If the transaction rolls back, no email is sent.

**Trade-off:** In unit tests without an active database transaction, `on_commit()` fires the callback synchronously — this is Django's documented behaviour and preserves test assertion semantics.

### Why `premailer` for CSS inlining (not a cloud email service's rendering)

Email clients (particularly Outlook and Gmail) strip `<style>` blocks. Inline CSS is required for reliable rendering. `premailer` handles this server-side at render time with `allow_network=False` so it never makes external HTTP calls during email sending. The alternative — relying on the ESP to inline CSS — creates a provider-specific dependency that breaks when switching backends.
