# Requirements: Foundation Template

**Defined:** 2026-03-11
**Core Value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## v1.2 Requirements — Observability & DevEx Hardening

Requirements for v1.2. Each maps to roadmap phases starting at phase 13.

### Observability

- [ ] **OBS-01**: Developer can see structured JSON logs with `request_id`, `user_id`, `duration_ms` auto-injected on every Django request via `structlog`
- [ ] **OBS-02**: Developer can trace requests end-to-end across Django + Celery + PostgreSQL via OpenTelemetry auto-instrumentation with OTLP exporter; Jaeger runs in Docker Compose for local inspection
- [ ] **OBS-03**: Developer can capture exceptions + product analytics + session replay via `ObservabilityAdapter` ABC with `PostHogAdapter` as default — covers Django + Celery + Next.js + Expo — `--without observability` removes it cleanly; `SentryAdapter` available as documented swap
- [ ] **OBS-04**: Ops can probe app readiness via `GET /api/health/live` (process alive), `/api/health/ready` (DB + Redis + Celery reachable), `/api/health/startup` (migrations applied)
- [ ] **OBS-05**: Developer gets a `celery beat` service in Docker Compose with an example periodic task scaffold (noop task demonstrating retry + error handling patterns)
- [ ] **OBS-06**: Developer can view Celery worker and task status via Flower running in Docker Compose (dev only — not in production Docker Compose)

### Security & Performance

- [ ] **SEC-01**: Auth endpoints are rate-limited via `django-ratelimit` with Redis-backed counters; limits configurable per endpoint via Django settings
- [ ] **SEC-02**: Every HTTP response ships with security headers (`django-csp`, HSTS, `X-Frame-Options`, `Referrer-Policy`) via Django middleware; Next.js `headers()` config ships matching CSP + frame policy
- [ ] **SEC-03**: Django cache and session store use Redis via `django-redis` as default backend — `LocMemCache` is not used in any non-test environment

### Dev-Time Quality Gates

- [ ] **DEV-01**: Secrets are blocked at commit time and fail CI via `detect-secrets` pre-commit hook + CI step
- [ ] **DEV-02**: Python security issues (hardcoded passwords, unsafe subprocess calls, etc.) are flagged at commit time and in CI via `bandit` pre-commit hook + CI step
- [ ] **DEV-03**: Known-vulnerable Python and JS dependencies block CI merge via `pip-audit` + `pnpm audit` gate
- [ ] **DEV-04**: N+1 query regressions fail the backend test suite via `nplusone` auto-detecting pytest fixture (raises on detected N+1 unless explicitly allowed)
- [ ] **DEV-05**: API contract regressions are caught in CI via `schemathesis` property-based fuzzing against the OpenAPI spec on the Django test server
- [ ] **DEV-06**: Developer can analyze SQL queries, cache hits, and request profiling locally via `django-debug-toolbar` (dev only — disabled in test + production)
- [ ] **DEV-07**: Non-conventional commits are blocked at commit time via `commitlint` pre-commit hook enforcing the Conventional Commits spec
- [ ] **DEV-08**: Code complexity exceeding McCabe max=10 is blocked by ruff in pre-commit + CI

## Future Requirements

### v1.3 — SaaS Functional Baseline

- **EMAIL-01**: EmailAdapter ABC with SendGridAdapter default; Celery-queued transactional email with HTML templates; `--without email` removes it
- **AUTH-EXT-01**: Social auth via allauth Google + GitHub (web), Apple (mobile); `--without social-auth` removes it
- **GDPR-01**: Hard account deletion via `DELETE /api/v1/account/` (cascade all user data)
- **GDPR-02**: Data export via `GET /api/v1/account/export` (JSON of all user-owned records)
- **GDPR-03**: Cookie consent banner in Next.js
- **RBAC-01**: Django groups wired to Ninja Extra guards with `@require_role("admin")` decorator and role assignment API
- **ENT-01**: `has_feature(user, key)` evaluated against plan config in settings; lightweight, no external service

### v1.4 — B2B Module (Optional)

- **B2B-01**: `Organization` model with membership + roles, per-org billing, request-scoped tenant isolation (`--with b2b` adds it)
- **B2B-02**: Outbound webhook registry with Celery delivery queue, exponential backoff, HMAC signing, delivery log
- **B2B-03**: `APIKey` model with scopes, per-key rate limiting, usage tracking
- **B2B-04**: `AuditLog` model via `django-pgaudit` — records who changed what, when, from where
- **B2B-05**: `django-unfold` admin backoffice + `django-hijack` for customer support impersonation

## Out of Scope

| Feature                         | Reason                                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Sentry as default error tracker | PostHog covers errors + analytics + flags in one SDK; Sentry remains available via SentryAdapter swap |
| Grafana / Prometheus stack      | Too heavyweight for template; document as OpenSpec guide for projects that need it                    |
| PagerDuty / OpsGenie alerting   | Product-specific; template provides structured logs + traces, alerting is project configuration       |
| SSO / SAML                      | Too product-specific; will be OpenSpec guide only                                                     |
| Push notifications              | Product-specific; OpenSpec guide                                                                      |
| SMS + 2FA                       | Product-specific; OpenSpec guide                                                                      |

## Traceability

| Requirement | Phase | Status  |
| ----------- | ----- | ------- |
| OBS-01      | 13    | Pending |
| OBS-02      | 13    | Pending |
| OBS-03      | 14    | Pending |
| OBS-04      | 15    | Pending |
| OBS-05      | 15    | Pending |
| OBS-06      | 15    | Pending |
| SEC-01      | 16    | Pending |
| SEC-02      | 16    | Pending |
| SEC-03      | 16    | Pending |
| DEV-01      | 17    | Pending |
| DEV-02      | 17    | Pending |
| DEV-03      | 17    | Pending |
| DEV-06      | 17    | Pending |
| DEV-04      | 18    | Pending |
| DEV-05      | 18    | Pending |
| DEV-07      | 18    | Pending |
| DEV-08      | 18    | Pending |

**Coverage:**

- v1.2 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---

_Requirements defined: 2026-03-11_
_Last updated: 2026-03-11 — traceability populated by roadmapper (phases 13–18)_
