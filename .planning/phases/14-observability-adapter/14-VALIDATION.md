---
phase: 14
slug: observability-adapter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-11
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                   |
| ---------------------- | ------------------------------------------------------- |
| **Framework**          | pytest 8.x + pytest-django                              |
| **Config file**        | `apps/api/pyproject.toml` — `[tool.pytest.ini_options]` |
| **Quick run command**  | `cd apps/api && python -m pytest tests/core/ -x -q`     |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -x -q`          |
| **Estimated runtime**  | ~15 seconds                                             |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/core/test_observability.py -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                    | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | ------------------------------------------------------------------------------------ | ----------- | ---------- |
| 14-01-01 | 01   | 1    | OBS-03      | unit        | `pytest tests/core/test_observability.py::test_noop_adapter -x`                      | ❌ W0       | ⬜ pending |
| 14-01-02 | 01   | 1    | OBS-03      | unit (mock) | `pytest tests/core/test_observability.py::test_posthog_adapter_capture_exception -x` | ❌ W0       | ⬜ pending |
| 14-01-03 | 01   | 1    | OBS-03      | unit        | `pytest tests/core/test_observability.py::test_get_adapter_default -x`               | ❌ W0       | ⬜ pending |
| 14-02-01 | 02   | 1    | OBS-03      | unit        | `pytest tests/core/test_observability.py::test_middleware_process_exception -x`      | ❌ W0       | ⬜ pending |
| 14-02-02 | 02   | 1    | OBS-03      | unit        | `pytest tests/core/test_observability.py::test_middleware_user_context -x`           | ❌ W0       | ⬜ pending |
| 14-02-03 | 02   | 1    | OBS-03      | unit        | `pytest tests/core/test_observability.py::test_celery_signal_handler -x`             | ❌ W0       | ⬜ pending |
| 14-03-01 | 03   | 2    | OBS-03      | manual      | N/A — UI verification                                                                | N/A         | ⬜ pending |
| 14-04-01 | 04   | 2    | OBS-03      | integration | `pytest tests/test_scaffolder_observability_removal.py -x`                           | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/core/test_observability.py` — stubs for OBS-03 adapter unit tests, middleware tests, signal handler tests
- [ ] `apps/api/tests/test_scaffolder_observability_removal.py` — CLI removal integration test (modeled on `test_scaffolder_billing_removal.py`)

_(conftest.py and pytest infrastructure already exist — no Wave 0 framework gaps)_

---

## Manual-Only Verifications

| Behavior                                                                              | Requirement | Why Manual                                        | Test Instructions                                                                                                                                               |
| ------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Next.js page view events appear in PostHog dashboard without per-page instrumentation | OBS-03      | Requires live PostHog project with valid API key  | 1. Set `NEXT_PUBLIC_POSTHOG_KEY` + `NEXT_PUBLIC_POSTHOG_HOST`; 2. Navigate between pages in web app; 3. Verify `$pageview` events appear in PostHog Live Events |
| Expo mobile screen events appear in PostHog dashboard                                 | OBS-03      | Requires live PostHog project + device/simulator  | 1. Set `EXPO_PUBLIC_POSTHOG_KEY`; 2. Navigate between screens; 3. Verify `$screen` events appear in PostHog Live Events                                         |
| Session replay records correctly with inputs masked                                   | OBS-03      | Requires live PostHog with session replay enabled | 1. Set PostHog key with session replay plan; 2. Use web app; 3. Verify replay in PostHog dashboard shows masked inputs                                          |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
