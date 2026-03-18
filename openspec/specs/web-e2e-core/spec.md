## Requirements

### Requirement: Playwright configuration

The web app SHALL have a `playwright.config.ts` at `apps/web/playwright.config.ts` that supports both local and remote target URLs without code changes.

#### Scenario: Default local target

- **WHEN** `BASE_URL` environment variable is not set
- **THEN** Playwright uses `http://localhost:3000` as `baseURL`

#### Scenario: Remote target via env var

- **WHEN** `BASE_URL=https://staging.example.com` is set
- **THEN** Playwright uses that URL as `baseURL` without any config file changes

#### Scenario: Test isolation via storage state

- **WHEN** a Playwright test begins
- **THEN** it starts with a fresh browser context (no cookies or local storage from previous tests)
- **THEN** any auth state is established within the test's own `beforeAll` or `beforeEach` block

### Requirement: E2E auth flow tests

The Playwright suite SHALL include tests for the complete authentication flow.

#### Scenario: Signup redirects to dashboard

- **WHEN** a new user completes the signup form with a unique email and valid password
- **THEN** the browser MUST redirect to the dashboard page
- **THEN** the dashboard MUST display the user's email or name

#### Scenario: Login with valid credentials

- **WHEN** an existing user submits the login form with correct credentials
- **THEN** the browser MUST redirect to the dashboard page
- **THEN** the session cookie MUST be set

#### Scenario: Login with invalid credentials shows inline error

- **WHEN** a user submits the login form with an incorrect password
- **THEN** the browser MUST NOT redirect
- **THEN** an inline error message MUST appear on the login page within 2 seconds
- **THEN** the error MUST NOT expose whether the email exists

#### Scenario: Logout clears session and redirects

- **WHEN** an authenticated user clicks the logout button
- **THEN** the session cookie MUST be cleared
- **THEN** the browser MUST redirect to the login page

### Requirement: E2E GDPR data export test

The Playwright suite SHALL include a test that exercises the GDPR data export UI button, closing the v1.3 audit gap where the export endpoint existed but had no frontend E2E coverage.

#### Scenario: Download my data button triggers file download

- **WHEN** an authenticated user navigates to the settings page
- **THEN** a "Download my data" button MUST be visible
- **WHEN** the user clicks "Download my data"
- **THEN** a file download MUST be initiated within 5 seconds
- **THEN** the downloaded file MUST be valid JSON

#### Scenario: Export API fallback assertion

- **WHEN** the browser download cannot be captured due to sandbox restrictions
- **THEN** the test MUST assert that `GET /api/v1/account/export` returns HTTP 200 and `Content-Type: application/json` using Playwright's `request` context

### Requirement: E2E billing display tests

The Playwright suite SHALL include tests verifying the billing page renders correctly for an authenticated user.

#### Scenario: Plan cards visible on billing page

- **WHEN** an authenticated user navigates to `/billing`
- **THEN** at least one plan card MUST be visible on the page
- **THEN** each plan card MUST display a plan name and price

#### Scenario: Current plan badge visible

- **WHEN** an authenticated user with an active subscription navigates to `/billing`
- **THEN** a "Current plan" badge or indicator MUST appear on the active plan card

#### Scenario: Upgrade CTA links to Stripe

- **WHEN** an authenticated user on the free plan views the billing page
- **THEN** an upgrade call-to-action MUST be present
- **THEN** clicking it MUST initiate a redirect to a Stripe-hosted URL (starting with `https://checkout.stripe.com` or `https://billing.stripe.com`)

### Requirement: E2E health probe API tests

The Playwright suite SHALL include tests that assert the three health endpoints return HTTP 200 via direct API calls (not browser navigation).

#### Scenario: Liveness probe returns 200

- **WHEN** a GET request is made to `/api/health/live` using Playwright `request` context
- **THEN** the response status MUST be 200

#### Scenario: Readiness probe returns 200

- **WHEN** a GET request is made to `/api/health/ready` using Playwright `request` context
- **THEN** the response status MUST be 200

#### Scenario: Startup probe returns 200

- **WHEN** a GET request is made to `/api/health/startup` using Playwright `request` context
- **THEN** the response status MUST be 200

### Requirement: E2E self-seeding fixtures

All Playwright tests SHALL create their own test data via API calls and clean up after themselves — no pre-existing database state is assumed.

#### Scenario: Test user created before suite

- **WHEN** a Playwright test suite begins
- **THEN** a test user MUST be created via a Django management command or seed API before browser interaction starts
- **THEN** the test user credentials MUST be stored in environment variables accessible to the test

#### Scenario: Test data cleaned up after suite

- **WHEN** a Playwright test suite completes (pass or fail)
- **THEN** any data created by the suite MUST be deleted via API DELETE calls in `afterAll`
- **THEN** the database MUST be in the same state as before the suite ran
