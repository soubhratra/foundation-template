## Requirements

### Requirement: Backend Testing with pytest

The Django API SHALL use pytest with Django plugin for all backend tests, including endpoint, service, and model tests.

#### Scenario: API endpoint test with fixtures

- **WHEN** a developer tests the GET `/api/v1/users/me` endpoint
- **THEN** they MUST use the `authenticated_client` fixture from `conftest.py`
- **THEN** the test MUST send a request and assert HTTP 200 response
- **THEN** the test MUST verify response JSON contains expected user fields
- **THEN** the test function name MUST follow pattern `test_get_current_user_when_authenticated_returns_user_data`

#### Scenario: Database isolation via transactions

- **WHEN** a pytest test marked with `@pytest.mark.django_db` runs
- **THEN** it MUST run inside a database transaction
- **THEN** the transaction MUST roll back after the test completes
- **THEN** subsequent tests MUST NOT see any data from previous tests

### Requirement: Frontend Testing with vitest

Next.js and shared TypeScript packages SHALL use vitest with Testing Library for component and hook tests.

#### Scenario: Component test with user interaction

- **WHEN** testing a `LoginForm` component
- **THEN** the test MUST use `render()` from `@testing-library/react`
- **THEN** it MUST simulate user input with `fireEvent.change()` and `fireEvent.click()`
- **THEN** it MUST assert validation errors appear using `screen.getByText()`
- **THEN** it MUST use `waitFor()` for async validation

#### Scenario: API mocking with MSW

- **WHEN** a component test requires API responses
- **THEN** the test MUST use MSW (Mock Service Worker) handlers
- **THEN** handlers MUST be defined in `tests/mocks/handlers.ts`
- **THEN** MSW server MUST be configured in `vitest.setup.ts` with `beforeAll()`, `afterEach()`, and `afterAll()` lifecycle hooks

### Requirement: Mobile E2E Testing with Detox

The Expo app SHALL use Detox for end-to-end testing of critical user flows on iOS and Android.

#### Scenario: Authentication flow E2E test

- **WHEN** testing the full signup and login flow
- **THEN** the test MUST launch the app with `device.launchApp()`
- **THEN** it MUST tap elements using `element(by.id("signup-button")).tap()`
- **THEN** it MUST type text with `element(by.id("email-input")).typeText()`
- **THEN** it MUST verify screen visibility with `expect(element(by.id("dashboard-screen"))).toBeVisible()`

#### Scenario: Detox device configuration

- **WHEN** Detox runs in CI
- **THEN** iOS tests MUST use iPhone 15 simulator configured in `.detoxrc.js`
- **THEN** Android tests MUST use Pixel 7 API 34 emulator
- **THEN** tests MUST have a 120-second setup timeout

### Requirement: Test Orchestration with Turborepo

The monorepo SHALL use Turborepo to orchestrate tests across all workspaces in parallel.

#### Scenario: Running all tests via Turborepo

- **WHEN** a developer runs `pnpm test` from repository root
- **THEN** Turborepo MUST execute the `test` task for all workspaces
- **THEN** vitest MUST run for `apps/web`, `packages/api-client`, `packages/validation`, and `packages/ui`
- **THEN** pytest MUST run for `apps/api` via custom task configuration
- **THEN** tests MUST run in parallel without shared state

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

### Requirement: Coverage Thresholds

All test suites SHALL enforce minimum coverage thresholds that fail builds when not met.

#### Scenario: Backend coverage enforcement

- **WHEN** pytest runs with coverage
- **THEN** it MUST measure coverage of `apps/` directory only
- **THEN** coverage MUST be at least 80% line coverage
- **THEN** if coverage falls below 80%, the build MUST fail

#### Scenario: Frontend coverage enforcement

- **WHEN** vitest runs with coverage for web or shared packages
- **THEN** it MUST enforce 80% statement coverage and 70% branch coverage
- **THEN** if thresholds are not met, the build MUST fail

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
