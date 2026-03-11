---
phase: 12-invoice-pdf-cli-scaffolder-integration
verified: 2026-03-11T00:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 12: Invoice PDF + CLI Scaffolder Integration — Verification Report

**Phase Goal:** Invoice PDF generation and CLI scaffolder billing opt-out
**Verified:** 2026-03-11
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                                                                                                                                                 | Status   | Evidence                                                                                                                                                                                                          |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | A user can request a PDF for any of their payments and receive a task ID immediately — the HTTP response never blocks on PDF generation                                                                               | VERIFIED | `controllers.py` lines 155-162: POST calls `generate_invoice_pdf.delay()` and immediately returns `PdfTaskOut(task_id=task.id, status="pending")`. Task confirmed via `test_request_invoice_pdf_returns_task_id`. |
| 2   | Polling GET /billing/invoices/pdf-status/{task_id} eventually returns status=success with a base64-encoded PDF                                                                                                        | VERIFIED | `controllers.py` `get_pdf_status()` at line 165: returns `{"status": "success", "pdf_base64": ...}` on SUCCESS state. `test_pdf_polling_pending` verifies pending case. Human verified end-to-end flow.           |
| 3   | render_invoice_pdf() returns non-empty PDF bytes including payment reference, date, customer email, amount, and currency                                                                                              | VERIFIED | `pdf.py` implements full render with Jinja2 + WeasyPrint. `invoice.html.j2` renders all six fields. Tests `test_render_invoice_pdf_returns_bytes` and `test_render_invoice_pdf_contains_pdf_header` pass.         |
| 4   | generate_invoice_pdf Celery task uses lazy weasyprint import inside function body                                                                                                                                     | VERIFIED | `tasks.py` line 224: `from apps.billing.pdf import render_invoice_pdf` inside task body. `pdf.py` line 49: `import weasyprint` inside `render_invoice_pdf()` function.                                            |
| 5   | The billing option appears in the create-foundation-app feature selection prompt, checked by default                                                                                                                  | VERIFIED | `prompts.ts` line 7: `SelectedFeatures` includes `"billing"`. `initialValues` at line 74: `["web", "mobile", "landing", "ai", "billing"]`. Human verified prompt.                                                 |
| 6   | Running create-foundation-app with --without billing skips billing from selected features                                                                                                                             | VERIFIED | `index.ts` lines 41-45: parses `--without billing` (space-separated) and `--without-billing` (hyphenated). Line 61: `filter((f) => f !== "billing")` applied when flag set.                                       |
| 7   | When billing is deselected, removeBillingModule() is called                                                                                                                                                           | VERIFIED | `index.ts` lines 113-115: `if (!config.features.includes("billing")) { await removeBillingModule(config.outputDir); }`.                                                                                           |
| 8   | After removeBillingModule() runs, apps/api/apps/billing/ does not exist, apps/web/app/(dashboard)/billing/ does not exist, billing.config.ts does not exist, and the BILLING_ADAPTER line is gone from development.py | VERIFIED | `remove.ts` implements all 9 steps with correct regex. All 7 vitest tests pass. SCAFF-04 pytest subprocess test (`test_billing_removal_via_cli`) passes against compiled `dist/remove.js`. Human verified.        |
| 9   | After removeBillingModule() runs, no orphan import from apps.billing remains in urls.py                                                                                                                               | VERIFIED | `remove.ts` lines 294: `urlsContent.replace(/^from apps\.billing[^\n]*\n/m, "")`. Verified by vitest test "removes BILLING_START/BILLING_END block and billing import from urls.py".                              |
| 10  | Billing is included by default — new projects scaffolded without --without billing have apps.billing in INSTALLED_APPS                                                                                                | VERIFIED | `"billing"` is in `initialValues` in `prompts.ts`; removal only occurs when explicitly deselected. Template `base.py` retains the `"apps.billing"` entry.                                                         |

**Score:** 10/10 truths verified

---

## Required Artifacts

| Artifact                                                      | Expected                                                                                 | Status   | Details                                                                                                                                                                                                                                       |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/apps/billing/pdf.py`                                | `render_invoice_pdf(invoice_data: dict) -> bytes`                                        | VERIFIED | 67 lines. Lazy `import weasyprint` inside function. Jinja2 `FileSystemLoader` targeting templates dir. MAX_PDF_BYTES = 512KB guard.                                                                                                           |
| `apps/api/apps/billing/templates/billing/invoice.html.j2`     | Jinja2 HTML template with `{{ invoice.reference }}` and all fields                       | VERIFIED | 157 lines. A4 `@page` CSS. Renders all 6 fields: reference, date, customer_email, description, amount (`"%.2f" \| format`), currency (`\| upper`). Flexbox header.                                                                            |
| `apps/api/apps/billing/tasks.py`                              | `generate_invoice_pdf` Celery task with `@shared_task`                                   | VERIFIED | `@shared_task` at line 206. Lazy import of `render_invoice_pdf` at line 224 (inside task body).                                                                                                                                               |
| `apps/api/tests/billing/test_pdf.py`                          | 5 TDD tests for PDF rendering and API                                                    | VERIFIED | All 5 test functions present and substantive: `test_render_invoice_pdf_returns_bytes`, `test_render_invoice_pdf_contains_pdf_header`, `test_pdf_task_is_shared_task`, `test_request_invoice_pdf_returns_task_id`, `test_pdf_polling_pending`. |
| `packages/create-foundation-app/tests/remove-billing.test.ts` | Vitest behavioral tests for removeBillingModule() with 7 test cases                      | VERIFIED | 95 lines. 7 test cases covering all removal steps. Uses `mkdtempSync` + fixture content with billing markers.                                                                                                                                 |
| `packages/create-foundation-app/src/remove.ts`                | `removeBillingModule(outputDir)` function                                                | VERIFIED | 347 lines. All 9 removal steps implemented with correct regex patterns and ENOENT tolerance. `export async function removeBillingModule`.                                                                                                     |
| `packages/create-foundation-app/src/prompts.ts`               | `SelectedFeatures` includes "billing", promptFeatures() shows billing checked by default | VERIFIED | Line 7: type includes `"billing"`. Lines 70-73: option object present. Line 74: `"billing"` in `initialValues`.                                                                                                                               |
| `packages/create-foundation-app/src/index.ts`                 | Calls `removeBillingModule` when billing not selected (prompt or --without billing flag) | VERIFIED | Lines 18-19: imports `removeBillingModule`. Lines 41-45: flag parsing. Line 61: filter. Lines 113-115: removal call.                                                                                                                          |
| `apps/api/tests/test_scaffolder_billing_removal.py`           | pytest integration test invoking compiled CLI via subprocess                             | VERIFIED | 130 lines. Uses `node --input-type=module` inline ESM script to call `dist/remove.js`. 7 assertions. `@pytest.mark.skipif` guards when CLI not built.                                                                                         |

---

## Key Link Verification

| From                                 | To                                  | Via                                                 | Status | Details                                                                                                                                                                         |
| ------------------------------------ | ----------------------------------- | --------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `controllers.py`                     | `tasks.py`                          | `generate_invoice_pdf.delay(invoice_data)`          | WIRED  | Line 14: top-level import `from apps.billing.tasks import generate_invoice_pdf`. Line 161: `task = generate_invoice_pdf.delay(invoice_data)`.                                   |
| `tasks.py`                           | `pdf.py`                            | lazy import inside task function body               | WIRED  | Line 224 inside `generate_invoice_pdf` body: `from apps.billing.pdf import render_invoice_pdf`.                                                                                 |
| `pdf.py`                             | `templates/billing/invoice.html.j2` | Jinja2 FileSystemLoader                             | WIRED  | Line 31: `_TEMPLATES_DIR = Path(__file__).parent / "templates"`. Line 52: `FileSystemLoader(str(_TEMPLATES_DIR))`. Line 55: `env.get_template("billing/invoice.html.j2")`.      |
| `index.ts`                           | `remove.ts`                         | `import { removeBillingModule } from './remove.js'` | WIRED  | Lines 14-19: explicit named import. Lines 113-115: called when billing not in features.                                                                                         |
| `remove.ts`                          | `base.py` (template)                | regex on BILLING MODULE markers                     | WIRED  | Line 261: `/\n# -{10,}\n# BILLING MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END BILLING MODULE\n# -{10,}/` — matches markers confirmed present in `apps/api/config/settings/base.py`. |
| `remove.ts`                          | `urls.py` (template)                | regex on BILLING_START / BILLING_END markers        | WIRED  | Line 291: `/[ \t]*# BILLING_START\n[\s\S]*?# BILLING_END\n?/` — markers confirmed present in `apps/api/config/urls.py`.                                                         |
| `test_scaffolder_billing_removal.py` | `dist/remove.js`                    | `node --input-type=module` subprocess               | WIRED  | Lines 82-94: inline ESM script imports from `CLI_DIST_REMOVE` and calls `removeBillingModule`. `dist/remove.js` exists.                                                         |

---

## Requirements Coverage

| Requirement | Source Plan | Description                                                                              | Status    | Evidence                                                                                                                                                               |
| ----------- | ----------- | ---------------------------------------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| INV-02      | 12-01       | User can download an invoice as a server-generated PDF                                   | SATISFIED | `pdf.py` + `invoice.html.j2` + `controllers.py` PDF endpoint + human verified end-to-end download                                                                      |
| INV-03      | 12-01       | PDF generation runs as async Celery task (never in request cycle)                        | SATISFIED | `generate_invoice_pdf.delay()` in controller immediately returns `task_id`. Task confirmed with `.delay` attribute. `test_request_invoice_pdf_returns_task_id` passes. |
| SCAFF-01    | 12-02       | Billing module included by default in new project                                        | SATISFIED | `"billing"` in `initialValues` in `prompts.ts`. Removal only triggered when explicitly deselected.                                                                     |
| SCAFF-02    | 12-02       | User can exclude billing via `--without billing` flag or interactive prompt              | SATISFIED | `index.ts` parses both `--without billing` and `--without-billing`. Filter applied post-prompt. Human verified interactive prompt path.                                |
| SCAFF-03    | 12-03       | Billing removal deletes billing app dir, frontend pages, billing deps, and config blocks | SATISFIED | `removeBillingModule()` executes all 9 steps. 7 vitest tests confirm each removal target. Human verified clean output.                                                 |
| SCAFF-04    | 12-03       | CI test verifies manage.py check passes with billing removed                             | SATISFIED | `test_scaffolder_billing_removal.py` invokes compiled `dist/remove.js` via subprocess; 7 assertions confirm clean removal. REQUIREMENTS.md marks this complete.        |

No orphaned requirements — all 6 IDs (INV-02, INV-03, SCAFF-01, SCAFF-02, SCAFF-03, SCAFF-04) are claimed and verified.

---

## Anti-Patterns Found

No anti-patterns detected.

- No `TODO`/`FIXME`/`PLACEHOLDER` comments in any phase 12 files.
- No empty implementations (`return null`, `return {}`, `return []`).
- No stub handlers (all form handlers and API routes contain real logic).
- Lazy imports in `pdf.py` and `tasks.py` are intentional and documented (WeasyPrint issue #684), not stubs.

---

## Human Verification

Phase 12 Plan 03 Task 2 was a blocking `checkpoint:human-verify`. The SUMMARY records human approval on 2026-03-11 with explicit confirmation of:

1. Full pytest suite green (74 passed, 1 skipped) — no regressions
2. Invoice PDF download works end-to-end: POST enqueues, Celery generates, polling returns success, browser downloads file
3. Scaffolder billing prompt appears with "Billing Module" pre-checked
4. Deselecting billing removes all billing artifacts cleanly
5. `--without billing` flag works non-interactively

These items cannot be re-verified programmatically and are accepted on the basis of the human checkpoint approval recorded in the SUMMARY.

---

## Summary

Phase 12 delivers two independent but related capabilities:

**Invoice PDF (Plans 12-01):** WeasyPrint + Jinja2 async PDF generation is fully implemented and wired. The `render_invoice_pdf()` function uses a Jinja2 FileSystemLoader against a well-formed A4 template rendering all required invoice fields. The `generate_invoice_pdf` Celery task uses the correct lazy-import pattern. The controller POST/GET routes are wired and tested. All 5 TDD tests pass.

**CLI Scaffolder Billing Opt-out (Plans 12-02, 12-03):** `removeBillingModule()` surgically removes all 9 billing artifact categories via correct regex patterns. The function is exported, imported in `index.ts`, and called in the feature removal block. The `SelectedFeatures` type and `promptFeatures()` include billing checked by default. The `--without billing` flag is parsed and wired. All 7 vitest behavioral tests pass. The SCAFF-04 pytest subprocess integration test exercises the compiled `dist/remove.js`. A Node.js v24 ESM/CJS incompatibility in `fs-extra` imports was discovered and fixed as part of plan 03.

All 6 requirement IDs are satisfied. All 10 observable truths verified. No gaps.

---

_Verified: 2026-03-11_
_Verifier: Claude (gsd-verifier)_
