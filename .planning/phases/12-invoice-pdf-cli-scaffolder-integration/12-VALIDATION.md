---
phase: 12
slug: invoice-pdf-cli-scaffolder-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                  |
| ---------------------- | ------------------------------------------------------ |
| **Framework**          | pytest 7.x + pytest-django                             |
| **Config file**        | `apps/api/pytest.ini`                                  |
| **Quick run command**  | `cd apps/api && python -m pytest tests/billing/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest tests/ -x -q`         |
| **Estimated runtime**  | ~30 seconds                                            |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/billing/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement | Test Type   | Automated Command                                                                                                                 | File Exists | Status     |
| -------- | ---- | ---- | ----------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------- |
| 12-01-01 | 01   | 1    | INV-02      | unit        | `cd apps/api && python -m pytest tests/billing/test_pdf.py -x -q`                                                                 | ❌ W0       | ⬜ pending |
| 12-01-02 | 01   | 1    | INV-02      | unit        | `cd apps/api && python -m pytest tests/billing/test_pdf.py -x -q`                                                                 | ❌ W0       | ⬜ pending |
| 12-01-03 | 01   | 1    | INV-03      | unit        | `cd apps/api && python -m pytest tests/billing/test_tasks.py -x -q`                                                               | ❌ W0       | ⬜ pending |
| 12-01-04 | 01   | 1    | INV-03      | integration | `cd apps/api && python -m pytest tests/billing/test_pdf_endpoint.py -x -q`                                                        | ❌ W0       | ⬜ pending |
| 12-02-01 | 02   | 2    | SCAFF-01    | integration | `cd packages/create-foundation-app && npx ts-node bin/cli.ts --without billing && cd /tmp/test-project && python manage.py check` | manual      | ⬜ pending |
| 12-02-02 | 02   | 2    | SCAFF-02    | unit        | `cd packages/create-foundation-app && npx vitest run tests/remove-billing.test.ts`                                                | ❌ W0       | ⬜ pending |
| 12-02-03 | 02   | 2    | SCAFF-03    | unit        | `cd packages/create-foundation-app && npx vitest run tests/remove-billing.test.ts`                                                | ❌ W0       | ⬜ pending |
| 12-02-04 | 02   | 2    | SCAFF-04    | integration | `cd packages/create-foundation-app && npx vitest run tests/scaffolder.test.ts`                                                    | ✅          | ⬜ pending |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [ ] `apps/api/tests/billing/test_pdf.py` — unit stubs for INV-02 (WeasyPrint wrapper, Jinja2 template rendering)
- [ ] `apps/api/tests/billing/test_tasks.py` — unit stubs for INV-03 (Celery task returns task ID, not PDF bytes)
- [ ] `apps/api/tests/billing/test_pdf_endpoint.py` — integration stubs for download endpoint (INV-03)
- [ ] `packages/create-foundation-app/tests/remove-billing.test.ts` — unit stubs for SCAFF-02/SCAFF-03 (billing file removal, marker stripping)

_Existing pytest infrastructure covers billing tests. Existing vitest infrastructure covers scaffolder tests._

---

## Manual-Only Verifications

| Behavior                                             | Requirement | Why Manual                                                      | Test Instructions                                                                                                      |
| ---------------------------------------------------- | ----------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--without billing` produces clean `manage.py check` | SCAFF-01    | Requires spawning a real scaffolded project in a temp directory | Run `create-foundation-app --without billing` in /tmp, install deps, run `python manage.py check` and confirm 0 errors |
| PDF renders correctly (fonts, layout, amounts)       | INV-02      | Visual rendering can't be asserted in unit tests                | Download a PDF for a seeded invoice; open in PDF viewer; verify all fields render correctly                            |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
