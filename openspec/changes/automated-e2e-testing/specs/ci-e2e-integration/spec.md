## ADDED Requirements

### Requirement: Nightly E2E GitHub Actions workflow

The template SHALL include a GitHub Actions workflow file `e2e-nightly.yml` that runs the full Playwright suite on a schedule and auto-creates a GitHub issue on failure.

#### Scenario: Nightly schedule trigger

- **WHEN** the scheduled cron expression fires (2am UTC daily)
- **THEN** the `e2e-nightly.yml` workflow MUST start automatically
- **THEN** no manual trigger is required

#### Scenario: Environment setup sequence

- **WHEN** the nightly workflow runs
- **THEN** it MUST execute in order: `docker compose up -d` → wait for health ready → `python manage.py migrate` → seed test users → `scripts/run-e2e-tests.sh`
- **THEN** the workflow MUST fail if any step in the sequence fails before reaching the test run

#### Scenario: FAILURES.md uploaded as artifact

- **WHEN** the nightly workflow completes (pass or fail)
- **THEN** `test-results/FAILURES.md` MUST be uploaded as a GitHub Actions artifact named `e2e-failures`
- **THEN** the artifact MUST be retained for 7 days

#### Scenario: Auto-issue creation on failure

- **WHEN** the nightly E2E suite has one or more failures
- **THEN** the workflow MUST open a GitHub issue using `gh issue create`
- **THEN** the issue body MUST include: run date, link to the failed workflow run, and a link to the uploaded `FAILURES.md` artifact
- **THEN** the issue MUST be labeled `e2e-failure` and `automated`

#### Scenario: No duplicate issues when already open

- **WHEN** a `e2e-failure` labeled issue is already open
- **THEN** the workflow MUST NOT open a duplicate issue
- **THEN** it MAY add a comment to the existing open issue instead

#### Scenario: Docker Compose teardown on completion

- **WHEN** the nightly workflow completes (pass or fail)
- **THEN** `docker compose down -v` MUST run in a `always()` step to clean up volumes
- **THEN** no persistent Docker state remains for the next nightly run

### Requirement: PR E2E smoke job

The existing `ci.yml` PR workflow SHALL include an E2E smoke job that runs auth and health probe tests and blocks merge on failure.

#### Scenario: Smoke job runs on every PR

- **WHEN** a pull request is opened or updated against the main branch
- **THEN** the E2E smoke job MUST run as part of the CI matrix
- **THEN** the smoke job result MUST be a required status check (blocks merge if failing)

#### Scenario: Smoke job scope

- **WHEN** the PR smoke job runs
- **THEN** it MUST execute ONLY the auth flow tests and health probe tests (subset of full E2E suite)
- **THEN** it MUST NOT run the full billing, B2B, or social auth suites (reserved for nightly)

#### Scenario: Smoke job runtime target

- **WHEN** the smoke job runs
- **THEN** it MUST complete within 3 minutes wall-clock time in GitHub Actions
- **THEN** if the job exceeds 5 minutes, it MUST be considered a flake and retried once automatically

#### Scenario: Smoke job environment

- **WHEN** the smoke job runs
- **THEN** it MUST start Docker Compose, run migrations, and seed a test user before running Playwright
- **THEN** `BASE_URL` MUST point to the Docker Compose web container

### Requirement: FAILURES.md CI artifact

Both the nightly and PR smoke workflows SHALL upload a `FAILURES.md` artifact that Claude can retrieve and act on autonomously.

#### Scenario: FAILURES.md format is Claude-parseable

- **WHEN** a workflow uploads `FAILURES.md`
- **THEN** the file MUST use the markdown table format defined in the `automation-scripts` spec
- **THEN** the `Requirements` column MUST be populated for every failed test

#### Scenario: Empty FAILURES.md on passing run

- **WHEN** all tests pass
- **THEN** `FAILURES.md` MUST still be uploaded as an artifact
- **THEN** its content MUST indicate zero failures (e.g., an empty table with headers only, or a "All tests passed" line)
