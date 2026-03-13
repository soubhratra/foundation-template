## ADDED Requirements

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
