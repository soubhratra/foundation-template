# Requirements: Foundation Template

**Defined:** 2026-03-17
**Core Value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## v1.5 Requirements — Automated Testing & Claude Automation

Requirements for v1.5. Each maps to roadmap phases starting at phase 35.

### Automation Scripts

- [ ] **AUTO-01**: Developer can run `scripts/run-api-tests.sh` to execute the full pytest suite with environment setup and produce a structured failure report
- [ ] **AUTO-02**: Developer can run `scripts/run-e2e-tests.sh` to execute Playwright E2E tests against local or CI environment using the same script with no env-specific branches
- [ ] **AUTO-03**: Developer can run `scripts/run-all-tests.sh --mode=dev` to produce `test-results/FAILURES.md` in a structured format Claude can parse and act on for the auto-fix loop
- [ ] **AUTO-04**: Developer can run `scripts/check-req-coverage.py` to get a tabular gap report mapping OpenSpec requirement IDs to test coverage across pytest and Playwright

### Spec Traceability

- [ ] **TRACE-01**: Every existing pytest test function covering a specific requirement has a `@pytest.mark.req("REQ-ID")` marker so coverage can be automatically extracted by `check-req-coverage.py`
- [ ] **TRACE-02**: Every Playwright test covering a specific requirement has a `// @spec: REQ-ID` comment so coverage can be automatically extracted by `check-req-coverage.py`
- [ ] **TRACE-03**: `scripts/check-req-coverage.py` produces a per-requirement coverage status (✅ covered / ⚠️ partial / ❌ uncovered) for all v1.1–v1.4 milestone requirements across both test suites

### Web E2E — Core Flows

- [ ] **E2E-01**: Playwright tests cover the full auth flow — signup creates account and redirects to dashboard, login with valid credentials, login with invalid credentials shows error, logout clears session and redirects to login
- [ ] **E2E-02**: Playwright tests cover settings flows — profile update persists on refresh, GDPR data export button is visible and triggers download (closes v1.3 audit gap), account deletion confirmation flow completes
- [ ] **E2E-03**: Playwright tests cover billing flow — plan selection page renders with plan cards, upgrade CTA redirects to Stripe checkout, current plan badge visible in settings
- [ ] **E2E-04**: Playwright tests cover health probes — `GET /api/health/live`, `/api/health/ready`, `/api/health/startup` all return HTTP 200 via direct API assertions

### Web E2E — B2B & Social Flows

- [ ] **E2E-05**: Playwright tests cover social auth — Google and GitHub OAuth buttons are visible on login page, clicking triggers redirect to the respective OAuth provider
- [ ] **E2E-06**: Playwright tests cover RBAC — an admin-only page returns 403 for a regular user and is accessible for an admin user
- [ ] **E2E-07**: Playwright tests cover org management — create org succeeds, invite member sends invite, org appears in the user's org list
- [ ] **E2E-08**: Playwright tests cover API key management — create key displays the raw key once, key appears masked in the list, deleting removes it from the list
- [ ] **E2E-09**: Playwright tests cover webhook management — register an endpoint, it appears in the list, deleting removes it
- [ ] **E2E-10**: Playwright tests cover audit log — admin can view log entries that show actor identity, action type, and timestamp

### CI Integration

- [ ] **CI-01**: `.github/workflows/scheduled-e2e.yml` runs the full E2E suite nightly at 2am UTC — spins up Docker Compose, runs migrations, seeds test users, runs Playwright, then tears down; failure creates a GitHub issue
- [ ] **CI-02**: `ci.yml` includes an E2E smoke job on PRs running the critical path (auth flow + health probes) against a Docker Compose environment
- [ ] **CI-03**: CI E2E failures produce a structured `FAILURES.md` artifact uploaded to GitHub Actions that Claude can retrieve and act on to fix failures locally

### Claude Automation Documentation

- [ ] **DOCS-01**: Root `CLAUDE.md` documents the two-mode testing pattern (dev auto-fix loop vs CI report mode), all script commands, and when to use each — inherited verbatim by every project scaffolded from this template
- [ ] **DOCS-02**: Root `CLAUDE.md` documents the `@pytest.mark.req()` and `// @spec:` traceability conventions with the explicit rule that all new feature tests must include markers before a phase can be marked complete
- [ ] **DOCS-03**: `apps/api/CLAUDE.md` and `apps/web/CLAUDE.md` each document how to add tests for new features following established fixture patterns and spec traceability conventions

## Future Requirements

### v1.6 — Mobile E2E & Advanced Automation

- **MOB-E2E-01**: Detox E2E tests cover mobile auth flow (signup, login, logout) on iOS simulator
- **MOB-E2E-02**: Detox E2E tests cover mobile billing and settings flows
- **AUTO-05**: `scripts/run-all-tests.sh --mode=ci` posts failure summary to a Slack webhook
- **AUTO-06**: Claude Code hooks auto-run relevant tests after file edits (PostToolUse hook)

## Out of Scope

| Feature                                            | Reason                                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| Detox mobile E2E tests                             | Requires macOS runner + iOS simulator — high CI cost; defer to v1.6           |
| Visual regression testing (Chromatic, Percy)       | Product-specific; template provides functional coverage only                  |
| Load/performance testing (k6, Locust)              | Product-specific; beyond template scope                                       |
| Real OAuth credential testing in CI                | Requires live provider secrets; redirect assertion is sufficient for template |
| Synthetic monitoring (Checkly, Datadog Synthetics) | Hosted solution; product-specific configuration                               |

## Traceability

| Requirement | Phase | Status  |
| ----------- | ----- | ------- |
| AUTO-01     | 35    | Pending |
| AUTO-02     | 35    | Pending |
| AUTO-03     | 35    | Pending |
| AUTO-04     | 35    | Pending |
| TRACE-01    | 35    | Pending |
| TRACE-02    | 36    | Pending |
| TRACE-03    | 35    | Pending |
| E2E-01      | 36    | Pending |
| E2E-02      | 36    | Pending |
| E2E-03      | 36    | Pending |
| E2E-04      | 36    | Pending |
| E2E-05      | 37    | Pending |
| E2E-06      | 37    | Pending |
| E2E-07      | 37    | Pending |
| E2E-08      | 37    | Pending |
| E2E-09      | 37    | Pending |
| E2E-10      | 37    | Pending |
| CI-01       | 38    | Pending |
| CI-02       | 38    | Pending |
| CI-03       | 38    | Pending |
| DOCS-01     | 38    | Pending |
| DOCS-02     | 38    | Pending |
| DOCS-03     | 38    | Pending |

**Coverage:**

- v1.5 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---

_Requirements defined: 2026-03-17_
_Last updated: 2026-03-17 — initial definition_
