## Why

The Foundation Template has shipped v1.0–v1.4 (34 phases, ~150 requirements) with zero browser-level E2E coverage and no structured automation loop. Claude agents can write and run code but have no machine-readable feedback loop — when tests fail there is no structured report tying failures back to OpenSpec requirement IDs, so Claude cannot self-correct. This milestone closes that gap: every shipped UI-facing feature gets a Playwright test, every test carries a spec traceability marker, and Claude can run one script to get a structured FAILURES.md it can parse and act on autonomously.

## What Changes

- **New**: Shell scripts `scripts/run-api-tests.sh`, `scripts/run-e2e-tests.sh`, `scripts/run-all-tests.sh` providing a single entrypoint for each test tier
- **New**: `scripts/check-req-coverage.py` — scans all test files for `@pytest.mark.req()` and `// @spec:` markers, outputs a per-requirement coverage table
- **New**: `@pytest.mark.req("REQ-ID")` markers added to every existing pytest test that exercises a specific feature (retrofitted across all v1.1–v1.4 test files)
- **New**: Playwright test suite under `apps/web/tests/e2e/` covering auth, settings/GDPR export, billing, health probes, social auth redirects, RBAC, org management, API keys, webhooks, and audit log
- **New**: Nightly GitHub Actions workflow (`e2e-nightly.yml`) — spins up Docker Compose, runs full Playwright suite, auto-opens GitHub issue on failure with FAILURES.md artifact link
- **New**: E2E smoke job added to existing `ci.yml` PR workflow — blocks merge if auth or health probe flows fail
- **Modified**: `apps/api/CLAUDE.md` and `apps/web/CLAUDE.md` — document fixture patterns and spec traceability marker requirements
- **Modified**: Root `CLAUDE.md` — documents the two-mode testing pattern (dev auto-fix loop vs CI report mode)

## Capabilities

### New Capabilities

- `automation-scripts`: Shell runners and Python coverage checker that form the Claude automation loop — single entrypoints for API tests, E2E tests, and combined runs; produce structured `test-results/FAILURES.md` parseable by Claude; `check-req-coverage.py` maps every requirement ID to test coverage status
- `spec-traceability`: Convention and tooling for tying tests to OpenSpec requirements — `@pytest.mark.req("REQ-ID")` for pytest, `// @spec: REQ-ID` for Playwright; enforced at phase completion via `check-req-coverage.py`
- `web-e2e-core`: Playwright tests for core flows — signup/login/logout, GDPR data export button (closes v1.3 audit gap), billing plan display, health probe API assertions; self-seeding fixtures using API calls (no pre-existing DB state required)
- `web-e2e-b2b`: Playwright tests for B2B and social flows — OAuth button presence + redirect verification, RBAC access control (403 vs 200), org creation + invite, API key create/mask/delete, webhook + audit log management
- `ci-e2e-integration`: Nightly GitHub Actions workflow with Docker Compose environment, FAILURES.md artifact upload, auto-issue creation on failure; E2E smoke job in PR CI blocking merge

### Modified Capabilities

- `testing`: Existing testing spec gains requirements for spec traceability markers (every new feature test must include `@pytest.mark.req()` or `// @spec:` before phase can be marked complete), Playwright as the web E2E framework alongside existing Detox (mobile), and the two-mode automation pattern (dev loop vs CI report)

## Impact

- **`apps/api/tests/`**: All existing pytest test files — add `@pytest.mark.req()` markers retrofitted to ~50+ test functions spanning billing, webhooks, API keys, org, RBAC, GDPR, social auth, health probes
- **`apps/web/tests/e2e/`**: New directory — Playwright test files for auth, settings, billing, health, social, rbac, org, apikeys, webhooks, audit
- **`scripts/`**: New directory at repo root — `run-api-tests.sh`, `run-e2e-tests.sh`, `run-all-tests.sh`, `check-req-coverage.py`
- **`test-results/`**: Runtime artifact directory (gitignored) — `FAILURES.md` written by test runners
- **`.github/workflows/`**: `e2e-nightly.yml` (new), `ci.yml` (add E2E smoke job)
- **`CLAUDE.md`**: Root file updated with two-mode testing documentation
- **`apps/api/CLAUDE.md`**, **`apps/web/CLAUDE.md`**: Updated with fixture patterns and spec traceability requirements
- **`apps/web/playwright.config.ts`**: New — Playwright configuration pointing at dev server or `$BASE_URL`
- **`apps/web/package.json`**: Add `@playwright/test` dev dependency
- **`apps/api/conftest.py`** or **`pytest.ini`**: Register `req` custom marker to suppress PytestUnknownMarkWarning
