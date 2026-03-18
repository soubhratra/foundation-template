## ADDED Requirements

### Requirement: Web E2E Testing with Playwright

The web app SHALL use Playwright (`@playwright/test`) for browser-level end-to-end tests of all UI-facing features.

#### Scenario: Playwright configuration at apps/web

- **WHEN** Playwright tests are run
- **THEN** `apps/web/playwright.config.ts` MUST be the configuration entry point
- **THEN** tests MUST be located under `apps/web/tests/e2e/`
- **THEN** `pnpm --filter web test:e2e` MUST invoke the Playwright runner

#### Scenario: Browser matrix

- **WHEN** the PR smoke E2E job runs
- **THEN** Playwright MUST use Chromium only
- **WHEN** the nightly E2E job runs
- **THEN** Playwright MUST run both Chromium and Firefox

#### Scenario: Playwright dev dependency

- **WHEN** `pnpm install` runs in the `apps/web` workspace
- **THEN** `@playwright/test` MUST be installed as a dev dependency
- **THEN** no Playwright dependency MUST appear in the production bundle

### Requirement: Two-mode test automation pattern

The template SHALL support two automation modes: a dev loop mode for Claude-assisted self-correction, and a CI report mode for structured artifact production.

#### Scenario: Dev loop mode invocation

- **WHEN** a developer (or Claude) runs `scripts/run-all-tests.sh --mode=dev`
- **THEN** both API and E2E suites run
- **THEN** `test-results/FAILURES.md` is written with full failure detail including requirement IDs
- **THEN** Claude MUST be able to read `FAILURES.md`, identify which tests to fix, cross-reference requirement IDs against OpenSpec specs, apply fixes, and re-run without human intervention

#### Scenario: CI report mode invocation

- **WHEN** `scripts/run-all-tests.sh --mode=ci` is run in GitHub Actions
- **THEN** the same script executes both suites
- **THEN** `test-results/FAILURES.md` is written and uploaded as a CI artifact
- **THEN** the script exits non-zero if any test fails (blocks CI merge or triggers issue creation)

### Requirement: Spec traceability marker enforcement

Every new feature test added to the template (after v1.5) SHALL carry a spec traceability marker before the phase that introduces it is marked complete.

#### Scenario: New pytest test without marker is a phase completion blocker

- **WHEN** a new pytest test is written for a feature with an OpenSpec requirement ID
- **THEN** `@pytest.mark.req("REQ-ID")` MUST be present on that test function
- **THEN** the phase MUST NOT be marked complete until `check-req-coverage.py` reports that requirement as covered

#### Scenario: New Playwright test without marker is a phase completion blocker

- **WHEN** a new Playwright test is written for a feature with an OpenSpec requirement ID
- **THEN** `// @spec: REQ-ID` MUST appear as the first line of the test body
- **THEN** the phase MUST NOT be marked complete until `check-req-coverage.py` reports that requirement as covered

## MODIFIED Requirements

### Requirement: CI Integration with GitHub Actions

CI SHALL run parallel jobs for API, web unit, web E2E (smoke), and mobile with type staleness verification.

#### Scenario: API CI job

- **WHEN** a pull request is opened
- **THEN** the API job MUST run on `ubuntu-latest` with `pgvector/pgvector:pg16` service
- **THEN** it MUST install dependencies with `uv sync`
- **THEN** it MUST run `ruff check`, `ruff format --check`, `mypy`, and `pytest --cov --cov-fail-under=80`

#### Scenario: Web E2E smoke CI job

- **WHEN** a pull request is opened
- **THEN** a separate E2E smoke job MUST run Playwright auth and health probe tests via Docker Compose
- **THEN** the smoke job MUST be a required status check blocking merge

#### Scenario: Type staleness gate

- **WHEN** the CI type-staleness job runs
- **THEN** it MUST regenerate the OpenAPI spec from Django
- **THEN** it MUST diff the generated spec against committed `packages/api-client/openapi.json`
- **THEN** if they differ, the job MUST fail with a message to run type generation locally
