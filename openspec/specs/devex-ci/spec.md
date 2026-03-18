## Requirements

### Requirement: Pre-Commit Hooks for Code Quality

The repository SHALL use pre-commit hooks to enforce linting and formatting before commits.

#### Scenario: Python pre-commit hooks with Ruff

- **WHEN** a developer attempts to commit Python code changes
- **THEN** the pre-commit hook MUST run `ruff check` on staged Python files
- **THEN** it MUST run `ruff format --check` on staged Python files
- **THEN** if any check fails, the commit MUST be blocked
- **THEN** the developer MUST fix issues before the commit succeeds

#### Scenario: JavaScript/TypeScript pre-commit hooks

- **WHEN** a developer attempts to commit TypeScript or JavaScript code changes
- **THEN** the pre-commit hook MUST run `eslint` on staged files
- **THEN** it MUST run `prettier --check` on staged files
- **THEN** if any check fails, the commit MUST be blocked

### Requirement: GitHub Actions CI with Parallel Jobs

CI SHALL run three parallel jobs for API, web, and mobile workspaces to maximize build speed.

#### Scenario: API job execution

- **WHEN** a pull request is opened or updated
- **THEN** the API job MUST run on `ubuntu-latest` runner
- **THEN** it MUST start a `pgvector/pgvector:pg16` PostgreSQL service container
- **THEN** it MUST install dependencies with `uv sync`
- **THEN** it MUST run linting, formatting, type checking, and tests sequentially

#### Scenario: Web job execution

- **WHEN** a pull request is opened or updated
- **THEN** the web job MUST run on `ubuntu-latest` runner
- **THEN** it MUST install pnpm dependencies with `pnpm install --frozen-lockfile`
- **THEN** it MUST run `pnpm turbo lint --filter=web...`
- **THEN** it MUST run `pnpm turbo type-check --filter=web...`
- **THEN** it MUST run `pnpm turbo test --filter=web...`
- **THEN** it MUST run `pnpm turbo build --filter=web` to verify production build succeeds

#### Scenario: Mobile job execution

- **WHEN** a pull request is opened or updated
- **THEN** the mobile job MUST run on `ubuntu-latest` runner
- **THEN** it MUST run `pnpm turbo lint --filter=mobile...`
- **THEN** it MUST run `pnpm turbo type-check --filter=mobile...`
- **THEN** Detox E2E tests MUST NOT run (reserved for merge to main on macOS runners)

### Requirement: Type Staleness CI Gate

CI SHALL verify that committed TypeScript types match the current Django OpenAPI spec to prevent type drift.

#### Scenario: Type staleness check

- **WHEN** the type-staleness CI job runs
- **THEN** it MUST start a PostgreSQL service container
- **THEN** it MUST run `uv run python manage.py export_openapi_schema > /tmp/openapi.json`
- **THEN** it MUST run `diff /tmp/openapi.json packages/api-client/openapi.json`
- **THEN** if the diff is non-empty, the job MUST fail with message "OpenAPI spec is out of sync. Run type generation locally."

### Requirement: Production Dockerfiles with Multi-Stage Builds

The system SHALL provide production Dockerfiles for Django API and Next.js web app with optimized multi-stage builds.

#### Scenario: Django production Docker build

- **WHEN** building the Django API Docker image for production
- **THEN** the Dockerfile MUST use a multi-stage build with separate builder and runtime stages
- **THEN** the builder stage MUST install dependencies with `uv sync`
- **THEN** the runtime stage MUST copy only the installed dependencies and application code
- **THEN** the image MUST run gunicorn with multiple workers

#### Scenario: Next.js production Docker build

- **WHEN** building the Next.js web app Docker image for production
- **THEN** the Dockerfile MUST use a multi-stage build with dependencies, builder, and runner stages
- **THEN** it MUST install production dependencies only with `pnpm install --frozen-lockfile --prod`
- **THEN** it MUST run `pnpm build` to generate optimized static assets
- **THEN** the runtime stage MUST run `next start` with NODE_ENV=production

### Requirement: Type Checking with mypy and tsc

The CI pipeline SHALL enforce static type checking for Python with mypy and TypeScript with tsc.

#### Scenario: Python type checking with mypy

- **WHEN** the API CI job runs
- **THEN** it MUST execute `uv run mypy .` on the Django codebase
- **THEN** mypy MUST be configured in `pyproject.toml` with strict mode
- **THEN** if type errors are found, the build MUST fail

#### Scenario: TypeScript type checking with tsc

- **WHEN** the web or mobile CI job runs
- **THEN** it MUST execute `pnpm turbo type-check` which runs `tsc --noEmit`
- **THEN** if type errors are found in any workspace, the build MUST fail

### Requirement: Turborepo Caching for Fast Builds

Turborepo SHALL cache task outputs to speed up local and CI builds by avoiding redundant work.

#### Scenario: Local Turborepo cache hit

- **WHEN** a developer runs `pnpm turbo test` locally
- **THEN** Turborepo MUST check the local cache for previous test results
- **THEN** if source files and dependencies have not changed, it MUST return cached results
- **THEN** the test task MUST skip re-execution

#### Scenario: CI Turborepo cache with GitHub Actions

- **WHEN** a CI job runs with Turborepo
- **THEN** it SHOULD use `actions/cache` to persist Turborepo cache between runs
- **THEN** subsequent CI runs with unchanged code MUST retrieve cached task outputs
- **THEN** build time MUST decrease for incremental changes

### Requirement: Secret Scanning in Pre-Commit and CI

The repository SHALL use `detect-secrets` to prevent credentials from being committed, with a committed baseline file tracking known false positives.

#### Scenario: detect-secrets pre-commit hook blocks new secrets

- **WHEN** a developer attempts to commit a file containing a string that matches a secret pattern (API key, password, token)
- **THEN** the `detect-secrets` pre-commit hook MUST block the commit
- **AND** the developer MUST either remove the secret or audit it into `.secrets.baseline`

#### Scenario: .secrets.baseline committed to repository

- **WHEN** the repository is initialized
- **THEN** a `.secrets.baseline` file MUST exist at the repository root
- **AND** it MUST list any known false positives so they are not re-flagged
- **AND** the baseline MUST be kept current as new false positives are audited

#### Scenario: detect-secrets runs in CI on every PR

- **WHEN** a pull request is opened or updated
- **THEN** the CI pipeline MUST run `detect-secrets scan --baseline .secrets.baseline`
- **AND** if new unaudited secrets are found, the CI job MUST fail
- **AND** the failure message MUST instruct the developer to run `detect-secrets audit .secrets.baseline` locally

### Requirement: Python SAST with Bandit

The CI pipeline SHALL run `bandit` static application security testing on the Django codebase at HIGH severity, failing the build on any HIGH-confidence findings.

#### Scenario: Bandit runs on Python source

- **WHEN** the API CI job runs
- **THEN** it MUST execute `uv run bandit -r apps/ -ll -ii` (HIGH severity + HIGH confidence)
- **AND** if any HIGH severity issues are found, the CI job MUST fail
- **AND** the output MUST include file path, line number, and issue description

#### Scenario: Bandit also runs as pre-commit hook

- **WHEN** a developer commits Python files
- **THEN** the `bandit` pre-commit hook MUST run on staged `.py` files
- **AND** HIGH severity findings MUST block the commit

### Requirement: N+1 Query Detection with nplusone

The pytest test suite SHALL detect N+1 database query patterns automatically using an autouse `nplusone` fixture.

#### Scenario: nplusone autouse fixture active in all tests

- **WHEN** any pytest test runs that executes database queries
- **THEN** the `nplusone` fixture MUST be active without explicit opt-in
- **AND** if the test triggers an N+1 query pattern, `nplusone` MUST raise `NPlusOneError`
- **AND** the test MUST fail with a message identifying the relationship causing the N+1

#### Scenario: Intentional N+1 explicitly suppressed

- **WHEN** a developer has a legitimate reason to allow an N+1 query in a test
- **THEN** they MUST use the `@allow_lazy_load` decorator imported from `nplusone.ext.pytest`
- **AND** the suppression MUST be scoped to the minimum necessary test function

### Requirement: API Contract Fuzzing with Schemathesis

The CI pipeline SHALL run `schemathesis` as a fourth parallel job to fuzz all Django Ninja API endpoints against the OpenAPI spec.

#### Scenario: Schemathesis CI job runs against live API

- **WHEN** the schemathesis CI job runs
- **THEN** it MUST start a PostgreSQL service container and run Django with `runserver`
- **AND** it MUST execute `schemathesis run <openapi-url> --checks all`
- **AND** if any endpoint returns an unexpected 5xx response for a schema-valid input, the job MUST fail

#### Scenario: Schemathesis runs in parallel with other CI jobs

- **WHEN** a pull request is opened or updated
- **THEN** the schemathesis job MUST run concurrently with (not after) the API, web, and mobile jobs
- **AND** it MUST NOT block other jobs from starting

### Requirement: Conventional Commit Enforcement with commitlint

The repository SHALL enforce the Conventional Commits format on all commit messages using a `commit-msg` pre-commit hook powered by `commitlint`.

#### Scenario: Non-conventional commit message blocked

- **WHEN** a developer writes a commit message that does not start with a valid type prefix (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`, `ci`, `build`, `revert`)
- **THEN** the `commitlint` commit-msg hook MUST block the commit
- **AND** the error MUST display the allowed types and the correct format

#### Scenario: commitlint activation requires explicit install step

- **WHEN** a developer clones the repository and runs `pre-commit install`
- **THEN** they MUST also run `pre-commit install --hook-type commit-msg` to activate the commit-msg stage
- **AND** `DEV_SETUP.md` MUST document both install commands explicitly

### Requirement: Cyclomatic Complexity Gate with Ruff C90

The CI pipeline and pre-commit hooks SHALL enforce a maximum cyclomatic complexity of 10 on all Python functions using Ruff's McCabe complexity checker.

#### Scenario: Function exceeding complexity threshold blocked

- **WHEN** a Python function has a McCabe cyclomatic complexity greater than 10
- **THEN** `ruff check` MUST report a `C901` violation
- **AND** the pre-commit hook MUST block the commit
- **AND** the CI API linting step MUST fail

#### Scenario: Ruff C90 configured in pyproject.toml

- **WHEN** the repository is initialized
- **THEN** `pyproject.toml` MUST include `[tool.ruff.lint.mccabe]` with `max-complexity = 10`
- **AND** `"C90"` MUST be listed in `[tool.ruff.lint] select`
