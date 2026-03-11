# Phase 17: Dev-Time Security Gates - Research

**Researched:** 2026-03-11
**Domain:** Dev-time security tooling — detect-secrets, bandit, pip-audit, pnpm audit, django-debug-toolbar
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**detect-secrets**

- Baseline file: Pre-scanned baseline committed to repo — run `detect-secrets scan` on the template before commit. Known dev values (`POSTGRES_PASSWORD: postgres`, `SECRET_KEY: test-secret-key-for-ci` in CI yaml) are baselined and pass. New secrets not in the baseline fail at commit time.
- Scaffolded projects: Inherit the template's `.secrets.baseline` directly — dev values are already baselined, project works immediately. New secrets the project introduces fail until the developer runs `detect-secrets audit .secrets.baseline`.
- Runs in: Pre-commit (blocks locally) + CI (separate step to catch --no-verify pushes).
- False positive handling: Developer runs `detect-secrets audit .secrets.baseline` and marks the finding as a false positive. Baseline update is committed — reviewable in code review. No inline comments approach.

**bandit**

- Runs in: Both pre-commit + CI. Pre-commit gives immediate feedback before push. CI re-runs to enforce at merge time.
- Severity threshold: HIGH severity only. MEDIUM and LOW findings appear in output but do not block commit or CI. Matches success criterion DEV-02.
- Scope: `apps/` directory only — excludes `tests/`. Tests intentionally use hardcoded credentials, unsafe patterns in factories, etc., which would generate noise.
- False positive handling: `# nosec B<RULE_ID>` inline comment on the specific line. Rule ID must be explicit (not bare `# nosec`) — reviewable in code review. No project-wide bandit.yaml exclusions in the template.

**pip-audit (Python dependency audit)**

- Severity threshold: CRITICAL + HIGH blocks CI merge. MEDIUM and LOW are reported in CI output but do not block.
- Runs in: CI only (requires network to fetch OSV/PyPI advisories — not suitable for pre-commit offline workflow).
- Escape hatch: Template ships an empty `.pip-audit-ignore` (or equivalent `--ignore-vuln` list in the CI step). Projects populate it with CVE IDs + documented reason when upstream has not yet released a fix. Ignore entries are visible in CI config and code review.

**pnpm audit (JS/TS dependency audit)**

- Severity threshold: `--audit-level high` — mirrors pip-audit. CRITICAL + HIGH blocks. Consistent story across both ecosystems.
- Runs in: CI only (requires network — same rationale as pip-audit).

**django-debug-toolbar**

- Where it renders: Django admin only. DDT injects into HTML responses — in this API-first template, only Django admin views render HTML. SQL query analysis is the primary value, and admin views exercise the ORM adequately.
- Panels: All default DDT panels enabled (SQL, headers, request, static files, templates, signals, history). Easy to remove per-project; difficult to add if absent.
- Configuration: Django settings only — no docker-compose changes needed. Added to `INSTALLED_APPS` and `MIDDLEWARE` in `development.py` only. Absent from `test.py` and `production.py`.
- No env var toggle: No `DDT_ENABLED` env var — `development.py` is the toggle.

### Claude's Discretion

- Exact `.secrets.baseline` contents and which plugin types to enable in detect-secrets (e.g., `HexHighEntropyString`, `AWSKeyDetector`, etc.)
- CI job structure: whether audit runs as a separate job or as steps within the existing `api` job
- pip-audit ignore file format (CLI flags vs config file)
- DDT `SHOW_TOOLBAR_CALLBACK` configuration to restrict to `127.0.0.1` only
- DDT URL routing (`path('__debug__/', include(debug_toolbar.urls))`) in `urls.py`

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                                                        | Research Support                                                                                                       |
| ------ | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| DEV-01 | Secrets are blocked at commit time and fail CI via `detect-secrets` pre-commit hook + CI step                      | detect-secrets 1.5.0 pre-commit hook via `Yelp/detect-secrets`, CI step via `uv run detect-secrets` or standalone scan |
| DEV-02 | Python security issues flagged at commit time and in CI via `bandit` pre-commit hook + CI step                     | bandit 1.9.4 pre-commit hook via `PyCQA/bandit`, `-lll` flag for HIGH-only, `-x tests/` exclusion                      |
| DEV-03 | Known-vulnerable Python and JS dependencies block CI merge via `pip-audit` + `pnpm audit` gate                     | pip-audit 2.10.0 with `--ignore-vuln` escape hatch; pnpm audit with `--audit-level high`                               |
| DEV-06 | Developer can analyze SQL queries, cache hits, and request profiling locally via `django-debug-toolbar` (dev only) | django-debug-toolbar 6.2.0, development.py only, INTERNAL_IPS restriction                                              |

</phase_requirements>

---

## Summary

Phase 17 adds four dev-time security gates — none affect runtime behavior in production. All four tools have stable, well-maintained pre-commit hooks and CI integrations. The implementation is mechanical: add hooks to `.pre-commit-config.yaml`, add steps to `.github/workflows/ci.yml`, add a package dependency to `pyproject.toml`, and configure `development.py` for DDT.

The one significant design constraint to internalize is that **pip-audit does not have a built-in severity filter** (verified against official docs). Its exit code is non-zero when ANY vulnerability is found, regardless of severity. The CRITICAL+HIGH-only blocking behavior must be implemented by parsing pip-audit JSON output, or — more pragmatically — by using pip-audit's `--ignore-vuln` flag to suppress known LOW/MEDIUM findings and accepting that new vulnerabilities of any level will block CI. The latter approach is simpler and aligns with the locked decision's escape hatch pattern.

For bandit, the severity filtering CLI flag is `-lll` (three lowercase L's) for HIGH-only. The pre-commit hook receives `args: ["-lll", "-x", "tests/"]` to constrain scope. In CI, the equivalent is `uv run bandit -r apps/ -lll`. The `# nosec B<RULE_ID>` inline suppression is well-supported and standard.

**Primary recommendation:** Implement as three focused plans — (1) detect-secrets + bandit pre-commit and CI, (2) pip-audit + pnpm audit CI gates, (3) django-debug-toolbar dev configuration. Each plan is independent.

---

## Standard Stack

### Core

| Library              | Version | Purpose                                                         | Why Standard                                                                                |
| -------------------- | ------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| detect-secrets       | 1.5.0   | Entropy-based and pattern-based secret detection                | Yelp's original; most widely deployed in enterprise; baseline workflow handles legacy repos |
| bandit               | 1.9.4   | Static AST analysis for Python security anti-patterns           | Official PyCQA tool; native pre-commit hook; broad rule set covering OWASP Top 10 patterns  |
| pip-audit            | 2.10.0  | Python dependency CVE scanning via OSV/PyPI advisory database   | PyPA-maintained; `uv run` compatible; supports `--ignore-vuln` for graceful handling        |
| django-debug-toolbar | 6.2.0   | SQL query, header, cache, and request profiling in Django admin | Official Django ecosystem tool; zero production overhead; supports Django 4.2–6.0           |

### Supporting (JS)

| Library    | Version  | Purpose                                                 | When to Use                                                                         |
| ---------- | -------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| pnpm audit | built-in | JS/TS dependency CVE scanning via npm advisory registry | Already available — no install needed; `--audit-level high` controls exit threshold |

### Alternatives Considered

| Instead of     | Could Use | Tradeoff                                                                                                                              |
| -------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| detect-secrets | gitleaks  | gitleaks has better false-positive rates but no baseline workflow; detect-secrets baseline pattern is better for template inheritance |
| bandit         | semgrep   | semgrep is more powerful but heavier to configure; bandit is zero-config for standard Django patterns                                 |
| pip-audit      | safety    | safety requires a paid API key for full coverage since 2023; pip-audit uses OSV (free, Google-maintained)                             |

**Installation (Python dev deps):**

```bash
cd apps/api && uv add --group dev bandit pip-audit django-debug-toolbar
```

No JS install needed — `pnpm audit` is built into pnpm. `detect-secrets` is managed by the pre-commit runner (no manual install).

---

## Architecture Patterns

### Recommended File Layout

```
.                              # repo root
├── .pre-commit-config.yaml    # add detect-secrets + bandit hooks here
├── .secrets.baseline          # NEW: generated by detect-secrets scan
├── apps/
│   └── api/
│       ├── pyproject.toml     # add bandit, pip-audit, django-debug-toolbar to dev group
│       └── config/
│           ├── settings/
│           │   └── development.py    # DDT INSTALLED_APPS + MIDDLEWARE + INTERNAL_IPS
│           └── urls.py              # DDT URL pattern under if settings.DEBUG
└── .github/
    └── workflows/
        └── ci.yml             # add bandit step to api job; add audit steps (new security job or api job)
```

### Pattern 1: detect-secrets Pre-commit Hook

**What:** Hooks into pre-commit to scan staged files against a committed baseline. New secrets not in the baseline fail the commit.
**When to use:** Every commit to any file — no scope restriction (unlike bandit).

```yaml
# Source: https://github.com/Yelp/detect-secrets (pre-commit hook)
# Add to .pre-commit-config.yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ["--baseline", ".secrets.baseline"]
```

**Generating the baseline:**

```bash
# Run from repo root — scans everything, outputs known-safe baseline
cd apps/api && uv run detect-secrets scan > ../../.secrets.baseline
# OR (if detect-secrets in pre-commit env):
pre-commit run detect-secrets --all-files
```

**CI enforcement step (catches --no-verify bypasses):**

```yaml
# In .github/workflows/ci.yml
- name: Check detect-secrets baseline
  run: |
    pip install detect-secrets
    detect-secrets-hook --baseline .secrets.baseline $(git diff --name-only HEAD~1 HEAD || git ls-files)
```

A simpler CI approach is to just run `detect-secrets scan` and diff against the committed baseline:

```yaml
- name: Detect secrets
  run: |
    pip install detect-secrets
    detect-secrets scan --baseline .secrets.baseline
```

This re-scans all files and fails if any new secrets are found that are not in the baseline.

### Pattern 2: bandit Pre-commit Hook + CI

**What:** PyCQA/bandit scans Python AST for security anti-patterns. `-lll` = HIGH severity only. `-x tests/` = exclude tests directory.
**When to use:** Only on Python files in `apps/` — the hook's `files` pattern scopes this.

```yaml
# Source: https://github.com/PyCQA/bandit (.pre-commit-hooks.yaml)
# Add to .pre-commit-config.yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.9.4
  hooks:
    - id: bandit
      args: ["-lll", "-x", "tests/"]
      files: ^apps/
```

**CI step:**

```yaml
# Source: bandit CLI docs https://bandit.readthedocs.io/en/latest/man/bandit.html
- name: Run bandit security scan
  run: cd apps/api && uv run bandit -r apps/ -lll -x tests/
```

**False positive suppression:**

```python
# Source: bandit docs — inline nosec with explicit rule ID
result = subprocess.run(cmd, shell=True)  # nosec B603
```

Note: bare `# nosec` without rule ID is NOT accepted per locked decisions — rule ID is mandatory.

### Pattern 3: pip-audit CI Gate

**What:** pip-audit scans installed Python packages against OSV + PyPI advisory DB.
**Critical finding:** pip-audit has NO built-in severity filter. It exits non-zero when ANY vulnerability is detected. The CRITICAL+HIGH-only policy is enforced by ignoring known LOW/MEDIUM findings via `--ignore-vuln`.

**Recommended CI approach** (align with locked decisions escape hatch):

Option A — Store ignore list in a file, pass each entry as `--ignore-vuln`:

```yaml
- name: Run pip-audit
  run: |
    cd apps/api
    # Build --ignore-vuln args from .pip-audit-ignore file (one CVE ID per line, # for comments)
    IGNORE_ARGS=$(grep -v '^#' ../../.pip-audit-ignore 2>/dev/null | grep -v '^$' | sed 's/^/--ignore-vuln /' | tr '\n' ' ')
    uv run pip-audit $IGNORE_ARGS --format=columns
```

Option B — Inline `--ignore-vuln` flags in CI yaml (visible in code review, no external file):

```yaml
- name: Run pip-audit
  run: |
    cd apps/api
    uv run pip-audit --format=columns
    # Add --ignore-vuln PYSEC-XXXX-YYYY for confirmed LOW/MEDIUM findings
```

The template should ship with Option A + an empty `.pip-audit-ignore` file. The file approach provides a reviewable, auditable list of suppressed CVEs with comments explaining why each is suppressed.

**Template `.pip-audit-ignore` initial state:**

```
# pip-audit ignore list
# Format: one vulnerability ID per line (CVE-*, PYSEC-*, GHSA-*)
# Add comment on next line explaining why: upstream fix not yet released, not applicable, etc.
# Example:
# PYSEC-2023-1234
# Not applicable — we do not use the affected code path (XML parsing disabled)
```

### Pattern 4: pnpm audit CI Gate

**What:** pnpm's built-in audit command. `--audit-level high` causes non-zero exit on HIGH or CRITICAL findings only.

```yaml
# Source: https://pnpm.io/cli/audit
- name: Run pnpm audit
  run: pnpm audit --audit-level high
```

Place this in the `web` job in `ci.yml` (after `pnpm install`) — pnpm workspace audit covers all packages from repo root.

### Pattern 5: django-debug-toolbar (DEV-06)

**What:** DDT injects a sidebar panel into HTML responses when `DEBUG=True` and request IP is in `INTERNAL_IPS`. In this API-first template, only Django admin views produce HTML — DDT renders there.

**Installation location:** `development.py` only. Not `base.py`, not `test.py`, not `production.py`.

```python
# Source: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
# apps/api/config/settings/development.py

# --- django-debug-toolbar (DEV-06) ---
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # must be early in MIDDLEWARE
    *MIDDLEWARE,  # noqa: F405
]

INTERNAL_IPS = ["127.0.0.1"]
# For Docker: DDT only shows toolbar when request IP is in INTERNAL_IPS.
# 127.0.0.1 covers direct local dev. Docker users can set SHOW_TOOLBAR_CALLBACK.
```

**URL registration** in `urls.py` (conditional — never in production):

```python
# Source: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
from django.conf import settings

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
```

DDT 6.x uses the `debug_toolbar_urls()` helper function (not the old `include(debug_toolbar.urls)` pattern). Both work but the helper is the current recommended approach.

**SHOW_TOOLBAR_CALLBACK** (Claude's discretion — recommended):

```python
# Restrict to localhost only — prevents accidental exposure in shared dev environments
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: request.META.get("REMOTE_ADDR") in INTERNAL_IPS,
}
```

The default callback already checks `INTERNAL_IPS`, so this is only needed if Docker gateway IP handling is required.

### Anti-Patterns to Avoid

- **bare `# nosec` suppression in bandit:** Must include explicit rule ID (`# nosec B603`). The planner should make this a verification step.
- **detect-secrets in git pre-push (not pre-commit):** Secrets should be caught before `git commit`, not at push time. Hook must be `pre-commit` stage.
- **pip-audit in pre-commit hook:** pip-audit requires network and is slow — CI only per locked decisions.
- **DDT in `base.py`:** DDT middleware will 500-error in production if not installed. Must be `development.py` only.
- **DDT middleware position:** `DebugToolbarMiddleware` must be as early as possible in `MIDDLEWARE`, but after `GZipMiddleware` (if used). Wrong position causes DDT to miss responses.
- **`import debug_toolbar` in `urls.py` outside `if settings.DEBUG`:** Will cause `ImportError` in environments where DDT is not installed (test, prod).

---

## Don't Hand-Roll

| Problem                    | Don't Build                       | Use Instead          | Why                                                                                |
| -------------------------- | --------------------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| Secret pattern matching    | Custom regex for AWS keys, tokens | detect-secrets       | Covers 30+ secret types including entropy analysis; false positive tuning built in |
| Python security linting    | Custom AST checks                 | bandit               | 100+ test IDs covering OWASP patterns; maintained by PyCQA                         |
| CVE database lookups       | pip-audit DIY                     | pip-audit (PyPA)     | OSV integration, free, maintained by Python Packaging Authority                    |
| SQL query profiling in dev | Custom logging middleware         | django-debug-toolbar | 10+ panels, zero config, well-maintained ecosystem                                 |

**Key insight:** All four tools are maintained by their respective ecosystem authorities (Yelp, PyCQA, PyPA, Django project). Custom solutions would need to replicate years of false-positive tuning and vulnerability database integrations.

---

## Common Pitfalls

### Pitfall 1: pip-audit exits non-zero on any severity

**What goes wrong:** CI fails on LOW/MEDIUM CVEs in transitive dependencies that are not exploitable. Team adds `continue-on-error: true` to "fix" it, defeating the gate.
**Why it happens:** pip-audit has no built-in severity filter (confirmed via official docs). Exit code is binary: vulnerabilities found or not.
**How to avoid:** Use `--ignore-vuln` for confirmed non-critical findings. Ship the template with an empty `.pip-audit-ignore` and document the workflow: find CVE, assess severity, if LOW/MEDIUM and not a realistic exploit path, add to ignore file with comment.
**Warning signs:** `.pip-audit-ignore` growing large without comments is a smell.

### Pitfall 2: bandit fires on test files

**What goes wrong:** bandit flags `assert password == "hardcoded"`, `subprocess.run(cmd)` in test factories — noisy, causes developers to add blanket suppressions.
**Why it happens:** Test code intentionally violates security patterns.
**How to avoid:** `-x tests/` in both pre-commit args and CI command. This is already in the locked decisions. Planner must include this in every bandit invocation.

### Pitfall 3: detect-secrets baseline file becomes stale

**What goes wrong:** Developer regenerates baseline with `detect-secrets scan > .secrets.baseline` without reviewing it — silently baselines new real secrets.
**Why it happens:** `scan > .secrets.baseline` overwrites without diff.
**How to avoid:** The correct workflow is `detect-secrets audit .secrets.baseline` for reviewing and marking individual findings as false positives. Document this in the project's DEV_SETUP.md addition.

### Pitfall 4: DDT shows in test runs

**What goes wrong:** `pytest` uses `DJANGO_SETTINGS_MODULE = config.settings.development` (current setting in `pyproject.toml`). DDT is in `development.py`. Tests run with DDT installed — adds overhead, may cause unexpected toolbar injection in integration tests.
**Why it happens:** `pyproject.toml` currently sets `DJANGO_SETTINGS_MODULE = "config.settings.development"`.
**How to avoid:** Two options:

1. Create `config/settings/test.py` (extends base, no DDT) and update `pyproject.toml` to point at it.
2. Keep development settings for tests but verify DDT doesn't cause test failures (DDT only activates when `INTERNAL_IPS` matches, which won't happen in pytest's test client by default).
   Option 2 is lower-risk. The test client's `REMOTE_ADDR` defaults to `127.0.0.1`, which IS in `INTERNAL_IPS` — but DDT only injects into HTML responses. Since tests hit JSON API endpoints, no actual injection occurs. Option 2 is acceptable.

### Pitfall 5: pnpm audit flags dev dependencies

**What goes wrong:** Dev-only packages (jest, vitest) have CVEs that are irrelevant in production.
**Why it happens:** `pnpm audit` scans all dependency types by default.
**How to avoid:** `pnpm audit --audit-level high --prod` limits to production dependencies only. However, the locked decision says `--audit-level high` without `--prod`. Starting without `--prod` is consistent with the locked decisions; add `--prod` later if dev dep noise becomes an issue.

### Pitfall 6: DDT URL import fails in production

**What goes wrong:** `from debug_toolbar.toolbar import debug_toolbar_urls` at module level causes `ImportError` in production (DDT not installed).
**Why it happens:** Import is outside `if settings.DEBUG` guard.
**How to avoid:** The import must be inside the `if settings.DEBUG:` block in `urls.py`. The DDT 6.x pattern puts both import and `urlpatterns +=` inside the guard.

---

## Code Examples

Verified patterns from official sources:

### detect-secrets: Generating Initial Baseline

```bash
# Source: https://github.com/Yelp/detect-secrets
# Run from repo root — creates/updates .secrets.baseline
detect-secrets scan > .secrets.baseline
# Or with uv in the api virtualenv:
cd apps/api && uv run detect-secrets scan ../.. > ../../.secrets.baseline
```

### bandit: Pre-commit Hook Entry

```yaml
# Source: https://github.com/PyCQA/bandit/.pre-commit-hooks.yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.9.4
  hooks:
    - id: bandit
      args: ["-lll", "-x", "tests/"]
      files: ^apps/
```

`-lll` = report HIGH severity and above only (3 l's = HIGH threshold per bandit docs).

### bandit: CI Step

```yaml
# Source: bandit CLI docs
- name: Run bandit
  run: cd apps/api && uv run bandit -r apps/ -lll -x tests/
```

### pip-audit: CI Step with Ignore File

```yaml
# Source: https://github.com/pypa/pip-audit (--ignore-vuln flag)
- name: Run pip-audit
  run: |
    # Read ignore list from .pip-audit-ignore (one ID per line, # comments allowed)
    IGNORE_ARGS=""
    if [ -f ".pip-audit-ignore" ]; then
      while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        IGNORE_ARGS="$IGNORE_ARGS --ignore-vuln $line"
      done < ".pip-audit-ignore"
    fi
    cd apps/api && uv run pip-audit $IGNORE_ARGS
```

### pnpm audit: CI Step

```yaml
# Source: https://pnpm.io/cli/audit
- name: Run pnpm audit
  run: pnpm audit --audit-level high
```

### DDT: development.py Configuration

```python
# Source: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
# apps/api/config/settings/development.py

# --- django-debug-toolbar (DEV-06) ---
INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]  # noqa: F405
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
```

### DDT: urls.py URL Registration

```python
# Source: https://django-debug-toolbar.readthedocs.io/en/latest/installation.html
# apps/api/config/urls.py — inside the file, after urlpatterns definition

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()
```

---

## State of the Art

| Old Approach                             | Current Approach              | When Changed     | Impact                                              |
| ---------------------------------------- | ----------------------------- | ---------------- | --------------------------------------------------- |
| `include(debug_toolbar.urls)` in urls.py | `debug_toolbar_urls()` helper | DDT 4.x+         | Simpler, handles URL prefix internally              |
| `safety check` (paid API key required)   | `pip-audit` (free OSV)        | 2023             | pip-audit is now the standard for free CVE scanning |
| `bandit` with `.bandit` config file      | `bandit` via pre-commit args  | Always supported | Args approach is cleaner for template inheritance   |

**Deprecated/outdated:**

- `safety` CLI: Requires API key since 2023 — replaced by pip-audit in open-source contexts.
- `DEBUG_TOOLBAR_CONFIG["SHOW_TOOLBAR_CALLBACK"]` using `DEBUG` flag: The standard pattern now uses `INTERNAL_IPS` check, which is DDT's default behavior.

---

## Open Questions

1. **pip-audit severity gap: how to handle truly new HIGH CVEs in transitive deps**
   - What we know: pip-audit blocks CI on any finding not in the ignore list. New transitive dep CVEs will block CI until assessed.
   - What's unclear: Whether the team wants `continue-on-error: true` as a fallback or strict blocking.
   - Recommendation: The locked decision says HIGH blocks. Ship with strict blocking. If a transitive dep introduces a HIGH CVE that's not patchable yet, add to `.pip-audit-ignore` with a comment and a scheduled review date.

2. **CI job structure for audit steps**
   - What we know: Claude's discretion — can be within `api` job or a new `security` job.
   - What's unclear: Whether parallel security job is worth the extra job overhead.
   - Recommendation: Add as steps within existing `api` and `web` jobs. `pip-audit` goes after `uv sync` in the `api` job. `pnpm audit` goes after `pnpm install` in the `web` job. This avoids a third job while keeping audit steps visible in the job that installs the deps.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                          |
| ------------------ | -------------------------------------------------------------- |
| Framework          | pytest 8.0+ with pytest-django                                 |
| Config file        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]`        |
| Quick run command  | `cd apps/api && uv run pytest tests/core/test_dev_gates.py -x` |
| Full suite command | `cd apps/api && uv run pytest --cov --cov-report=xml`          |

### Phase Requirements → Test Map

| Req ID | Behavior                                                                                    | Test Type   | Automated Command                                                                                | File Exists? |
| ------ | ------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------ | ------------ |
| DEV-01 | `.secrets.baseline` file exists at repo root                                                | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_secrets_baseline_exists -x`     | ❌ Wave 0    |
| DEV-01 | CI step runs detect-secrets scan and exits non-zero on new secrets                          | manual-only | N/A — pre-commit hook behavior; verified by attempting to commit a fake secret                   | —            |
| DEV-02 | `bandit` CLI installed and available via `uv run bandit`                                    | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_bandit_available -x`            | ❌ Wave 0    |
| DEV-02 | `bandit -r apps/ -lll` exits 0 on current codebase (no existing HIGH findings)              | integration | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_bandit_clean -x`                | ❌ Wave 0    |
| DEV-03 | `pip-audit` CLI installed and available via `uv run pip-audit`                              | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_pip_audit_available -x`         | ❌ Wave 0    |
| DEV-06 | DDT absent from INSTALLED_APPS in `base.py` and `production.py` (not in test settings path) | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_not_in_base_settings -x`    | ❌ Wave 0    |
| DEV-06 | DDT present in INSTALLED_APPS in `development.py`                                           | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_in_development_settings -x` | ❌ Wave 0    |
| DEV-06 | `/__debug__/` URL is routable when `DEBUG=True` (returns 200/404, not 500)                  | integration | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_url_accessible_in_debug -x` | ❌ Wave 0    |

**Note on DEV-01 and DEV-02 pre-commit behavior:** Full end-to-end test (commit blocked by hook) cannot be automated in pytest. The test suite validates that the tooling is installed and that the current codebase is clean. The pre-commit hook configuration itself is a Wave 0 deliverable (`.pre-commit-config.yaml` additions) that is verified by running `pre-commit run --all-files` as a manual check or CI step.

### Sampling Rate

- **Per task commit:** `cd apps/api && uv run pytest tests/core/test_dev_gates.py -x`
- **Per wave merge:** `cd apps/api && uv run pytest --cov --cov-report=xml`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/core/test_dev_gates.py` — covers DEV-01, DEV-02, DEV-03, DEV-06 as described in test map above

_(Existing `tests/conftest.py` and pytest infrastructure fully cover shared fixtures — no new conftest needed)_

---

## Sources

### Primary (HIGH confidence)

- `https://django-debug-toolbar.readthedocs.io/en/latest/installation.html` — DDT 6.2.0 installation config (INSTALLED_APPS, MIDDLEWARE, INTERNAL_IPS, `debug_toolbar_urls()` helper)
- `https://bandit.readthedocs.io/en/latest/man/bandit.html` — bandit CLI flags (`-lll` for HIGH severity, `-x` for exclude paths)
- `https://github.com/pypa/pip-audit` — pip-audit CLI; confirmed no built-in severity filter; `--ignore-vuln` flag for CVE suppression; current version 2.10.0
- `https://pnpm.io/cli/audit` — pnpm audit `--audit-level high` flag behavior and exit code semantics
- `https://github.com/Yelp/detect-secrets` — detect-secrets pre-commit hook config; baseline workflow; version 1.5.0

### Secondary (MEDIUM confidence)

- `https://pypi.org/project/django-debug-toolbar/` — version 6.2.0 confirmed, Django 4.2–6.0 support matrix
- `https://pypi.org/project/bandit/` — version 1.9.4 confirmed
- `https://pypi.org/project/pip-audit/` — version 2.10.0 confirmed
- `https://pypi.org/project/detect-secrets/` — version 1.5.0 confirmed

### Tertiary (LOW confidence)

- WebSearch findings on pip-audit severity behavior — corroborated by official GitHub README fetch

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all versions verified via PyPI and official docs
- Architecture: HIGH — bandit flags, DDT config, detect-secrets baseline workflow all verified from official sources
- Pitfalls: HIGH for DDT/bandit/detect-secrets; MEDIUM for pip-audit severity gap (confirmed no built-in filter, but recommended workaround is pragmatic, not the only approach)

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (90 days — all four tools are mature/stable; DDT moves fastest due to Django version tracking)
