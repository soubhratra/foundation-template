---
phase: 13
slug: structured-logging-distributed-tracing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| **Framework**          | pytest 8.x + pytest-django 4.9                          |
| **Config file**        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command**  | `cd apps/api && python -m pytest tests/core/ -x -q`     |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -q`             |
| **Estimated runtime**  | ~15 seconds                                             |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/core/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type            | Automated Command                                      | File Exists | Status     |
| -------- | ---- | ---- | ----------- | -------------------- | ------------------------------------------------------ | ----------- | ---------- |
| 13-01-01 | 01   | 0    | OBS-01      | unit                 | `python -m pytest tests/core/test_logging.py -x -q`    | ❌ W0       | ⬜ pending |
| 13-01-02 | 01   | 0    | OBS-01      | unit                 | `python -m pytest tests/core/test_middleware.py -x -q` | ❌ W0       | ⬜ pending |
| 13-01-03 | 01   | 0    | OBS-02      | unit                 | `python -m pytest tests/core/test_tracing.py -x -q`    | ❌ W0       | ⬜ pending |
| 13-02-01 | 02   | 1    | OBS-01      | unit                 | `python -m pytest tests/core/test_logging.py -x -q`    | ❌ W0       | ⬜ pending |
| 13-02-02 | 02   | 1    | OBS-01      | unit                 | `python -m pytest tests/core/test_middleware.py -x -q` | ❌ W0       | ⬜ pending |
| 13-03-01 | 03   | 2    | OBS-02      | unit                 | `python -m pytest tests/core/test_tracing.py -x -q`    | ❌ W0       | ⬜ pending |
| 13-03-02 | 03   | 2    | OBS-02      | smoke (manual)       | N/A                                                    | manual-only | ⬜ pending |
| 13-03-03 | 03   | 2    | OBS-02      | integration (manual) | N/A                                                    | manual-only | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/core/__init__.py` — test package init
- [ ] `apps/api/tests/core/test_logging.py` — covers OBS-01: structlog processor, renderer selection (DEBUG flag), trace_id/span_id injection, no-span omission
- [ ] `apps/api/tests/core/test_middleware.py` — covers OBS-01: request_id field, user_id field, method/path/status_code/duration_ms fields, X-Request-ID response header, context isolation between requests
- [ ] `apps/api/tests/core/test_tracing.py` — covers OBS-02: configure_otel() is no-op when env var absent, creates TracerProvider when env var set
- [ ] `uv add --dev pytest-structlog` — if not already installed (provides `structlog_capture` fixture and reset utilities)

---

## Manual-Only Verifications

| Behavior                                                                      | Requirement | Why Manual                            | Test Instructions                                                                                                                                       |
| ----------------------------------------------------------------------------- | ----------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Jaeger UI accessible at http://localhost:16686 after `docker compose up`      | OBS-02      | Requires running Docker Compose stack | Run `docker compose up -d`, open http://localhost:16686, confirm Jaeger UI loads                                                                        |
| Django view → Celery task trace propagation (same trace_id visible in Jaeger) | OBS-02      | Requires live Jaeger + Celery worker  | Run `docker compose up`, trigger a view that dispatches a Celery task, open Jaeger and confirm the trace spans both the Django view and the Celery task |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
