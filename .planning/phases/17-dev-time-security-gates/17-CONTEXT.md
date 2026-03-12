# Phase 17: Dev-Time Security Gates - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Add dev-time security gates: `detect-secrets` blocks secret commits in pre-commit + CI;
`bandit` blocks HIGH-severity Python security findings in pre-commit + CI;
`pip-audit` + `pnpm audit` block CRITICAL/HIGH dependency vulnerabilities as a CI merge gate;
`django-debug-toolbar` enables SQL query analysis locally in development (Django admin only).

No user-visible UI. No runtime behavior changes. All changes affect the developer workflow
and CI pipeline only.

Requirements: DEV-01, DEV-02, DEV-03, DEV-06.

</domain>

<decisions>
## Implementation Decisions

### detect-secrets

- **Baseline file:** Pre-scanned baseline committed to the repo — run `detect-secrets scan`
  on the template before commit. Known dev values (`POSTGRES_PASSWORD: postgres`,
  `SECRET_KEY: test-secret-key-for-ci` in CI yaml) are baselined and pass. New secrets
  not in the baseline fail at commit time.
- **Scaffolded projects:** Inherit the template's `.secrets.baseline` directly — dev values
  are already baselined, project works immediately. New secrets the project introduces
  fail until the developer runs `detect-secrets audit .secrets.baseline`.
- **Runs in:** Pre-commit (blocks locally) + CI (separate step to catch --no-verify pushes).
- **False positive handling:** Developer runs `detect-secrets audit .secrets.baseline` and
  marks the finding as a false positive. Baseline update is committed — reviewable in code
  review. No inline comments approach.

### bandit

- **Runs in:** Both pre-commit + CI. Pre-commit gives immediate feedback before push.
  CI re-runs to enforce at merge time.
- **Severity threshold:** HIGH severity only. MEDIUM and LOW findings appear in output
  but do not block commit or CI. Matches success criterion DEV-02.
- **Scope:** `apps/` directory only — excludes `tests/`. Tests intentionally use hardcoded
  credentials, unsafe patterns in factories, etc., which would generate noise.
- **False positive handling:** `# nosec B<RULE_ID>` inline comment on the specific line.
  Rule ID must be explicit (not bare `# nosec`) — reviewable in code review. No
  project-wide bandit.yaml exclusions in the template.

### pip-audit (Python dependency audit)

- **Severity threshold:** CRITICAL + HIGH blocks CI merge. MEDIUM and LOW are reported
  in CI output but do not block.
- **Runs in:** CI only (requires network to fetch OSV/PyPI advisories — not suitable for
  pre-commit offline workflow).
- **Escape hatch:** Template ships an empty `.pip-audit-ignore` (or equivalent
  `--ignore-vuln` list in the CI step). Projects populate it with CVE IDs + documented
  reason when upstream has not yet released a fix. Ignore entries are visible in CI config
  and code review.

### pnpm audit (JS/TS dependency audit)

- **Severity threshold:** `--audit-level high` — mirrors pip-audit. CRITICAL + HIGH blocks.
  Consistent story across both ecosystems.
- **Runs in:** CI only (requires network — same rationale as pip-audit).

### django-debug-toolbar

- **Where it renders:** Django admin only. DDT injects into HTML responses — in this
  API-first template, only Django admin views render HTML. SQL query analysis is the
  primary value, and admin views exercise the ORM adequately.
- **Panels:** All default DDT panels enabled (SQL, headers, request, static files,
  templates, signals, history). Easy to remove per-project; difficult to add if absent.
- **Configuration:** Django settings only — no docker-compose changes needed.
  Added to `INSTALLED_APPS` and `MIDDLEWARE` in `development.py` only.
  Absent from `test.py` and `production.py`.
- **No env var toggle:** No `DDT_ENABLED` env var — `development.py` is the toggle.

### Claude's Discretion

- Exact `.secrets.baseline` contents and which plugin types to enable in detect-secrets
  (e.g., `HexHighEntropyString`, `AWSKeyDetector`, etc.)
- CI job structure: whether audit runs as a separate job or as steps within the existing
  `api` job
- pip-audit ignore file format (CLI flags vs config file)
- DDT `SHOW_TOOLBAR_CALLBACK` configuration to restrict to `127.0.0.1` only
- DDT URL routing (`path('__debug__/', include(debug_toolbar.urls))`) in `urls.py`

</decisions>

<code_context>

## Existing Code Insights

### Reusable Assets

- `.pre-commit-config.yaml` already exists with ruff, lint-staged, pre-commit-hooks — add
  detect-secrets and bandit hooks to this file (do not create a new one)
- `.github/workflows/ci.yml` already has `api`, `web`, `mobile` jobs — add pip-audit and
  pnpm audit as steps within existing jobs or as a dedicated `security` job
- `apps/api/config/settings/development.py` — DDT goes here; already has dev-only settings
- `apps/api/config/settings/base.py` — bandit scope config (if using bandit.yaml ref)

### Established Patterns

- Pre-commit hooks are community repos (ruff uses `astral-sh/ruff-pre-commit`) or local
  hooks (lint-staged) — detect-secrets uses `Yelp/detect-secrets`, bandit uses
  `PyCQA/bandit` pre-commit hooks
- CI: `uv run <tool>` pattern for Python tools (ruff, mypy, pytest) — `uv run bandit` and
  `uv run pip-audit` follow the same pattern
- Settings: `INSTALLED_APPS` and `MIDDLEWARE` in `development.py` follow established
  per-environment override pattern from Phase 16 (HSTS dev/prod split)
- `apps/api/config/urls.py` already exists — DDT URL registration goes here under
  `if settings.DEBUG`

### Integration Points

- `.pre-commit-config.yaml` — detect-secrets + bandit hooks added to existing file
- `.github/workflows/ci.yml` — pip-audit step in `api` job; pnpm audit step in `web` or
  mobile job (or new dedicated `security` job)
- `apps/api/config/settings/development.py` — DDT `INSTALLED_APPS` + `MIDDLEWARE` entry
- `apps/api/config/urls.py` — DDT URL pattern under `if settings.DEBUG`
- `apps/api/pyproject.toml` — `bandit` and `pip-audit` added to dev dependencies

</code_context>

<specifics>
## Specific Ideas

No specific product references. Standard dev-time security tooling for a greenfield SaaS
template — decisions above represent conventional defaults for this Django/Next.js stack.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 17-dev-time-security-gates_
_Context gathered: 2026-03-11_
