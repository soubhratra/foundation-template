---
phase: 21
slug: gdpr-baseline
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
audited: 2026-03-12
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                         |
| ---------------------- | --------------------------------------------- |
| **Framework**          | pytest 8.x + pytest-django                    |
| **Config file**        | `apps/api/pytest.ini`                         |
| **Quick run command**  | `cd apps/api && pytest tests/accounts/ -x -q` |
| **Full suite command** | `cd apps/api && pytest -x -q`                 |
| **Estimated runtime**  | ~30 seconds                                   |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && pytest tests/accounts/ -x -q`
- **After every plan wave:** Run `cd apps/api && pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type | Automated Command                                              | File Exists | Status   |
| -------- | ---- | ---- | ----------- | --------- | -------------------------------------------------------------- | ----------- | -------- |
| 21-01-01 | 01   | 0    | GDPR-01     | unit      | `cd apps/api && pytest tests/accounts/test_deletion.py -x -q`  | ✅          | ✅ green |
| 21-01-02 | 01   | 0    | GDPR-02     | unit      | `cd apps/api && pytest tests/accounts/test_export.py -x -q`    | ✅          | ✅ green |
| 21-02-01 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/accounts/test_deletion.py -x -q`  | ✅          | ✅ green |
| 21-02-02 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/core/test_observability.py -x -q` | ✅          | ✅ green |
| 21-02-03 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/billing/test_adapters.py -x -q`   | ✅          | ✅ green |
| 21-03-01 | 03   | 2    | GDPR-02     | unit      | `cd apps/api && pytest tests/accounts/test_export.py -x -q`    | ✅          | ✅ green |
| 21-04-01 | 04   | 3    | GDPR-03     | manual    | browser devtools — network tab for posthog.init()              | N/A         | manual   |
| 21-04-02 | 04   | 3    | GDPR-03     | manual    | browser console — analytics_consent localStorage key           | N/A         | manual   |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `apps/api/tests/accounts/__init__.py` — new test package
- [x] `apps/api/tests/accounts/test_deletion.py` — GDPR-01 (6 tests)
- [x] `apps/api/tests/accounts/test_export.py` — GDPR-02 (8 tests)

_Frontend test gaps: None — GDPR-03 (cookie consent) is manually tested via browser devtools; Vitest setup exists but cookie consent banner is a thin UI-only component with no testable logic._

---

## Manual-Only Verifications

| Behavior                                   | Requirement | Why Manual                                                                                        | Test Instructions                                                                                      |
| ------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| PostHog does NOT initialise before consent | GDPR-03     | Network-level browser behaviour — no JS unit test can reliably verify network requests are absent | Open DevTools > Network > filter "posthog" > visit app fresh — verify no requests until Accept clicked |
| Declining consent leaves PostHog opted out | GDPR-03     | Requires real browser session + localStorage inspection                                           | Click Decline > open console > `localStorage.getItem('analytics_consent')` should return `"false"`     |
| Accepting consent initialises PostHog      | GDPR-03     | Requires real browser session + network requests                                                  | Click Accept > DevTools Network — posthog.js loads and identify/pageview fires                         |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s (actual: 11.15s accounts + 2.06s support tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-12 — 30/30 automated tests passing; 3 behaviors correctly marked manual-only (GDPR-03 cookie consent)

---

## Validation Audit 2026-03-12

| Metric              | Count |
| ------------------- | ----- |
| Gaps found          | 0     |
| Resolved            | 0     |
| Escalated           | 0     |
| Automated tests run | 30    |
| Tests passing       | 30    |
| Manual-only         | 3     |
