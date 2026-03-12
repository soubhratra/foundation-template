# Design: SaaS Platform Enhancements — v1.2 → v1.4

**Date:** 2026-03-11
**Status:** Approved
**Context:** Post-v1.1 gap analysis — what the foundation template needs to become a complete SaaS starter for both B2B and B2C products.

---

## Problem Statement

The template has excellent DevEx bones (ruff, ESLint, pre-commit, Turborepo, CI/CD, Docker, type generation, dual auth, billing) but is missing:

1. **Runtime observability** — near-zero logging structure, no tracing, no error tracking, no metrics
2. **Dev-time quality gates** — no secret scanning, no SAST, no dependency auditing, no N+1 detection
3. **SaaS functional table-stakes** — no transactional email, no RBAC, no social auth, no GDPR endpoints, no feature entitlements
4. **B2B module** — no multi-tenancy, no outbound webhooks, no API keys, no audit logging

## Constraints

- Tech stack is locked (Django, Next.js, Expo, Turborepo, pnpm) — no alternatives
- CLI scaffolder must support `--without <module>` for all optional modules
- Both B2B and B2C products must be supportable from a single template
- Core additions baked in; advanced/product-specific as OpenSpec specs only

---

## Milestone Plan

### v1.2 — Observability & DevEx Hardening

**Theme:** Every deployed app gets full visibility from day one. Every commit is security-checked.

#### Non-Functional (Runtime)

| Capability                 | Tool / Approach                                                                                                                                                                                                                                                                                              | Bake In                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| Structured logging         | `structlog` — JSON logs with `request_id`, `user_id`, `duration_ms`                                                                                                                                                                                                                                          | Yes (default)                           |
| Distributed tracing        | OpenTelemetry auto-instrumentation (Django + Celery + DB). OTLP exporter. Jaeger in Docker Compose for local dev.                                                                                                                                                                                            | Yes (default)                           |
| Error tracking + analytics | `ObservabilityAdapter` ABC with `PostHogAdapter` default. Single `POSTHOG_API_KEY` env var. Covers exceptions, session replay, product analytics, and feature flags across Django + Celery + Next.js + Expo. Projects can swap to `SentryAdapter` via one Django setting if richer error grouping is needed. | Yes (`--without observability` removes) |
| Enhanced health probes     | `/api/health/live`, `/api/health/ready`, `/api/health/startup`                                                                                                                                                                                                                                               | Yes (default)                           |
| Rate limiting              | `django-ratelimit` on auth endpoints. Redis-backed.                                                                                                                                                                                                                                                          | Yes (default)                           |
| Security headers           | `django-csp`, HSTS, X-Frame-Options via middleware. Next.js `headers()` config.                                                                                                                                                                                                                              | Yes (default)                           |
| Caching layer              | `django-redis` as default cache backend. Session store via Redis.                                                                                                                                                                                                                                            | Yes (default)                           |
| Celery Beat scaffold       | `celery beat` service in Docker Compose. Example recurring tasks.                                                                                                                                                                                                                                            | Yes (default)                           |
| Background job monitoring  | Flower in Docker Compose (dev only). Sentry Crons spec for production.                                                                                                                                                                                                                                       | Dev only                                |

#### Non-Functional (Dev-Time)

| Capability             | Tool                       | Where           |
| ---------------------- | -------------------------- | --------------- |
| Secret scanning        | `detect-secrets`           | pre-commit + CI |
| Python SAST            | `bandit`                   | pre-commit + CI |
| Dependency auditing    | `pip-audit` + `pnpm audit` | CI gate         |
| N+1 detection          | `nplusone` in test suite   | pytest fixture  |
| API contract fuzzing   | `schemathesis`             | CI job          |
| Query analysis (local) | `django-debug-toolbar`     | Local dev only  |
| Commit lint            | `commitlint`               | pre-commit hook |
| Complexity gates       | ruff McCabe (max=10)       | pre-commit      |

---

### v1.3 — SaaS Functional Baseline

**Theme:** Every scaffolded product ships with the functional building blocks every SaaS needs.

| Feature              | Approach                                                                                                                  | Bake In                         |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| Transactional email  | `EmailAdapter` ABC (mirrors `PaymentAdapter`). `SendGridAdapter` default. Celery-queued. HTML templates.                  | Yes (`--without email` removes) |
| Social auth          | allauth Google + GitHub (web). Apple (mobile). `--without social-auth` removes.                                           | Yes (optional)                  |
| GDPR baseline        | `DELETE /api/v1/account/` (hard delete + cascade), `GET /api/v1/account/export` (JSON). Cookie consent banner in Next.js. | Yes (default)                   |
| RBAC                 | Django groups wired to Ninja Extra guards. `@require_role("admin")` decorator. Role assignment API.                       | Yes (default)                   |
| Feature entitlements | `has_feature(user, key)` evaluated against plan config in settings. Lightweight, no external service.                     | Yes (default)                   |

---

### v1.4 — B2B Module (Optional)

**Theme:** One flag to enable full multi-tenant B2B capabilities.

| Feature           | Approach                                                                                                          | Bake In                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------ |
| Multi-tenancy     | `Organization` model, membership + roles, per-org billing, request-scoped tenant isolation. `--with b2b` adds it. | Optional module          |
| Outbound webhooks | Endpoint registry, Celery delivery queue, exponential backoff retry, HMAC signing, delivery log.                  | Optional (in B2B module) |
| API keys          | `APIKey` model, scopes, rate limiting per key, usage tracking.                                                    | Optional (in B2B module) |
| Audit logging     | `AuditLog` model via `django-pgaudit`. Records who changed what, when, from where.                                | Optional (in B2B module) |
| Admin backoffice  | `django-unfold` + `django-hijack` (impersonation). Customer support tooling.                                      | Optional (in B2B module) |

---

### Specs Only (No Code)

These are too product-specific to bake in. Will be documented as OpenSpec guides:

- SSO / SAML (python-saml, allauth enterprise)
- Usage-based / metered billing (Stripe Metering API)
- Push notifications (Expo FCM/APNs)
- SMS + 2FA (Twilio + django-otp)
- Landing page pattern (apps/landing/ scaffold)
- Alerting strategy (Grafana alerts, PagerDuty, OpsGenie)
- SLO/SLI framework (Prometheus recording rules)
- Database connection pooling at scale (PgBouncer)

---

## Execution Approach

Each milestone follows the GSD workflow:

```
/gsd:new-milestone  →  requirements  →  roadmap
  → per phase: /gsd:discuss-phase  →  /gsd:plan-phase  →  /gsd:execute-phase  →  /gsd:verify-work
→ /gsd:complete-milestone  →  /opsx:new gsd-milestone-N-sync  →  /opsx:archive
```

OpenSpec delta specs are created per milestone to capture decisions before archiving.

---

## Success Criteria

- Every project scaffolded from the template ships with structured logging, tracing, error tracking, and security headers with zero extra configuration
- `detect-secrets`, `bandit`, and `pip-audit` block vulnerable commits in CI
- All new functional modules are removable via `--without <module>` flag
- B2B capabilities are fully isolated — `--with b2b` adds them, absence has no coupling
