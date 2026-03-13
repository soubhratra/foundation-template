---
phase: 28
slug: api-key-authentication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                  |
| ---------------------- | ------------------------------------------------------ |
| **Framework**          | pytest + pytest-django (existing)                      |
| **Config file**        | `apps/api/pytest.ini` / `pyproject.toml [tool.pytest]` |
| **Quick run command**  | `uv run pytest apps/api/tests/api_keys/ -x -q`         |
| **Full suite command** | `uv run pytest apps/api/tests/ -x -q`                  |
| **Estimated runtime**  | ~30 seconds                                            |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest apps/api/tests/api_keys/ -x -q`
- **After every plan wave:** Run `uv run pytest apps/api/tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type        | Automated Command                                                                                                                                        | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 28-01-01 | 01   | 0    | AKEY-01     | integration      | `uv run pytest apps/api/tests/api_keys/ -x -q`                                                                                                           | ❌ W0       | ⬜ pending |
| 28-02-01 | 02   | 1    | AKEY-01     | unit/integration | `uv run pytest apps/api/tests/api_keys/test_models.py apps/api/tests/api_keys/test_auth.py -x -q`                                                        | ❌ W0       | ⬜ pending |
| 28-02-02 | 02   | 1    | AKEY-01     | integration      | `uv run pytest apps/api/tests/api_keys/test_controllers.py -x -q`                                                                                        | ❌ W0       | ⬜ pending |
| 28-03-01 | 03   | 2    | AKEY-02     | integration      | `uv run pytest apps/api/tests/api_keys/test_ratelimit.py -x -q`                                                                                          | ❌ W0       | ⬜ pending |
| 28-04-01 | 04   | 2    | AKEY-03     | integration      | `uv run pytest apps/api/tests/api_keys/test_auth.py::test_last_used_at_updated apps/api/tests/api_keys/test_auth.py::test_usage_count_incremented -x -q` | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/api_keys/__init__.py` — module-level import RED trigger (mirrors `tests/webhooks/__init__.py`)
- [ ] `apps/api/tests/api_keys/conftest.py` — user + api_key fixtures
- [ ] `apps/api/tests/api_keys/test_models.py` — covers key generation, hash storage
- [ ] `apps/api/tests/api_keys/test_auth.py` — covers `ApiKeyAuth`, `RequireScope`, AKEY-01, AKEY-03; rate limit tests must override `RATELIMIT_ENABLE=True`
- [ ] `apps/api/tests/api_keys/test_ratelimit.py` — covers AKEY-02 (rate limit headers); must set `settings.RATELIMIT_ENABLE = True`
- [ ] `apps/api/tests/api_keys/test_controllers.py` — covers create/list/revoke HTTP endpoints
- [ ] `apps/api/tests/api_keys/test_checks.py` — covers `API_KEY_SCOPES` validator warnings

**Critical note:** `test_isolation_settings` autouse fixture in `apps/api/tests/conftest.py` sets `RATELIMIT_ENABLE=False` globally. Rate limit tests MUST override with `settings.RATELIMIT_ENABLE = True` or `get_usage()` returns `None` and no headers appear.

---

## Manual-Only Verifications

| Behavior                     | Requirement | Why Manual                | Test Instructions                                                                                                                 |
| ---------------------------- | ----------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Raw key displayed once in UI | AKEY-01     | Frontend display behavior | Create key via API endpoint, verify response contains `raw_key`; verify subsequent GET /api-keys does not include `raw_key` field |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
