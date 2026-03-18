## 1. Automation Scripts + Requirement Coverage Checker

- [x] 1.1 Create `scripts/` directory at repo root and add `scripts/run-api-tests.sh` — runs pytest suite, writes `test-results/FAILURES.md` as a markdown table with columns Test / File / Assertion / Requirements / Status, creates `test-results/` if absent, exits 0 on pass / 1 on fail
- [x] 1.2 Create `scripts/run-e2e-tests.sh` — runs Playwright suite using `BASE_URL` env var (defaults to `http://localhost:3000`), writes `test-results/FAILURES.md` in the same format as the API runner
- [x] 1.3 Create `scripts/run-all-tests.sh` — accepts `--mode=dev` and `--mode=ci`; invokes `run-api-tests.sh` then `run-e2e-tests.sh`; merges failures under separate section headers; exits non-zero in CI mode if any failure
- [x] 1.4 Create `scripts/check-req-coverage.py` — parses requirement IDs from ROADMAP.md phase blocks (`Requirements: X, Y`); scans `apps/api/tests/**/*.py` for `@pytest.mark.req()` and `apps/web/tests/e2e/**/*.ts` for `// @spec:`; outputs per-requirement table with `covered` / `partial` / `uncovered` status; exits 1 if any `uncovered`
- [x] 1.5 Add `test-results/` to root `.gitignore`

## 2. Spec Traceability — pytest Marker Retrofit

- [x] 2.1 Register `req` custom marker in `apps/api/pytest.ini` (or `pyproject.toml` `[tool.pytest.ini_options]`) to suppress `PytestUnknownMarkWarning`
- [x] 2.2 Add `@pytest.mark.req()` markers to all existing billing test functions (v1.1 requirement IDs)
- [x] 2.3 Add `@pytest.mark.req()` markers to all existing observability, health probe, and security test functions (v1.2 requirement IDs)
- [x] 2.4 Add `@pytest.mark.req()` markers to all existing transactional email, social auth, GDPR, RBAC, and entitlements test functions (v1.3 requirement IDs)
- [x] 2.5 Add `@pytest.mark.req()` markers to all existing org, webhooks, API key, audit log, and admin test functions (v1.4 requirement IDs)
- [x] 2.6 Run `scripts/check-req-coverage.py` and verify zero uncovered requirements for v1.1–v1.4 requirement IDs

## 3. Playwright Setup

- [x] 3.1 Add `@playwright/test` as a dev dependency in `apps/web/package.json`; run `pnpm install`
- [x] 3.2 Create `apps/web/playwright.config.ts` — sets `baseURL` from `BASE_URL` env var (default `http://localhost:3000`), Chromium-only browser, test directory `tests/e2e/`, starts fresh browser context per test
- [x] 3.3 Add `test:e2e` script to `apps/web/package.json` invoking `playwright test`
- [x] 3.4 Create `apps/web/tests/e2e/` directory structure with a `fixtures/` subdirectory and a `global-setup.ts` for test user seeding

## 4. Web E2E — Core Flows

- [x] 4.1 Create `apps/web/tests/e2e/auth.spec.ts` — tests: signup → dashboard redirect, login valid credentials, login invalid credentials shows inline error, logout clears session; add `// @spec: E2E-01` comment; self-seeding with `beforeAll` API call
- [x] 4.2 Create `apps/web/tests/e2e/settings.spec.ts` — test: click "Download my data" button triggers file download (or assert `GET /api/v1/account/export` returns 200 via request context as fallback); add `// @spec: E2E-02`
- [x] 4.3 Create `apps/web/tests/e2e/billing.spec.ts` — tests: plan cards visible, current plan badge visible, upgrade CTA links to Stripe URL; add `// @spec: E2E-03`
- [x] 4.4 Create `apps/web/tests/e2e/health.spec.ts` — tests: GET `/api/health/live`, `/api/health/ready`, `/api/health/startup` each return 200 via Playwright request context; add `// @spec: E2E-04`
- [x] 4.5 Verify all four core spec files pass against local dev server (`pnpm --filter web test:e2e`)

## 5. Web E2E — B2B & Social Flows

- [x] 5.1 Create `apps/web/tests/e2e/social-auth.spec.ts` — tests: Google + GitHub OAuth buttons present on login page; clicking each triggers redirect to correct provider URL; add `// @spec: E2E-05`
- [x] 5.2 Create `apps/web/tests/e2e/rbac.spec.ts` — tests: regular user gets 403 on admin-only route, admin user accesses same route successfully; seed admin + regular test users; add `// @spec: E2E-06`
- [x] 5.3 Create `apps/web/tests/e2e/org-management.spec.ts` — tests: create org appears in list, invite flow shows pending member; seed org owner user; add `// @spec: E2E-07`
- [x] 5.4 Create `apps/web/tests/e2e/api-keys.spec.ts` — tests: create key shows raw value once, masked in list on refresh, delete removes from list; add `// @spec: E2E-08`
- [x] 5.5 Create `apps/web/tests/e2e/webhooks-audit.spec.ts` — tests: register endpoint appears in list, delete removes it, admin sees audit log entries with actor / action / timestamp; add `// @spec: E2E-09, E2E-10`
- [x] 5.6 Verify all B2B spec files pass against local dev server

## 6. CI Integration

- [x] 6.1 Create `.github/workflows/e2e-nightly.yml` — schedule: `0 2 * * *`; steps: docker compose up → wait for ready → migrate → seed → `scripts/run-e2e-tests.sh`; upload `test-results/FAILURES.md` as artifact `e2e-failures` (7-day retention); on failure open GitHub issue via `gh issue create` with run link + artifact link labeled `e2e-failure,automated`; always run `docker compose down -v`
- [x] 6.2 Add duplicate-issue guard to `e2e-nightly.yml` — check for existing open `e2e-failure` issue before creating a new one; comment on existing issue if already open
- [x] 6.3 Add E2E smoke job to existing `.github/workflows/ci.yml` — runs auth + health probe Playwright tests only; Docker Compose environment; `BASE_URL` pointing to container; required status check; target runtime < 3 minutes
- [x] 6.4 Verify `e2e-nightly.yml` YAML is valid (`act` dry-run or `actionlint` if available)

## 7. CLAUDE.md Documentation

- [x] 7.1 Update root `CLAUDE.md` — add "Testing & Automation" section documenting: dev loop mode (`run-all-tests.sh --mode=dev` → Claude reads FAILURES.md → fixes → repeat), CI report mode, and the rule that all new feature tests must include `@pytest.mark.req()` or `// @spec:` before a phase is complete
- [x] 7.2 Update `apps/api/CLAUDE.md` — add section: which fixture patterns to follow (factory_boy, `authenticated_client`, `@pytest.mark.django_db`), how to add `@pytest.mark.req()` to new tests, and that markers are required before submitting work for verification
- [x] 7.3 Update `apps/web/CLAUDE.md` — add section: Playwright test location (`tests/e2e/`), how to run (`pnpm test:e2e`), self-seeding pattern, `// @spec:` comment requirement, and `scripts/check-req-coverage.py` usage
