---
phase: 17
slug: dev-time-security-gates
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                          |
| ---------------------- | -------------------------------------------------------------- |
| **Framework**          | pytest 8.0+ with pytest-django                                 |
| **Config file**        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]`        |
| **Quick run command**  | `cd apps/api && uv run pytest tests/core/test_dev_gates.py -x` |
| **Full suite command** | `cd apps/api && uv run pytest --cov --cov-report=xml`          |
| **Estimated runtime**  | ~10 seconds                                                    |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/core/test_dev_gates.py -x`
- **After every plan wave:** Run `cd apps/api && uv run pytest --cov --cov-report=xml`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | ------------------------------------------------------------------------------------------------ | ----------- | ---------- |
| 17-01-01 | 01   | 1    | DEV-01      | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_secrets_baseline_exists -x`     | ❌ W0       | ⬜ pending |
| 17-01-02 | 01   | 1    | DEV-01      | manual      | Attempt to commit file with fake AWS key — hook must block                                       | —           | ⬜ pending |
| 17-01-03 | 01   | 1    | DEV-02      | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_bandit_available -x`            | ❌ W0       | ⬜ pending |
| 17-01-04 | 01   | 1    | DEV-02      | integration | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_bandit_clean -x`                | ❌ W0       | ⬜ pending |
| 17-01-05 | 01   | 1    | DEV-03      | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_pip_audit_available -x`         | ❌ W0       | ⬜ pending |
| 17-02-01 | 02   | 2    | DEV-06      | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_not_in_base_settings -x`    | ❌ W0       | ⬜ pending |
| 17-02-02 | 02   | 2    | DEV-06      | unit        | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_in_development_settings -x` | ❌ W0       | ⬜ pending |
| 17-02-03 | 02   | 2    | DEV-06      | integration | `cd apps/api && uv run pytest tests/core/test_dev_gates.py::test_ddt_url_accessible_in_debug -x` | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/core/test_dev_gates.py` — stubs for DEV-01 (secrets baseline), DEV-02 (bandit available + clean), DEV-03 (pip-audit available), DEV-06 (DDT settings + URL)

_Existing `tests/conftest.py` and pytest infrastructure fully cover shared fixtures — no new conftest needed._

---

## Manual-Only Verifications

| Behavior                                                   | Requirement | Why Manual                                               | Test Instructions                                                                                                                       |
| ---------------------------------------------------------- | ----------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Pre-commit hook blocks commit containing detectable secret | DEV-01      | Hook executes in git subprocess; cannot drive via pytest | Create temp file with fake AWS key pattern (`AKIA...`), run `git add` + `git commit` — expect non-zero exit with detect-secrets finding |
| CI fails on PR with HIGH bandit finding                    | DEV-02      | Requires a live GitHub Actions run on a PR branch        | Push a branch with a known-bad bandit pattern (e.g., `subprocess.call(cmd, shell=True)`), open PR, verify CI `bandit` step fails        |
| CI fails on PR with known CVE dependency                   | DEV-03      | Requires a real CI run with a vulnerable dep             | Pin a dependency to a known-vulnerable version in a test branch, open PR, verify pip-audit step fails                                   |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
