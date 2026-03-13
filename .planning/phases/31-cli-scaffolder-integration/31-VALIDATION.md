---
phase: 31
slug: cli-scaffolder-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Framework**          | pytest 7.x (API) + Node.js (CLI integration)              |
| **Config file**        | `apps/api/pytest.ini`                                     |
| **Quick run command**  | `cd apps/api && python -m pytest tests/scaffolder/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest tests/scaffolder/ -v`    |
| **Estimated runtime**  | ~30 seconds                                               |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/scaffolder/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/scaffolder/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                        | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 31-01-01 | 01   | 1    | SCAFF-01    | unit        | `cd apps/api && python -m pytest tests/scaffolder/test_b2b_scaffold.py::test_scaffold_without_b2b -x -q` | ❌ W0       | ⬜ pending |
| 31-01-02 | 01   | 1    | SCAFF-01    | unit        | `cd apps/api && python -m pytest tests/scaffolder/test_b2b_scaffold.py::test_scaffold_with_b2b -x -q`    | ❌ W0       | ⬜ pending |
| 31-02-01 | 02   | 2    | SCAFF-01    | integration | `cd packages/create-foundation-app && pnpm build && node dist/index.js --help`                           | ✅          | ⬜ pending |
| 31-02-02 | 02   | 2    | SCAFF-01    | unit        | `cd apps/api && python -m pytest tests/scaffolder/ -x -q`                                                | ❌ W0       | ⬜ pending |
| 31-03-01 | 03   | 3    | SCAFF-01    | integration | `cd apps/api && python -m pytest tests/scaffolder/ -v`                                                   | ❌ W0       | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/scaffolder/test_b2b_scaffold.py` — test stubs for `test_scaffold_without_b2b` and `test_scaffold_with_b2b` (SCAFF-01)
- [ ] `apps/api/tests/scaffolder/__init__.py` — ensure scaffolder test package exists (may already exist from billing scaffold tests)

_If none: "Existing infrastructure covers all phase requirements."_

---

## Manual-Only Verifications

| Behavior                                               | Requirement | Why Manual            | Test Instructions                                                      |
| ------------------------------------------------------ | ----------- | --------------------- | ---------------------------------------------------------------------- |
| Interactive multiselect shows B2B unchecked by default | SCAFF-01    | Requires terminal TTY | Run `npx create-foundation-app my-test` and observe multiselect prompt |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
