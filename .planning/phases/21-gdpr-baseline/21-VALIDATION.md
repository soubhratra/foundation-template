---
phase: 21
slug: gdpr-baseline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-12
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

| Task ID  | Plan | Wave | Requirement | Test Type | Automated Command                                              | File Exists | Status     |
| -------- | ---- | ---- | ----------- | --------- | -------------------------------------------------------------- | ----------- | ---------- |
| 21-01-01 | 01   | 0    | GDPR-01     | unit      | `cd apps/api && pytest tests/accounts/test_deletion.py -x -q`  | ❌ W0       | ⬜ pending |
| 21-01-02 | 01   | 0    | GDPR-02     | unit      | `cd apps/api && pytest tests/accounts/test_export.py -x -q`    | ❌ W0       | ⬜ pending |
| 21-02-01 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/accounts/test_deletion.py -x -q`  | ❌ W0       | ⬜ pending |
| 21-02-02 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/core/test_observability.py -x -q` | ✅ partial  | ⬜ pending |
| 21-02-03 | 02   | 1    | GDPR-01     | unit      | `cd apps/api && pytest tests/billing/test_adapters.py -x -q`   | ✅ partial  | ⬜ pending |
| 21-03-01 | 03   | 2    | GDPR-02     | unit      | `cd apps/api && pytest tests/accounts/test_export.py -x -q`    | ❌ W0       | ⬜ pending |
| 21-04-01 | 04   | 3    | GDPR-03     | manual    | browser devtools — network tab for posthog.init()              | N/A         | ⬜ pending |
| 21-04-02 | 04   | 3    | GDPR-03     | manual    | browser console — analytics_consent localStorage key           | N/A         | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/accounts/__init__.py` — new test package (if missing)
- [ ] `apps/api/tests/accounts/test_deletion.py` — stubs for GDPR-01 (DELETE endpoint + Celery task cascade)
- [ ] `apps/api/tests/accounts/test_export.py` — stubs for GDPR-02 (GET export endpoint + schema)

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
