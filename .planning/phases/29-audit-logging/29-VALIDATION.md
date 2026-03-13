---
phase: 29
slug: audit-logging
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| **Framework**          | pytest 8.x + pytest-django 4.x                          |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command**  | `cd apps/api && python -m pytest tests/audit/ -x -q`    |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -x -q`          |
| **Estimated runtime**  | ~30 seconds                                             |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/audit/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement        | Test Type   | Automated Command                              | File Exists | Status     |
| -------- | ---- | ---- | ------------------ | ----------- | ---------------------------------------------- | ----------- | ---------- |
| 29-01-01 | 01   | 1    | AUDIT-01, AUDIT-02 | unit        | `pytest tests/audit/ -x -q`                    | ❌ W0       | ⬜ pending |
| 29-02-01 | 02   | 2    | AUDIT-01           | integration | `pytest tests/audit/test_middleware.py -x -q`  | ❌ W0       | ⬜ pending |
| 29-03-01 | 03   | 2    | AUDIT-02           | integration | `pytest tests/audit/test_controllers.py -x -q` | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/audit/__init__.py` — test module init
- [ ] `tests/audit/conftest.py` — shared fixtures (org, user, membership, api_key, webhook_endpoint factories)
- [ ] `tests/audit/test_middleware.py` — RED stubs for AUDIT-01 (trigger + context tests)
- [ ] `tests/audit/test_controllers.py` — RED stubs for AUDIT-02 (query API tests)

---

## Manual-Only Verifications

| Behavior                                          | Requirement | Why Manual                                         | Test Instructions            |
| ------------------------------------------------- | ----------- | -------------------------------------------------- | ---------------------------- |
| Impersonation context written by Phase 30 signals | AUDIT-01    | django-hijack signals not installed until Phase 30 | Verify in Phase 30 execution |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
