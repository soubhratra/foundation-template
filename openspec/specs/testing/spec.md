## ADDED Requirements

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
CI SHALL run three parallel jobs for API, web, and mobile with type staleness verification.

#### Scenario: API CI job
- **WHEN** a pull request is opened
- **THEN** the API job MUST run on `ubuntu-latest` with `pgvector/pgvector:pg16` service
- **THEN** it MUST install dependencies with `uv sync`
- **THEN** it MUST run `ruff check`, `ruff format --check`, `mypy`, and `pytest --cov --cov-fail-under=80`

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
