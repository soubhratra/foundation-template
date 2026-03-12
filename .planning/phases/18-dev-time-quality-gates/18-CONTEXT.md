# Phase 18: Dev-Time Quality Gates - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Add four dev-time quality gates to the template:

- `nplusone` — N+1 query detection as an autouse pytest fixture that fails tests automatically
- `schemathesis` — API contract fuzzing as a separate CI job against the live Django test server
- `commitlint` (conventional-pre-commit) — Conventional Commits enforcement as a pre-commit hook
- ruff McCabe complexity gate — C901 rule blocking functions exceeding complexity 10 in pre-commit + CI

No user-visible UI. No runtime behavior changes. All changes affect developer workflow and
CI pipeline only.

Requirements: DEV-04, DEV-05, DEV-07, DEV-08.

</domain>

<decisions>
## Implementation Decisions

### nplusone — N+1 detection fixture

- **Autouse scope:** `autouse=True` globally — single fixture in `apps/api/conftest.py`
  (root conftest). Applies to all pytest tests. Regressions cannot sneak in anywhere.
- **Failure mode:** Raise immediately on first detected N+1 (default NPlusOneError).
  No collect-and-report — fastest feedback, clearest error message.
- **Exception handling:** `@allow_lazy_load` decorator (nplusone API) on specific tests
  that intentionally trigger N+1s. Inline on the test function — visible in code review,
  no project-wide allowlists in settings.
- **Location:** `apps/api/conftest.py` — already exists, is the right root conftest for
  the api app's test suite.

### schemathesis — API contract fuzzing

- **Integration mode:** CLI tool (`schemathesis run`), NOT the pytest plugin
  (@schema.parametrize). Matches "CI job runs schemathesis against the live Django test
  server" wording in success criterion.
- **CI placement:** Separate `schemathesis` CI job in `.github/workflows/ci.yml`. Keeps
  the existing `api` job (unit + integration tests) fast. Fuzzing runs independently.
- **Endpoint coverage:** All endpoints in the OpenAPI spec by default. Use `--exclude-path`
  flags for endpoints not suitable for fuzzing (e.g., `/api/billing/webhook/`,
  health probes at `/api/health/`).
- **Spec source:** Live server endpoint — `http://localhost:8000/api/openapi.json`.
  Always in sync with the code; no committed schema file to maintain.
- **Server startup:** CI job starts `manage.py runserver` in the background, waits for
  it to be ready, then runs `schemathesis run`.

### commitlint — Conventional Commits enforcement

- **Tool:** `conventional-pre-commit` (Python-based, `compilerla/conventional-pre-commit`).
  No extra Node/npm setup. Consistent with the existing pre-commit hook pattern
  (detect-secrets, bandit) already in `.pre-commit-config.yaml`.
- **Stage:** `stages: [commit-msg]` — hooks on the commit message, not on staged files.
- **Allowed types:** Standard Conventional Commits set:
  `feat, fix, docs, refactor, test, chore, perf, ci, build, revert`
  (plus `style` is excluded — ruff handles formatting, not commits).
- **Config location:** Entirely in `.pre-commit-config.yaml` args — no separate
  commitlint.config.js or package.json entry needed.

### ruff McCabe complexity gate

- **Config location:** `pyproject.toml` `[tool.ruff.lint]` section. The existing pre-commit
  ruff hook reads pyproject.toml automatically — no changes to `.pre-commit-config.yaml`
  needed.
- **Rule set:** Add `[tool.ruff.lint]` with `select = ["E", "F", "C90"]` to make McCabe
  checking explicit alongside existing E/F rules.
- **Threshold:** `[tool.ruff.lint.mccabe]` `max-complexity = 10` (matches success
  criterion DEV-08 exactly).
- **CI enforcement:** The existing `uv run ruff check .` step in the `api` CI job picks
  up C90 automatically from pyproject.toml — no CI config changes needed beyond
  pyproject.toml.

### Claude's Discretion

- Exact schemathesis CLI flags (`--max-response-time`, `--checks all`, stateful testing)
- Which paths get `--exclude-path` beyond webhooks + health probes
- nplusone fixture function name and NPLUSONE_RAISE settings key if needed
- Whether schemathesis CI job shares the postgres service container or uses SQLite
- TDD wave 0 stub structure (mirrors Phases 16-01 and 17-01 patterns)

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/api/conftest.py` — already exists; nplusone autouse fixture goes here alongside
  existing fixtures
- `.pre-commit-config.yaml` — already has ruff, detect-secrets, bandit hooks; add
  conventional-pre-commit as a new entry (commit-msg stage)
- `.github/workflows/ci.yml` — has `api` and `web` jobs; add `schemathesis` as a third
  top-level job
- `apps/api/pyproject.toml` — has `[tool.pytest.ini_options]` and `[tool.mypy]` but no
  `[tool.ruff.lint]` section yet; C90 config goes here

### Established Patterns

- **TDD wave 0:** pytest.fail() RED stubs in a dedicated test file before implementation
  (Phases 16-01 and 17-01 both use this pattern exactly)
- **Pre-commit hooks:** Community repos with `rev` pinned (astral-sh, Yelp, PyCQA pattern)
  — conventional-pre-commit follows the same pattern
- **CI Python steps:** `uv run <tool>` pattern — `uv run ruff check .` already handles
  C90 once pyproject.toml is updated
- **Dev-only settings:** `development.py` is the toggle for dev-only tools (DDT pattern
  from Phase 17 confirmed)
- **Phase 17 gate structure:** bandit (pre-commit + CI), detect-secrets (pre-commit + CI),
  pip-audit (CI only) — nplusone is pytest-only, schemathesis is CI-only

### Integration Points

- `apps/api/conftest.py` — nplusone autouse fixture registration
- `.pre-commit-config.yaml` — conventional-pre-commit hook (commit-msg stage)
- `apps/api/pyproject.toml` — `[tool.ruff.lint]` section with C90 + max-complexity = 10
- `.github/workflows/ci.yml` — new `schemathesis` job; ruff CI step picks up C90 from
  pyproject.toml automatically
- `apps/api/pyproject.toml` `[project.dependencies]` — `nplusone` as runtime dep;
  `schemathesis` as dev dep

</code_context>

<specifics>
## Specific Ideas

No specific product references. Standard dev-time quality tooling decisions for a
Django/Next.js SaaS template — all choices above follow conventional defaults for
this stack.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 18-dev-time-quality-gates_
_Context gathered: 2026-03-11_
