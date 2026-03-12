## ADDED Requirements

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
- **THEN** they MUST use `with nplusone_app.ignore(model="MyModel", field="relation"):` context manager
- **AND** the suppression MUST be scoped to the minimum necessary code block

### Requirement: API Contract Fuzzing with Schemathesis

The CI pipeline SHALL run `schemathesis` as a fourth parallel job to fuzz all Django Ninja API endpoints against the OpenAPI spec.

#### Scenario: Schemathesis CI job runs against live API

- **WHEN** the schemathesis CI job runs
- **THEN** it MUST start a PostgreSQL service container and run Django with `runserver`
- **AND** it MUST execute `schemathesis run /api/schema.json --checks all`
- **AND** if any endpoint returns an unexpected 5xx response for a schema-valid input, the job MUST fail

#### Scenario: Schemathesis runs in parallel with other CI jobs

- **WHEN** a pull request is opened or updated
- **THEN** the schemathesis job MUST run concurrently with (not after) the API, web, and mobile jobs
- **AND** it MUST NOT block other jobs from starting

### Requirement: Conventional Commit Enforcement with commitlint

The repository SHALL enforce the Conventional Commits format on all commit messages using a `commit-msg` pre-commit hook powered by `commitlint`.

#### Scenario: Valid conventional commit accepted

- **WHEN** a developer writes a commit message following the pattern `type(scope): description`
- **THEN** the `commitlint` hook MUST pass
- **AND** the commit MUST proceed

#### Scenario: Non-conventional commit message blocked

- **WHEN** a developer writes a commit message that does not start with a valid type prefix (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`, `perf`, `ci`, `build`, `revert`)
- **THEN** the `commitlint` commit-msg hook MUST block the commit
- **AND** the error MUST display the allowed types and the correct format

#### Scenario: commitlint configured in repo root

- **WHEN** the repository is initialized
- **THEN** a `commitlint.config.js` (or equivalent) MUST exist at the repository root
- **AND** it MUST extend `@commitlint/config-conventional`
- **AND** the `.pre-commit-config.yaml` MUST include a `commit-msg` stage entry for `commitlint`

### Requirement: Cyclomatic Complexity Gate with Ruff C90

The CI pipeline and pre-commit hooks SHALL enforce a maximum cyclomatic complexity of 10 on all Python functions using Ruff's McCabe complexity checker.

#### Scenario: Function exceeding complexity threshold blocked

- **WHEN** a Python function has a McCabe cyclomatic complexity greater than 10
- **THEN** `ruff check` MUST report a `C901` violation
- **AND** the pre-commit hook MUST block the commit
- **AND** the CI API linting step MUST fail

#### Scenario: Ruff C90 configured in pyproject.toml

- **WHEN** the repository is initialized
- **THEN** `pyproject.toml` MUST include `[tool.ruff.mccabe]` with `max-complexity = 10`
- **AND** `"C90"` MUST be listed in `[tool.ruff.lint] select`
