---
phase: 27
slug: outbound-webhooks
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-13
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                           |
| ---------------------- | --------------------------------------------------------------- |
| **Framework**          | pytest + pytest-django                                          |
| **Config file**        | `apps/api/pytest.ini` / `apps/api/pyproject.toml [tool.pytest]` |
| **Quick run command**  | `cd apps/api && uv run pytest tests/webhooks/ -x -q`            |
| **Full suite command** | `cd apps/api && uv run pytest tests/ -x -q`                     |
| **Estimated runtime**  | ~57 seconds (36 tests)                                          |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && uv run pytest tests/webhooks/ -x -q`
- **After every plan wave:** Run `cd apps/api && uv run pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 57 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type          | Automated Command                                                                               | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ------------------ | ----------------------------------------------------------------------------------------------- | ----------- | -------- |
| 27-01-01 | 01   | 0    | HOOK-01     | unit               | `cd apps/api && uv run pytest tests/webhooks/ -x -q`                                            | ✅          | ✅ green |
| 27-01-02 | 01   | 1    | HOOK-01     | unit + integration | `cd apps/api && uv run pytest tests/webhooks/test_models.py tests/webhooks/test_utils.py -x -q` | ✅          | ✅ green |
| 27-01-03 | 01   | 1    | HOOK-01     | integration        | `cd apps/api && uv run pytest tests/webhooks/test_controllers.py::TestEndpointCRUD -x -q`       | ✅          | ✅ green |
| 27-02-01 | 02   | 2    | HOOK-01     | unit               | `cd apps/api && uv run pytest tests/webhooks/test_tasks.py -k "retry" -x -q`                    | ✅          | ✅ green |
| 27-02-02 | 02   | 2    | HOOK-04     | unit               | `cd apps/api && uv run pytest tests/webhooks/test_tasks.py -k "circuit_breaker" -x -q`          | ✅          | ✅ green |
| 27-02-03 | 02   | 2    | HOOK-02     | integration        | `cd apps/api && uv run pytest tests/webhooks/test_controllers.py::TestDeliveryHistory -x -q`    | ✅          | ✅ green |
| 27-03-01 | 03   | 3    | HOOK-03     | integration        | `cd apps/api && uv run pytest tests/webhooks/test_controllers.py::TestManualRetry -x -q`        | ✅          | ✅ green |
| 27-03-02 | 03   | 3    | HOOK-04     | integration        | `cd apps/api && uv run pytest tests/webhooks/test_controllers.py::TestReEnableEndpoint -x -q`   | ✅          | ✅ green |
| 27-03-03 | 03   | 3    | HOOK-01     | unit               | `cd apps/api && uv run pytest tests/webhooks/test_checks.py -x -q`                              | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `tests/webhooks/__init__.py` — marks package
- [x] `tests/webhooks/conftest.py` — `org`, `org_owner`, `admin_user`, `endpoint`, `delivery` fixtures
- [x] `tests/webhooks/test_models.py` — HOOK-01: endpoint registration fields, delivery cascade, attempt truncation
- [x] `tests/webhooks/test_utils.py` — HOOK-01: `fire_webhook_event()` validation, `transaction.on_commit()` dispatch
- [x] `tests/webhooks/test_tasks.py` — HOOK-01: HMAC header, retry logic, 7-retry exhaustion; HOOK-04: circuit breaker
- [x] `tests/webhooks/test_controllers.py` — HOOK-01–04: all 8 HTTP endpoints (register, list, update, delete, rotate-secret, history, retry, re-enable)
- [x] `tests/webhooks/test_checks.py` — HOOK-01: `manage.py check` validates `WEBHOOK_EVENTS` setting

---

## Manual-Only Verifications

| Behavior                                         | Requirement | Why Manual                                               | Test Instructions                                                                                                                                            |
| ------------------------------------------------ | ----------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Email notification when endpoint disabled        | HOOK-04     | Requires real email delivery in test env                 | Trigger 5 consecutive failures against a test endpoint; verify org admin inbox receives notification with endpoint URL and last failure reason               |
| HMAC signature verification by external consumer | HOOK-01     | Requires external HTTP server acting as webhook receiver | Use `ngrok` + simple Flask server to receive webhook, verify `X-Webhook-Signature: sha256=<hex>` matches computed HMAC-SHA256 of payload using shared secret |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ Nyquist-compliant (audited 2026-03-13)

---

## Validation Audit 2026-03-13

| Metric     | Count                |
| ---------- | -------------------- |
| Gaps found | 0                    |
| Resolved   | 0                    |
| Escalated  | 0                    |
| Tests run  | 36 passed, 0 skipped |
