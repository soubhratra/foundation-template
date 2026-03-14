---
phase: 31
slug: cli-scaffolder-integration
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
audited: 2026-03-13
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                               |
| ---------------------- | ------------------------------------------------------------------- |
| **Framework**          | pytest 7.x (API) + Node.js (CLI integration)                        |
| **Config file**        | `apps/api/pytest.ini`                                               |
| **Quick run command**  | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -x -q` |
| **Full suite command** | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -v`    |
| **Estimated runtime**  | ~4 seconds                                                          |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -x -q`
- **After every plan wave:** Run `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                                                         | File Exists | Status   |
| -------- | ---- | ---- | ----------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 31-01-01 | 01   | 1    | SCAFF-01    | unit        | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/test_b2b_scaffold.py::TestB2BScaffoldViaCLI::test_scaffold_without_b2b -x -q` | ✅          | ✅ green |
| 31-01-02 | 01   | 1    | SCAFF-01    | unit        | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/test_b2b_scaffold.py::TestB2BScaffoldViaCLI::test_scaffold_with_b2b -x -q`    | ✅          | ✅ green |
| 31-02-01 | 02   | 2    | SCAFF-01    | integration | `node packages/create-foundation-app/dist/index.js --help`                                                                                | ✅          | ✅ green |
| 31-02-02 | 02   | 2    | SCAFF-01    | unit        | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -x -q`                                                                       | ✅          | ✅ green |
| 31-03-01 | 03   | 3    | SCAFF-01    | integration | `cd apps/api && .venv/bin/python -m pytest tests/scaffolder/ -v`                                                                          | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

Wave 0 files were created in Plan 01 as TDD RED stubs and turned GREEN in Plan 02.

- [x] `apps/api/tests/scaffolder/test_b2b_scaffold.py` — created in Plan 01 (commit `722fb69`)
- [x] `apps/api/tests/scaffolder/__init__.py` — created in Plan 01 (commit `722fb69`)

---

## Manual-Only Verifications

| Behavior                                               | Requirement | Why Manual            | Test Instructions                                                      |
| ------------------------------------------------------ | ----------- | --------------------- | ---------------------------------------------------------------------- |
| Interactive multiselect shows B2B unchecked by default | SCAFF-01    | Requires terminal TTY | Run `npx create-foundation-app my-test` and observe multiselect prompt |

Human verified in Plan 03 Task 2.

---

## Validation Sign-Off

- [x] All tasks have automated verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 files exist and test GREEN (2 passed, 4.04s)
- [x] No watch-mode flags
- [x] Feedback latency < 30s (actual: ~4s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-03-13

---

## Validation Audit 2026-03-13

| Metric     | Count |
| ---------- | ----- |
| Gaps found | 0     |
| Resolved   | 0     |
| Escalated  | 0     |

All 5 tasks were COVERED at audit time. Test files created in Plan 01, GREEN since Plan 02. Wave 0 complete. 2 automated tests passing in 4.04s.
