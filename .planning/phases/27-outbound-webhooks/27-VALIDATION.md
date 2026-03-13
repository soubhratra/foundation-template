---
phase: 27
slug: outbound-webhooks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                           |
| **Config file**        | `apps/api/pytest.ini` or `apps/api/pyproject.toml [tool.pytest]` |
| **Quick run command**  | `cd apps/api && python -m pytest tests/webhooks/ -x -q`          |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -x -q`                   |
| **Estimated runtime**  | ~30 seconds (quick) / ~90 seconds (full)                         |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/webhooks/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type          | Automated Command                                                                                                                                        | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 27-01-01 | 01   | 0    | HOOK-01     | unit               | `cd apps/api && python -m pytest tests/webhooks/ -x -q`                                                                                                  | ❌ W0       | ⬜ pending |
| 27-01-02 | 01   | 1    | HOOK-01     | unit + integration | `cd apps/api && python -m pytest tests/webhooks/test_models.py tests/webhooks/test_utils.py -x -q`                                                       | ❌ W0       | ⬜ pending |
| 27-01-03 | 01   | 1    | HOOK-01     | integration        | `cd apps/api && python -m pytest tests/webhooks/test_controllers.py::test_create_endpoint tests/webhooks/test_controllers.py::test_list_endpoints -x -q` | ❌ W0       | ⬜ pending |
| 27-02-01 | 02   | 2    | HOOK-01     | unit               | `cd apps/api && python -m pytest tests/webhooks/test_tasks.py::test_deliver_webhook_retries -x -q`                                                       | ❌ W0       | ⬜ pending |
| 27-02-02 | 02   | 2    | HOOK-04     | unit               | `cd apps/api && python -m pytest tests/webhooks/test_tasks.py::test_circuit_breaker -x -q`                                                               | ❌ W0       | ⬜ pending |
| 27-02-03 | 02   | 2    | HOOK-02     | integration        | `cd apps/api && python -m pytest tests/webhooks/test_controllers.py::test_list_deliveries -x -q`                                                         | ❌ W0       | ⬜ pending |
| 27-03-01 | 03   | 3    | HOOK-03     | integration        | `cd apps/api && python -m pytest tests/webhooks/test_controllers.py::test_retry_delivery -x -q`                                                          | ❌ W0       | ⬜ pending |
| 27-03-02 | 03   | 3    | HOOK-04     | integration        | `cd apps/api && python -m pytest tests/webhooks/test_controllers.py::test_reenable_endpoint -x -q`                                                       | ❌ W0       | ⬜ pending |
| 27-03-03 | 03   | 3    | HOOK-01     | unit               | `cd apps/api && python -m pytest tests/webhooks/test_checks.py -x -q`                                                                                    | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `tests/webhooks/__init__.py` — marks package; top-level import from `apps.webhooks.models` ensures RED state before implementation
- [ ] `tests/webhooks/conftest.py` — `org`, `org_owner`, `admin_user`, `endpoint`, `delivery` fixtures
- [ ] `tests/webhooks/test_models.py` — model field coverage, `generate_secret()`, cascade delete behavior
- [ ] `tests/webhooks/test_utils.py` — `fire_webhook_event()` validation and `transaction.on_commit()` dispatch
- [ ] `tests/webhooks/test_tasks.py` — `deliver_webhook` retry logic, circuit breaker, cleanup task
- [ ] `tests/webhooks/test_controllers.py` — all 8 HTTP endpoints (register, list, update, delete, history, delivery detail, retry, re-enable)
- [ ] `tests/webhooks/test_checks.py` — `manage.py check` validates `WEBHOOK_EVENTS` setting

_All new files — no existing infrastructure covers webhooks._

---

## Manual-Only Verifications

| Behavior                                         | Requirement | Why Manual                                               | Test Instructions                                                                                                                                            |
| ------------------------------------------------ | ----------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Email notification when endpoint disabled        | HOOK-04     | Requires real email delivery in test env                 | Trigger 5 consecutive failures against a test endpoint; verify org admin inbox receives notification with endpoint URL and last failure reason               |
| HMAC signature verification by external consumer | HOOK-01     | Requires external HTTP server acting as webhook receiver | Use `ngrok` + simple Flask server to receive webhook, verify `X-Webhook-Signature: sha256=<hex>` matches computed HMAC-SHA256 of payload using shared secret |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
