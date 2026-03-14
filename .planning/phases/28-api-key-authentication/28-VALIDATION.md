---
phase: 28
slug: api-key-authentication
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-13
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                  |
| ---------------------- | ------------------------------------------------------ |
| **Framework**          | pytest + pytest-django (existing)                      |
| **Config file**        | `apps/api/pytest.ini` / `pyproject.toml [tool.pytest]` |
| **Quick run command**  | `cd apps/api && uv run pytest tests/api_keys/ -x -q`   |
| **Full suite command** | `cd apps/api && uv run pytest tests/ -x -q`            |
| **Estimated runtime**  | ~27 seconds (42 tests)                                 |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/api_keys/ -x -q`
- **After every plan wave:** Run `cd apps/api && uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 27 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type        | Automated Command                                                                                 | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ---------------- | ------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 28-01-01 | 01   | 0    | AKEY-01     | integration      | `cd apps/api && uv run pytest tests/api_keys/ -x -q`                                              | ✅          | ✅ green |
| 28-02-01 | 02   | 1    | AKEY-01     | unit/integration | `cd apps/api && uv run pytest tests/api_keys/test_models.py tests/api_keys/test_auth.py -x -q`    | ✅          | ✅ green |
| 28-02-02 | 02   | 1    | AKEY-01     | integration      | `cd apps/api && uv run pytest tests/api_keys/test_controllers.py -x -q`                           | ✅          | ✅ green |
| 28-03-01 | 03   | 2    | AKEY-02     | integration      | `cd apps/api && uv run pytest tests/api_keys/test_ratelimit.py -x -q`                             | ✅          | ✅ green |
| 28-04-01 | 04   | 2    | AKEY-03     | integration      | `cd apps/api && uv run pytest tests/api_keys/test_auth.py -k "last_used_at or usage_count" -x -q` | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/api_keys/__init__.py` — module marker
- [x] `tests/api_keys/conftest.py` — user + api_key fixtures
- [x] `tests/api_keys/test_models.py` — AKEY-01: key generation, hash storage, raw key shown once
- [x] `tests/api_keys/test_auth.py` — AKEY-01: `ApiKeyAuth`, `RequireScope`, session-only rejection; AKEY-03: usage tracking
- [x] `tests/api_keys/test_ratelimit.py` — AKEY-02: rate limit headers (overrides `RATELIMIT_ENABLE=True`)
- [x] `tests/api_keys/test_controllers.py` — AKEY-01: create/list/revoke HTTP endpoints
- [x] `tests/api_keys/test_checks.py` — AKEY-01: `API_KEY_SCOPES` startup validation
- [x] `tests/api_keys/test_ping.py` — end-to-end ping endpoint authentication via API key

**Critical note:** `test_isolation_settings` autouse fixture in `tests/conftest.py` sets `RATELIMIT_ENABLE=False` globally. Rate limit tests override with `settings.RATELIMIT_ENABLE = True` per test.

---

## Manual-Only Verifications

| Behavior                     | Requirement | Why Manual                | Test Instructions                                                                                                                 |
| ---------------------------- | ----------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Raw key displayed once in UI | AKEY-01     | Frontend display behavior | Create key via API endpoint, verify response contains `raw_key`; verify subsequent GET /api-keys does not include `raw_key` field |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ Nyquist-compliant (audited 2026-03-13)

---

## Validation Audit 2026-03-13

| Metric     | Count                |
| ---------- | -------------------- |
| Gaps found | 0                    |
| Resolved   | 0                    |
| Escalated  | 0                    |
| Tests run  | 42 passed, 0 skipped |
