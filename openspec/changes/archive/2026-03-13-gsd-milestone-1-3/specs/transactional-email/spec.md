## Implementation Decisions

### Why Resend (not SendGrid) as the default ESP

`django-anymail` dropped official SendGrid support in June 2025. Resend is the recommended replacement: it has first-class anymail support, a generous free tier, and a clean API. `django-anymail[resend]` is the declared dependency; `RESEND_API_KEY` is the activation environment variable.

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
