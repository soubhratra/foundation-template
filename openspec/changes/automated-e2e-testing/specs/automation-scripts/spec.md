## ADDED Requirements

### Requirement: API test runner script

The template SHALL provide `scripts/run-api-tests.sh` as the single entrypoint for executing the full pytest suite and producing a structured failure report.

#### Scenario: Successful run produces no FAILURES.md

- **WHEN** all pytest tests pass
- **THEN** the script exits with code 0
- **THEN** no `test-results/FAILURES.md` file is written (or it contains an empty failures section)

#### Scenario: Failed run writes FAILURES.md with structured rows

- **WHEN** one or more pytest tests fail
- **THEN** the script exits with code 1
- **THEN** `test-results/FAILURES.md` is written containing a markdown table
- **THEN** the table MUST have columns: `Test`, `File`, `Assertion`, `Requirements`, `Status`
- **THEN** each failed test occupies exactly one row
- **THEN** the `Requirements` column lists all `@pytest.mark.req()` IDs for that test, comma-separated
- **THEN** the file begins with a timestamp header in ISO 8601 format

#### Scenario: Script works without pre-existing test-results directory

- **WHEN** `test-results/` does not exist
- **THEN** the script creates it before writing
- **THEN** the script does NOT fail with a "directory not found" error

### Requirement: E2E test runner script

The template SHALL provide `scripts/run-e2e-tests.sh` as the single entrypoint for executing the Playwright suite against a configurable target URL.

#### Scenario: Run against local dev server

- **WHEN** `BASE_URL` environment variable is unset
- **THEN** the script defaults to `http://localhost:3000`
- **THEN** the Playwright suite runs against that URL

#### Scenario: Run against a deployed URL

- **WHEN** `BASE_URL=https://staging.example.com` is set
- **THEN** the script passes `BASE_URL` to Playwright without modification
- **THEN** the same test files run unchanged — no conditional branches in test code

#### Scenario: Failed E2E run writes FAILURES.md

- **WHEN** one or more Playwright tests fail
- **THEN** `test-results/FAILURES.md` is written in the same format as the API failure report
- **THEN** the `Requirements` column lists `// @spec:` IDs from each failing test file
- **THEN** the `File` column includes the filename and line number of the failing `expect()`

### Requirement: Combined test runner script

The template SHALL provide `scripts/run-all-tests.sh` that executes both API and E2E suites and merges results into a single `test-results/FAILURES.md`.

#### Scenario: Dev mode run produces merged FAILURES.md

- **WHEN** `scripts/run-all-tests.sh --mode=dev` is executed
- **THEN** both `run-api-tests.sh` and `run-e2e-tests.sh` are invoked in sequence
- **THEN** failures from both suites are merged into a single `test-results/FAILURES.md`
- **THEN** the merged report includes a section header distinguishing API failures from E2E failures

#### Scenario: CI mode run exits non-zero on any failure

- **WHEN** `scripts/run-all-tests.sh --mode=ci` is executed
- **THEN** if any test from either suite fails, the script exits with code 1
- **THEN** `test-results/FAILURES.md` is still written before exiting

### Requirement: Requirement coverage checker

The template SHALL provide `scripts/check-req-coverage.py` that produces a per-requirement coverage table for all v1.1–v1.4 requirement IDs.

#### Scenario: All requirements covered

- **WHEN** every requirement ID found in ROADMAP.md has at least one matching `@pytest.mark.req()` or `// @spec:` marker in the test files
- **THEN** the script exits with code 0
- **THEN** output shows a table with all requirements marked `covered`

#### Scenario: Uncovered requirements detected

- **WHEN** one or more requirement IDs from ROADMAP.md have no matching test marker
- **THEN** the script exits with code 1
- **THEN** output table marks those requirements as `uncovered`
- **THEN** the script prints a count: `N requirements uncovered`

#### Scenario: Partial coverage detected

- **WHEN** a requirement ID appears in only one test file (not all relevant test files)
- **THEN** the script marks it as `partial` in the output table
- **THEN** partial counts toward coverage (does not cause non-zero exit)

#### Scenario: Source of requirement IDs

- **WHEN** the script runs
- **THEN** it reads requirement IDs from ROADMAP.md by scanning lines matching `Requirements: ` within phase blocks
- **THEN** it scans all `apps/api/tests/**/*.py` files for `@pytest.mark.req()` markers
- **THEN** it scans all `apps/web/tests/e2e/**/*.ts` files for `// @spec:` comments
