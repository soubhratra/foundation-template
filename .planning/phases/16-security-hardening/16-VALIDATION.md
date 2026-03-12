---
phase: 16
slug: security-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                           |
| **Config file**        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]`          |
| **Quick run command**  | `cd apps/api && python -m pytest tests/core/test_security.py -x` |
| **Full suite command** | `cd apps/api && python -m pytest`                                |
| **Estimated runtime**  | ~15 seconds                                                      |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/core/test_security.py -x`
- **After every plan wave:** Run `cd apps/api && python -m pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                           | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | --------------------------------------------------------------------------- | ----------- | ---------- |
| 16-01-01 | 01   | 0    | SEC-01      | integration | `pytest tests/core/test_security.py -x`                                     | ❌ W0       | ⬜ pending |
| 16-01-02 | 01   | 1    | SEC-01a     | integration | `pytest tests/core/test_security.py::test_rate_limit_returns_429 -x`        | ❌ W0       | ⬜ pending |
| 16-01-03 | 01   | 1    | SEC-01b     | integration | `pytest tests/core/test_security.py::test_rate_limit_retry_after_header -x` | ❌ W0       | ⬜ pending |
| 16-01-04 | 01   | 1    | SEC-01c     | integration | `pytest tests/core/test_security.py::test_rate_limit_uses_redis_cache -x`   | ❌ W0       | ⬜ pending |
| 16-02-01 | 02   | 1    | SEC-02a     | integration | `pytest tests/core/test_security.py::test_csp_header_present -x`            | ❌ W0       | ⬜ pending |
| 16-02-02 | 02   | 1    | SEC-02b     | integration | `pytest tests/core/test_security.py::test_hsts_header_production -x`        | ❌ W0       | ⬜ pending |
| 16-02-03 | 02   | 1    | SEC-02c     | integration | `pytest tests/core/test_security.py::test_x_frame_options_header -x`        | ❌ W0       | ⬜ pending |
| 16-02-04 | 02   | 1    | SEC-02d     | integration | `pytest tests/core/test_security.py::test_referrer_policy_header -x`        | ❌ W0       | ⬜ pending |
| 16-03-01 | 03   | 1    | SEC-03a     | unit        | `pytest tests/core/test_security.py::test_default_cache_is_redis -x`        | ❌ W0       | ⬜ pending |
| 16-03-02 | 03   | 1    | SEC-03b     | unit        | `pytest tests/core/test_security.py::test_session_cache_is_redis -x`        | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/core/test_security.py` — stubs for SEC-01 (rate limiting), SEC-02 (security headers), SEC-03 (Redis cache/session)
- [ ] No new fixtures needed — existing `api_client` and `settings` fixtures from `tests/conftest.py` are sufficient
- [ ] No new packages for tests — existing `pytest-django` covers all test needs

_Note: `tests/core/` directory may need creating if it does not exist._

---

## Manual-Only Verifications

| Behavior                                            | Requirement | Why Manual                                                  | Test Instructions                                                          |
| --------------------------------------------------- | ----------- | ----------------------------------------------------------- | -------------------------------------------------------------------------- |
| Next.js `Content-Security-Policy` header in browser | SEC-02      | Next.js `headers()` config is not exercised by Django tests | Open browser DevTools → Network → check response headers for any page      |
| Next.js `X-Frame-Options` header in browser         | SEC-02      | Same — Next.js server, not Django                           | Open browser DevTools → Network → check `x-frame-options` on page response |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
