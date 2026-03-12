# Dev Setup — First Steps After Scaffolding

Run this checklist **once per new project**, immediately after scaffolding from
the foundation template. None of these steps are automated by the scaffolder.

---

## What the Template Carries for You

The following are already baked into the template source code and require **no
action** on your part:

| Area                   | What is already done                                                                                                                                                        |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CSRF                   | `use-auth.ts` reads the `csrftoken` cookie and injects `X-CSRFToken` on every mutating request (POST / PUT / PATCH / DELETE).                                               |
| CSRF priming           | Before the first login attempt, the client calls `GET /api/v1/auth/browser/v1/config` to seed the CSRF cookie if it is not yet present.                                     |
| Session cookies        | `createApiClient` passes `credentials: "include"` so session cookies are sent with every API call after login.                                                              |
| Allauth errors         | `formatError` reads `payload.errors[0].message` (allauth format) before falling back to HTTP status text. Login now shows the real error instead of generic "Unauthorized". |
| Dev email verification | `development.py` sets `ACCOUNT_EMAIL_VERIFICATION = "optional"` so you can sign in without completing an email verification flow locally. Production keeps `"mandatory"`.   |

---

## One-Time Bootstrap Steps

### 1. Copy and fill the API env file

```bash
cp apps/api/.env.example apps/api/.env
```

Open `apps/api/.env` and set at minimum:

```
SECRET_KEY=any-random-string-here
DATABASE_URL=postgres://foundation:foundation@localhost:5432/foundation
```

All other values have safe defaults for local development.

### 2. Install pre-commit hooks

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

The second command activates the `commitlint` commit-msg hook that enforces
Conventional Commits format. Both steps are required — `pre-commit install`
alone does not activate commit-msg stage hooks.

### 3. Start the backing services

```bash
docker compose up -d
```

This starts Postgres + PGVector + Redis + Celery worker/beat + Jaeger. Wait a
few seconds for Postgres to become ready before running migrations.

### 4. Run database migrations

```bash
cd apps/api
python manage.py migrate
```

This creates all tables including allauth's session and email tables.

### 5. Create your first dev user

**Option A — Use the app's signup form (recommended).**
Start the API and the web app, navigate to `/signup`, and register normally.
Because `ACCOUNT_EMAIL_VERIFICATION = "optional"` in dev, you can log straight
in without clicking a verification link.

**Option B — Django shell (useful in headless/CI environments).**

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()
user = User.objects.create_user(email="dev@example.com", password="changeme123")
EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
```

> Do **not** use `createsuperuser` for your primary test account. It bypasses
> allauth and leaves the `EmailAddress` table empty, which can cause subtle
> failures with allauth's session lookups.

---

## Quick Reference

```
cp apps/api/.env.example apps/api/.env  # fill in SECRET_KEY + DATABASE_URL
pre-commit install && pre-commit install --hook-type commit-msg
docker compose up -d
cd apps/api && python manage.py migrate
# then sign up via the web app OR use the shell snippet above
```

---

## Troubleshooting

| Symptom                                                  | Likely cause                        | Fix                                                                                                                   |
| -------------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `403 Forbidden` on login POST                            | CSRF cookie not present or not sent | Should not happen — template already handles this. Check CORS_ALLOWED_ORIGINS includes your frontend URL.             |
| `401 Unauthorized` on login                              | Account not verified                | Use Option A above or verify via `EmailAddress.objects.filter(user=user).update(verified=True)`.                      |
| `401` on all API calls after login                       | Session cookie not sent             | Should not happen — `credentials: "include"` is set in the client. Check `CORS_ALLOW_CREDENTIALS = True` in settings. |
| Login shows generic "Unauthorized" instead of real error | Old version of `formatError`        | Pull latest template — allauth error parsing is now built in.                                                         |
