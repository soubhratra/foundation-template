---
phase: 33
slug: apikey-auth-example-endpoint
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 33 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                               |
| ---------------------- | ------------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                              |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)             |
| **Quick run command**  | `cd apps/api && python -m pytest tests/api_keys/test_ping.py -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest tests/api_keys/ -x -q`             |
| **Estimated runtime**  | ~10 seconds                                                         |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/api_keys/test_ping.py -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/api_keys/ -x -q`
- **Before `/gsd:verify-work`:** Full api_keys suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement               | Test Type   | Automated Command                                                                                                                                                                                                                                                                                         | File Exists | Status     |
| -------- | ---- | ---- | ------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 33-01-01 | 01   | 0    | AKEY-01, AKEY-02, AKEY-03 | integration | `cd apps/api && python -m pytest tests/api_keys/test_ping.py -x -q`                                                                                                                                                                                                                                       | ❌ W0       | ⬜ pending |
| 33-01-02 | 01   | 1    | AKEY-01                   | integration | `cd apps/api && python -m pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_valid_key_with_read_scope_returns_200 tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_wrong_scope_returns_403 tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_session_auth_rejected -x -q` | ✅ W0       | ⬜ pending |
| 33-01-03 | 01   | 1    | AKEY-02                   | integration | `cd apps/api && python -m pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_rate_limit_headers_on_success tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_rate_limit_exceeded_returns_429 -x -q`                                                                                 | ✅ W0       | ⬜ pending |
| 33-02-01 | 02   | 1    | AKEY-03                   | integration | `cd apps/api && python -m pytest tests/api_keys/test_ping.py::TestApiKeyPingEndpoint::test_valid_key_updates_usage_tracking -x -q`                                                                                                                                                                        | ✅ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/api_keys/test_ping.py` — 6 integration test stubs covering AKEY-01, AKEY-02, AKEY-03:
  - `test_valid_key_with_read_scope_returns_200`
  - `test_wrong_scope_returns_403`
  - `test_session_auth_rejected`
  - `test_rate_limit_headers_on_success`
  - `test_rate_limit_exceeded_returns_429`
  - `test_valid_key_updates_usage_tracking`

_All other test infrastructure (conftest.py, fixtures, pytest config) exists and is reusable without modification._

---

## Manual-Only Verifications

_All phase behaviors have automated verification._

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
