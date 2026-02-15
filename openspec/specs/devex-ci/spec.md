## ADDED Requirements

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
