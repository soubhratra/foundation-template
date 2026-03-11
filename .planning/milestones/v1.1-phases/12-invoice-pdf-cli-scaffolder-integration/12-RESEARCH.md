# Phase 12: Invoice PDF + CLI Scaffolder Integration - Research

**Researched:** 2026-03-10
**Domain:** WeasyPrint PDF generation, Celery async tasks, CLI scaffolder billing removal
**Confidence:** HIGH

---

<phase_requirements>

## Phase Requirements

| ID       | Description                                                                                                                 | Research Support                                                                                                                                                                               |
| -------- | --------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| INV-02   | User can download an invoice as a server-generated PDF (WeasyPrint + Jinja2 template)                                       | WeasyPrint `HTML(string=...).write_pdf()` generates bytes from Jinja2-rendered HTML; new controller endpoint streams bytes as `application/pdf` response                                       |
| INV-03   | PDF generation runs as an async Celery task (never in the request cycle)                                                    | `@shared_task` pattern already established in `tasks.py`; POST returns task_id immediately; polling endpoint checks `AsyncResult(task_id).state`                                               |
| SCAFF-01 | Billing module included by default when creating a new project                                                              | Billing is already in the template's `INSTALLED_APPS` — no new work needed; just confirm it survives the copy step and validate that no billing removal runs by default                        |
| SCAFF-02 | User can exclude billing via `--without billing` flag (or interactive prompt)                                               | `prompts.ts` `SelectedFeatures` type + `promptFeatures()` must add `"billing"` option with `initialValues` including it by default; `index.ts` calls `removeBillingModule()` when not selected |
| SCAFF-03 | Billing removal deletes `apps/api/apps/billing/`, frontend billing pages, billing deps, and comment-delimited config blocks | `remove.ts` pattern already exists for AI/mobile/landing/web — `removeBillingModule()` follows the same structure; BILLING_START/BILLING_END markers already present in `urls.py` and settings |
| SCAFF-04 | CI test verifies `manage.py check` passes with billing removed from `INSTALLED_APPS`                                        | New test in `validation-runner.ts` or a separate pytest file; runs `python manage.py check` after billing removal; already piped through `execa` in the validation runner                      |

</phase_requirements>

---

## Summary

Phase 12 closes out the v1.1 Billing milestone with two independent tracks: server-side invoice PDF generation and CLI scaffolder opt-out for billing. These are largely self-contained and can be planned as separate work streams.

**Invoice PDF track (INV-02, INV-03):** WeasyPrint converts a Jinja2-rendered HTML template to PDF bytes. The key constraint is that PDF generation must not block an HTTP request — the established Celery `@shared_task` pattern already present in `tasks.py` is the correct vehicle. The endpoint returns a task ID immediately; a second polling endpoint returns the PDF bytes (or status) when the task completes. The `Payment` model already stores all fields needed for a minimal invoice (amount, currency, created_at, stripe_payment_intent_id). WeasyPrint requires system-level Pango/cairo libraries — the Docker Compose setup and Dockerfile must declare these dependencies.

**Scaffolder track (SCAFF-01 through SCAFF-04):** The CLI already has a complete remove pattern for AI, mobile, landing, and web features. Billing removal follows the same structure in `remove.ts`. The codebase already has comment-delimited BILLING_START/BILLING_END markers in `urls.py` and BILLING MODULE / END BILLING MODULE markers in `base.py`, plus a comment on the `apps.billing` INSTALLED_APPS line. The `prompts.ts` feature list needs a `"billing"` option added with default `true`. A CI validation test runs `manage.py check` against the output directory after billing removal to confirm clean separation.

**Primary recommendation:** Use `weasyprint>=62.0` (pure-Python wheels available since v53, but Pango is still required at runtime for text shaping). Store generated PDFs in-memory via `write_pdf(target=None)` and return the bytes from the Celery task result. For the scaffolder, model `removeBillingModule()` exactly on `removeAIModule()` — it is the most complex existing removal function and covers the right pattern.

---

## Standard Stack

### Core

| Library               | Version                               | Purpose                          | Why Standard                                                                       |
| --------------------- | ------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------- |
| weasyprint            | `>=62.0,<70`                          | HTML+CSS to PDF                  | Project requirement (INV-02); handles print CSS, flexbox, page breaks              |
| jinja2                | already installed (transitive)        | Template rendering for PDF HTML  | Standalone from Django's template engine; direct API for in-memory rendering       |
| celery[redis]         | `>=5.6.2` (already in pyproject.toml) | Async task queue                 | Already in project; `@shared_task` pattern already established in `tasks.py`       |
| django-celery-results | `>=2.6.0` (already installed)         | Task result storage in Django DB | `CELERY_RESULT_BACKEND = "django-db"` already configured; `AsyncResult` queries it |

### Supporting

| Library                   | Version                          | Purpose                                 | When to Use                                              |
| ------------------------- | -------------------------------- | --------------------------------------- | -------------------------------------------------------- |
| celery.result.AsyncResult | built-in                         | Polling task state by task_id           | In the polling endpoint to check PENDING/SUCCESS/FAILURE |
| fs-extra                  | already in create-foundation-app | File/directory operations in scaffolder | All existing `remove*.ts` functions use it               |
| execa                     | already in create-foundation-app | Run shell commands (manage.py check)    | Already used in `validation-runner.ts`                   |

### Alternatives Considered

| Instead of             | Could Use                  | Tradeoff                                                                                                                          |
| ---------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| WeasyPrint             | ReportLab                  | ReportLab uses its own drawing API, not HTML/CSS — much harder to style; WeasyPrint lets designers use HTML/CSS they already know |
| WeasyPrint             | pdfkit (wkhtmltopdf)       | wkhtmltopdf is unmaintained; requires a headless browser; WeasyPrint is pure Python + Pango                                       |
| WeasyPrint             | Stripe-hosted invoice PDFs | Explicitly excluded — expire, cannot be rebranded (see REQUIREMENTS.md Out of Scope)                                              |
| In-memory bytes        | Writing to disk / S3       | BILL-10 (PDF caching to S3) is deferred to v2 — for now, generate on demand, return bytes directly from task result               |
| Django template engine | Jinja2 standalone          | Django templates lack block expressions needed for clean invoice layout; Jinja2 gives filters like `{{ amount                     | float / 100 }}` directly |

**Installation:**

```bash
# Python — add to pyproject.toml [project] dependencies
uv add "weasyprint>=62.0,<70"

# System deps — add to Dockerfile (already has Python base)
# Debian/Ubuntu (matches the project's Docker base):
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

Note: Jinja2 is already transitively installed (LangChain pulls it in). Declare it explicitly in `pyproject.toml` under `billing` dependency group or project deps to make it intentional.

---

## Architecture Patterns

### Recommended File Structure (billing module additions)

```
apps/api/apps/billing/
├── templates/           # NEW — Jinja2 PDF templates
│   └── billing/
│       └── invoice.html.j2   # Invoice PDF template
├── pdf.py              # NEW — PDF generation logic (WeasyPrint wrapper)
├── tasks.py            # EXISTING — add generate_invoice_pdf task
├── controllers.py      # EXISTING — add POST /invoices/{invoice_id}/pdf + GET /invoices/pdf-status/{task_id}
└── schemas.py          # EXISTING — add PdfTaskOut schema

packages/create-foundation-app/src/
├── remove.ts           # EXISTING — add removeBillingModule()
├── prompts.ts          # EXISTING — add "billing" to SelectedFeatures + promptFeatures()
└── index.ts            # EXISTING — call removeBillingModule() when billing not selected
```

### Pattern 1: Async PDF Generation via Celery

**What:** POST endpoint enqueues a Celery task, returns task_id. GET polling endpoint checks `AsyncResult(task_id).state`. When `SUCCESS`, the PDF bytes are base64-encoded in the result and returned to the client.

**When to use:** Any operation that takes >100ms and must not block an HTTP worker. WeasyPrint PDF generation is typically 300ms–2s.

**Why in-memory bytes (not file storage):** BILL-10 (PDF caching to S3) is deferred to v2. For now, generate on demand. Celery result bytes are stored in `django_celery_results_taskresult` table via the `django-db` backend — sufficient for short-lived task results.

**Example:**

```python
# Source: Celery docs + project's existing tasks.py pattern

# apps/billing/pdf.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import weasyprint

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_invoice_pdf(invoice_data: dict) -> bytes:
    """Render invoice data to PDF bytes using Jinja2 + WeasyPrint.

    Import weasyprint inside function body — avoids Celery multi-process
    issues with WeasyPrint's internal state (documented in WeasyPrint
    GitHub issue #684).
    """
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    tmpl = env.get_template("billing/invoice.html.j2")
    html_string = tmpl.render(invoice=invoice_data)
    return weasyprint.HTML(string=html_string).write_pdf()


# apps/billing/tasks.py (addition)
@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), default_retry_delay=2)
def generate_invoice_pdf(self, invoice_data: dict) -> bytes:
    """Generate invoice PDF asynchronously. Returns raw PDF bytes.

    Caller uses AsyncResult(task_id).result to retrieve bytes after SUCCESS.
    """
    from apps.billing.pdf import render_invoice_pdf
    return render_invoice_pdf(invoice_data)
```

**Example controller endpoints:**

```python
# apps/billing/controllers.py additions

@route.post("/invoices/{invoice_id}/pdf", response=PdfTaskOut, url_name="billing-invoice-pdf")
def request_invoice_pdf(self, request, invoice_id: str):
    """Enqueue PDF generation for the given invoice. Returns task_id for polling."""
    invoice_data = self.service.get_invoice_for_pdf(request.user, invoice_id)
    task = generate_invoice_pdf.delay(invoice_data)
    return PdfTaskOut(task_id=task.id, status="pending")

@route.get("/invoices/pdf-status/{task_id}", url_name="billing-pdf-status")
def get_pdf_status(self, request, task_id: str):
    """Poll PDF generation status. When status=success, returns base64-encoded PDF."""
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    if result.state == "SUCCESS":
        import base64
        return api.create_response(request, {
            "status": "success",
            "pdf_base64": base64.b64encode(result.result).decode(),
        })
    elif result.state == "FAILURE":
        return api.create_response(request, {"status": "failed"}, status=500)
    return api.create_response(request, {"status": result.state.lower()})
```

### Pattern 2: Billing Module Removal in CLI Scaffolder

**What:** `removeBillingModule()` in `remove.ts` — mirrors the existing `removeAIModule()` pattern exactly.

**Steps:**

1. Delete `apps/api/apps/billing/` directory
2. Remove `apps.billing` from INSTALLED_APPS (line has `# BILLING MODULE — remove this line` comment)
3. Remove `# BILLING MODULE ... # END BILLING MODULE` block from `base.py`
4. Remove `BILLING_ADAPTER = ...` from `development.py`
5. Remove `# BILLING_START ... # BILLING_END` block from `urls.py`
6. Remove `apps/web/app/(dashboard)/billing/` directory
7. Remove `billing.config.ts` from `apps/web/`
8. Remove billing Python deps from `pyproject.toml` (`stripe`, `weasyprint`)

**`prompts.ts` change:**

```typescript
// Add to SelectedFeatures type
export type SelectedFeatures = Array<"web" | "mobile" | "landing" | "ai" | "billing">;

// Add to multiselect options in promptFeatures():
{
  value: "billing",
  label: "Billing Module (Stripe payments + invoice PDFs)",
},
// Add "billing" to initialValues: ["web", "mobile", "landing", "ai", "billing"]
```

**`index.ts` change:**

```typescript
if (!config.features.includes("billing")) {
  await removeBillingModule(config.outputDir);
}
```

**Marker-based block removal in `base.py` (BILLING MODULE block):**

```typescript
// Pattern: remove everything between and including marker lines
const billingBlockRegex =
  /\n# -----------+\n# BILLING MODULE\n# -----------+[\s\S]*?# -----------+\n# END BILLING MODULE\n# -----------+/;
settingsContent = settingsContent.replace(billingBlockRegex, "");
```

**BILLING_START/BILLING_END removal in `urls.py`:**

```typescript
const billingUrlsRegex = /\s*# BILLING_START\n\s*path[^\n]+\n\s*# BILLING_END/;
urlsContent = urlsContent.replace(billingUrlsRegex, "");
// Also remove the import line:
urlsContent = urlsContent.replace(/\nfrom apps\.billing import webhooks as billing_views\n/, "\n");
```

### Pattern 3: Invoice Data for PDF

The `Payment` model fields available for invoice rendering:

- `stripe_payment_intent_id` — used as invoice reference number
- `amount` (Decimal, stored as dollars) — payment amount
- `currency` — e.g. "usd"
- `status` — "succeeded", "failed"
- `created_at` — timestamp

The `BillingService.list_invoices()` already calls `adapter.list_invoices()`. For PDF generation, the service needs a new method `get_invoice_for_pdf(user, invoice_id)` that returns a `dict` with all fields needed by the Jinja2 template plus user metadata (name, email).

**Note:** `invoice_id` in the existing schema is `str` (from Stripe's `inv_xxx` format). The `Payment` model's `stripe_payment_intent_id` is the closest local identifier. The service needs to map between these — or use the Payment's `pk` as the local invoice ID for PDF requests.

### Anti-Patterns to Avoid

- **Generating PDF in the request cycle:** WeasyPrint calls Pango/cairo at the OS level — not suitable for synchronous HTTP handlers. Always `@shared_task`.
- **Importing WeasyPrint at module top-level in tasks.py:** Causes Celery multi-process crashes (WeasyPrint issue #684). Import inside the function body only.
- **Using Django's template engine for PDF templates:** Django templates do not support the filter expressions and whitespace control that make clean invoice HTML — use Jinja2's `Environment` directly.
- **Storing PDF bytes as base64 in the Celery result long-term:** Fine for < 5 minutes of polling; for longer-lived results, store to S3 (BILL-10, deferred to v2). Add a comment warning about this limit.
- **Using regex on Python files without anchoring on the comment markers:** The billing block in `base.py` has explicit comment delimiters (`# BILLING MODULE` / `# END BILLING MODULE`) — use these, not fragile line-count heuristics.

---

## Don't Hand-Roll

| Problem                               | Don't Build                          | Use Instead                                                   | Why                                                                                                       |
| ------------------------------------- | ------------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| HTML to PDF conversion                | Custom PDF drawing code              | WeasyPrint `HTML(string=...).write_pdf()`                     | WeasyPrint handles CSS layout, page breaks, fonts, Unicode — weeks of work to replicate                   |
| Template rendering for PDF            | Django's template engine             | Jinja2 `Environment` standalone                               | Direct API, richer filter support, no Django request context needed in Celery tasks                       |
| Task status storage                   | Custom database table for task state | `AsyncResult` + `django-celery-results` (already configured)  | `django_celery_results_taskresult` table already exists; `AsyncResult(task_id).state` queries it          |
| Retry logic for PDF task              | Manual try/except with sleep         | `autoretry_for=(Exception,), max_retries=3` on `@shared_task` | Already established pattern in existing `tasks.py`                                                        |
| File/directory deletion in scaffolder | os.unlink/shutil.rmtree              | `fs-extra`'s `remove()` (already in use)                      | Handles non-existent paths gracefully; consistent with existing remove functions                          |
| CLI arg parsing for `--without`       | Manual `process.argv` parsing        | Add `"billing"` to the existing `multiselect` prompt          | The CLI is interactive-first; SCAFF-02 allows either flag or prompt — start with prompt, flag is optional |

**Key insight:** The entire invoice PDF feature is ~3 new files (`pdf.py`, `invoice.html.j2`, small controller additions) because WeasyPrint + Jinja2 handle all the complexity. The scaffolder changes are pure structural additions to existing patterns.

---

## Common Pitfalls

### Pitfall 1: WeasyPrint System Dependencies Missing in Docker

**What goes wrong:** `weasyprint` installs via pip but crashes at runtime with `OSError: cannot load library 'libpango-1.0-0.so.0'`
**Why it happens:** WeasyPrint uses CFFI to call Pango/cairo C libraries — these must be installed at the OS level, not via pip
**How to avoid:** Add to `Dockerfile` before `pip install`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info && \
    rm -rf /var/lib/apt/lists/*
```

**Warning signs:** Tests pass locally (if Pango is on the dev machine via brew/apt) but fail in CI/Docker

### Pitfall 2: WeasyPrint Import at Module Level in Celery Worker

**What goes wrong:** Celery worker crashes on startup or during task execution with threading/GIL errors
**Why it happens:** WeasyPrint uses Pango's GLib internally; importing at module level before Celery forks the worker causes shared state issues
**How to avoid:** Always `import weasyprint` inside the task function body, or inside `render_invoice_pdf()` which is called from the task — not at module level in `tasks.py` or `pdf.py`
**Warning signs:** Celery worker starts but crashes on first PDF task, often with `Segmentation fault` or `GLib-GObject-CRITICAL` errors

### Pitfall 3: invoice_id Mapping Between Stripe and Local Payment Records

**What goes wrong:** The frontend sends `invoice_id` (Stripe's `inv_xxx` format) but the `Payment` model stores `stripe_payment_intent_id` (not `stripe_invoice_id`)
**Why it happens:** Phase 11's invoice listing proxies Stripe's invoice objects which have their own IDs; the local `Payment` model tracks payment intents, not invoices
**How to avoid:** Two options:

1. Use `Payment.pk` as the PDF request identifier — simple but uses internal DB IDs in URLs
2. Add `stripe_invoice_id` to `Payment` model and populate it from `invoice.payment_succeeded` webhook (involves a migration)
   Recommended: Use `Payment.pk` for this phase; option 2 is additive and can be done later
   **Warning signs:** `Payment.objects.get(stripe_payment_intent_id=invoice_id)` silently returns no results

### Pitfall 4: Billing Removal Leaves Orphan Import in urls.py

**What goes wrong:** After removing the `BILLING_START/BILLING_END` block from `urls.py`, the `from apps.billing import webhooks as billing_views` import remains, causing `ImportError` when `manage.py check` runs
**Why it happens:** The import is on line 17 of `urls.py`, separate from the URL pattern block
**How to avoid:** `removeBillingModule()` must remove BOTH the import line AND the `BILLING_START/BILLING_END` URL block. Check the import line explicitly with regex
**Warning signs:** `manage.py check` exits with `ModuleNotFoundError: No module named 'apps.billing'` after scaffolding

### Pitfall 5: development.py BILLING_ADAPTER Line Not Removed

**What goes wrong:** `manage.py check` fails with `django.core.exceptions.ImproperlyConfigured` or silent startup failure because `BILLING_ADAPTER` references the deleted `apps.billing.stub_adapter.StubAdapter`
**Why it happens:** `development.py` has `BILLING_ADAPTER = "apps.billing.stub_adapter.StubAdapter"` — removing `apps.billing` from INSTALLED_APPS is not enough
**How to avoid:** `removeBillingModule()` must also remove or comment out the `BILLING_ADAPTER` line from `development.py`
**Warning signs:** `manage.py check` passes initially but fails when settings are loaded in development mode

### Pitfall 6: Celery Result Size Limit

**What goes wrong:** Large PDF bytes (>1MB) stored in the `django_celery_results_taskresult` table may be rejected or cause slow queries
**Why it happens:** `django_celery_results` stores results as text in `result` column — base64-encoded PDF bytes can be large
**How to avoid:** For this phase, add a note that PDF size is bounded by invoice data (typically <100KB). Full solution (BILL-10) uses S3. Add a `MAX_PDF_BYTES = 512 * 1024` guard in `generate_invoice_pdf` and raise `ValueError` if exceeded
**Warning signs:** Task fails with database column overflow error

---

## Code Examples

### WeasyPrint PDF Generation (Verified Pattern)

```python
# Source: WeasyPrint docs (doc.courtbouillon.org/weasyprint/stable/first_steps.html)
# + Josh Karamuth's guide (joshkaramuth.com/blog/generate-good-looking-pdfs-weasyprint-jinja2/)

from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def render_invoice_pdf(invoice_data: dict) -> bytes:
    """Render invoice Jinja2 template to PDF bytes.

    NOTE: weasyprint is imported inside this function, not at module level.
    Importing at module level in a Celery worker context causes GLib threading
    issues (WeasyPrint GitHub issue #684).
    """
    import weasyprint  # lazy import — required for Celery safety

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    tmpl = env.get_template("billing/invoice.html.j2")
    html_string = tmpl.render(invoice=invoice_data)
    # write_pdf(target=None) returns bytes in memory — no file I/O
    return weasyprint.HTML(string=html_string).write_pdf()
```

### Celery Task Returning Bytes

```python
# Source: Celery docs (docs.celeryq.dev/en/stable/userguide/tasks.html)
# + project's existing tasks.py @shared_task pattern

from celery import shared_task


@shared_task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    default_retry_delay=2,
)
def generate_invoice_pdf(self, invoice_data: dict) -> bytes:
    """Generate invoice PDF bytes asynchronously.

    Returns raw bytes stored in django_celery_results_taskresult.
    Client polls GET /billing/invoices/pdf-status/{task_id} until state=SUCCESS.
    """
    from apps.billing.pdf import render_invoice_pdf  # lazy import avoids circular
    return render_invoice_pdf(invoice_data)
```

### Polling with AsyncResult

```python
# Source: Celery docs — AsyncResult state checking
from celery.result import AsyncResult

def check_pdf_task(task_id: str) -> dict:
    result = AsyncResult(task_id)
    # result.state: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY"
    if result.state == "SUCCESS":
        return {"status": "success", "result": result.result}  # result.result = bytes
    elif result.state == "FAILURE":
        return {"status": "failed", "error": str(result.result)}
    return {"status": result.state.lower()}
```

### Minimal Invoice Jinja2 Template Structure

```html
<!-- apps/billing/templates/billing/invoice.html.j2 -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <style>
      @page {
        size: A4;
        margin: 2cm;
      }
      body {
        font-family: sans-serif;
        font-size: 12px;
        color: #111;
      }
      .header {
        display: flex;
        justify-content: space-between;
      }
      .invoice-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 2em;
      }
      .invoice-table th,
      .invoice-table td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
      }
      .amount {
        text-align: right;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <div><strong>Invoice</strong></div>
      <div>#{{ invoice.reference }}</div>
    </div>
    <p>Date: {{ invoice.date }}</p>
    <p>To: {{ invoice.customer_email }}</p>
    <table class="invoice-table">
      <thead>
        <tr>
          <th>Description</th>
          <th class="amount">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{{ invoice.description }}</td>
          <td class="amount">
            {{ "%.2f" | format(invoice.amount) }} {{ invoice.currency | upper }}
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
```

### Scaffolder removeBillingModule() Skeleton

```typescript
// Source: existing removeAIModule() in packages/create-foundation-app/src/remove.ts

import { readFile, writeFile, remove } from "fs-extra";
import { join } from "node:path";
import { logger } from "./utils.js";

export async function removeBillingModule(outputDir: string): Promise<void> {
  logger.info("Removing billing module...");

  // 1. Delete billing Django app
  await remove(join(outputDir, "apps/api/apps/billing"));

  // 2. Remove "apps.billing" from INSTALLED_APPS in base.py
  const basePyPath = join(outputDir, "apps/api/config/settings/base.py");
  let baseContent = await readFile(basePyPath, "utf-8");
  baseContent = baseContent.replace(/\s*"apps\.billing",[^\n]*\n/g, "");
  // Remove the BILLING MODULE settings block
  baseContent = baseContent.replace(
    /\n# -{10,}\n# BILLING MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END BILLING MODULE\n# -{10,}/,
    "",
  );
  await writeFile(basePyPath, baseContent, "utf-8");

  // 3. Remove BILLING_ADAPTER line from development.py
  const devPyPath = join(outputDir, "apps/api/config/settings/development.py");
  let devContent = await readFile(devPyPath, "utf-8");
  devContent = devContent.replace(/^BILLING_ADAPTER\s*=.*$\n?/m, "");
  // Also remove the comment above it
  devContent = devContent.replace(/^# Use StubAdapter[^\n]*\n# Switch[^\n]*\n/m, "");
  await writeFile(devPyPath, devContent, "utf-8");

  // 4. Remove BILLING_START/BILLING_END block + billing import from urls.py
  const urlsPath = join(outputDir, "apps/api/config/urls.py");
  let urlsContent = await readFile(urlsPath, "utf-8");
  urlsContent = urlsContent.replace(/\s*# BILLING_START\n\s*path[^\n]+\n\s*# BILLING_END/, "");
  urlsContent = urlsContent.replace(
    /\nfrom apps\.billing import webhooks as billing_views\n/,
    "\n",
  );
  await writeFile(urlsPath, urlsContent, "utf-8");

  // 5. Remove billing Python deps from pyproject.toml
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  let pyprojectContent = await readFile(pyprojectPath, "utf-8");
  const billingPyDeps = ["stripe", "weasyprint"];
  for (const dep of billingPyDeps) {
    pyprojectContent = pyprojectContent.replace(new RegExp(`^\\s*"${dep}[^"]*",?\\s*$`, "gm"), "");
  }
  // Remove the [dependency-groups] billing section entirely
  pyprojectContent = pyprojectContent.replace(
    /\[dependency-groups\]\nbilling = \[[^\]]*\]\n?/s,
    "",
  );
  await writeFile(pyprojectPath, pyprojectContent, "utf-8");

  // 6. Remove frontend billing pages and config
  await remove(join(outputDir, "apps/web/app/(dashboard)/billing"));
  await remove(join(outputDir, "apps/web/billing.config.ts"));

  logger.info("✓ Billing module removed successfully");
}
```

---

## State of the Art

| Old Approach                       | Current Approach                 | When Changed         | Impact                                                                                                    |
| ---------------------------------- | -------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------- |
| wkhtmltopdf (headless browser)     | WeasyPrint (pure Python + Pango) | ~2018 onward         | wkhtmltopdf unmaintained since 2022; WeasyPrint actively maintained, Docker-friendly                      |
| Stripe-hosted invoice PDFs         | Server-side generation           | Project requirement  | Branded, non-expiring PDFs require server-side generation                                                 |
| Synchronous PDF generation in view | Celery async + task ID polling   | Django best practice | PDF generation is 300ms–2s; must not block HTTP workers                                                   |
| ReportLab programmatic drawing     | HTML/CSS template approach       | ~2015 onward         | HTML+CSS templates are designable and maintainable; ReportLab requires PDF-specific drawing API knowledge |

**Deprecated/outdated:**

- `django-weasyprint` class-based view package: Provides a synchronous class-based view — NOT suitable since INV-03 requires async generation. Use WeasyPrint's Python API directly.
- `pdfkit` (wkhtmltopdf wrapper): wkhtmltopdf last released 2022, no active maintenance, chromium-heavy — avoid.

---

## Open Questions

1. **invoice_id URL parameter: Stripe ID vs Payment.pk**
   - What we know: `InvoiceOut.invoice_id` is Stripe's `inv_xxx` ID; `Payment.stripe_payment_intent_id` is `pi_xxx`; there is no `stripe_invoice_id` field on `Payment`
   - What's unclear: Should the PDF download use Stripe invoice ID (requires adapter call to Stripe to get payment details) or Payment.pk (local, but internal DB ID exposed in URL)?
   - Recommendation: Use `Payment.pk` for this phase with `int` type in URL. The Ninja controller converts it cleanly. Avoids adapter call for PDF data. Document that BILL-10 upgrade can switch to S3 URLs with signed tokens.

2. **Celery result backend size: large PDFs in `django_celery_results_taskresult`**
   - What we know: `CELERY_RESULT_BACKEND = "django-db"` stores result bytes in a text column. Invoice PDFs for simple invoices should be ~50–150KB
   - What's unclear: Whether the `django_celery_results` text column has a practical size cap in PostgreSQL (it doesn't — PostgreSQL TEXT is unlimited, but base64 encoding adds 33% overhead)
   - Recommendation: Add a guard for invoices >512KB (unexpected), log a warning. Full fix is BILL-10 (S3 storage).

3. **Jinja2 template location: app-level vs project-level templates dir**
   - What we know: Django's `TEMPLATES` config has `"DIRS": []` and `APP_DIRS: True` — this is for Django's template engine, not Jinja2's `FileSystemLoader`
   - What's unclear: Should the template live in `apps/billing/templates/` (discovered by Django's app loader) or a separate `billing_templates/` subdirectory?
   - Recommendation: Place at `apps/api/apps/billing/templates/billing/invoice.html.j2`. Use Jinja2's `FileSystemLoader(Path(__file__).parent / "templates")` — no Django template discovery involved. Clean, self-contained.

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` — section included.

### Test Framework

| Property           | Value                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------- |
| Framework          | pytest 8.x + pytest-django 4.9                                                            |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`)                                   |
| Quick run command  | `cd apps/api && pytest tests/billing/test_pdf.py tests/billing/test_controllers.py -x -q` |
| Full suite command | `cd apps/api && pytest tests/ -q`                                                         |

### Phase Requirements to Test Map

| Req ID   | Behavior                                                                                       | Test Type        | Automated Command                                                        | File Exists?                          |
| -------- | ---------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------ | ------------------------------------- |
| INV-02   | `render_invoice_pdf(data)` returns non-empty bytes; response Content-Type is `application/pdf` | unit             | `pytest tests/billing/test_pdf.py -x`                                    | ❌ Wave 0                             |
| INV-02   | POST `/billing/invoices/{id}/pdf` returns `{"task_id": "...", "status": "pending"}`            | integration      | `pytest tests/billing/test_controllers.py::test_request_invoice_pdf -x`  | ❌ Wave 0 (new test in existing file) |
| INV-03   | `generate_invoice_pdf` is a `@shared_task`; `.delay()` returns AsyncResult                     | unit             | `pytest tests/billing/test_pdf.py::test_pdf_task_is_async -x`            | ❌ Wave 0                             |
| INV-03   | GET `/billing/invoices/pdf-status/{task_id}` returns `pending` when task not yet done          | unit             | `pytest tests/billing/test_controllers.py::test_pdf_polling_pending -x`  | ❌ Wave 0                             |
| SCAFF-01 | Template copy produces project with `apps.billing` in `INSTALLED_APPS`                         | manual           | n/a                                                                      | manual-only                           |
| SCAFF-02 | `removeBillingModule()` function exists and is called when billing not selected                | unit (TS)        | `cd packages/create-foundation-app && pnpm test`                         | ❌ Wave 0                             |
| SCAFF-03 | After `removeBillingModule(tmpDir)`, no billing files/directories remain                       | integration (TS) | `cd packages/create-foundation-app && pnpm test`                         | ❌ Wave 0                             |
| SCAFF-04 | `manage.py check` passes on the output dir after billing removal                               | CI integration   | `pytest tests/test_scaffolder_billing_removal.py -x` OR shell test in CI | ❌ Wave 0                             |

**SCAFF-04 implementation note:** `manage.py check` requires an installed Python environment in the test project. The most pragmatic approach is a shell-based CI step in the validation runner (`validation-runner.ts`) that runs `python manage.py check` after invoking `removeBillingModule()`. Alternatively, a pytest test using `subprocess.run` in a temp directory with `uv sync` + `manage.py check`.

### Sampling Rate

- **Per task commit:** `cd apps/api && pytest tests/billing/ -x -q`
- **Per wave merge:** `cd apps/api && pytest tests/ -q`
- **Phase gate:** Full suite green + manual scaffold smoke test before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/billing/test_pdf.py` — covers INV-02, INV-03 (new file)
- [ ] `apps/api/apps/billing/pdf.py` — production module to test against (new file)
- [ ] `apps/api/apps/billing/templates/billing/invoice.html.j2` — template required by `render_invoice_pdf` (new file)
- [ ] WeasyPrint system deps must be available in CI: add `apt-get install -y libpango-1.0-0 libpangoft2-1.0-0` to CI workflow or Docker image
- [ ] `packages/create-foundation-app/src/remove.ts` — `removeBillingModule()` function needed before scaffolder tests can run

---

## Sources

### Primary (HIGH confidence)

- WeasyPrint official docs (doc.courtbouillon.org/weasyprint/stable/first_steps.html) — installation requirements, `write_pdf()` API
- Celery official docs (docs.celeryq.dev/en/stable/userguide/tasks.html) — `AsyncResult` state API, `@shared_task` pattern
- Project codebase — `apps/api/apps/billing/tasks.py`, `controllers.py`, `schemas.py`, `stub_adapter.py`, `models.py`
- Project codebase — `packages/create-foundation-app/src/remove.ts`, `prompts.ts`, `index.ts`
- Project codebase — `apps/api/config/settings/base.py` (BILLING MODULE markers), `urls.py` (BILLING_START/BILLING_END markers)

### Secondary (MEDIUM confidence)

- Josh Karamuth's WeasyPrint + Jinja2 guide (joshkaramuth.com/blog/generate-good-looking-pdfs-weasyprint-jinja2/) — confirmed `HTML(string=...).write_pdf()` pattern, flexbox CSS for layout
- WeasyPrint GitHub issue #684 (github.com/Kozea/WeasyPrint/issues/684) — confirms lazy import requirement inside Celery tasks

### Tertiary (LOW confidence — flagged for validation)

- SCAFF-04 CI test strategy: `manage.py check` in temp directory via `subprocess` in pytest — pattern inferred from existing `validation-runner.ts` approach; needs validation in planning against actual CI setup

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — WeasyPrint is the project's explicit requirement; Celery already installed and configured; patterns confirmed via official docs
- Architecture: HIGH — invoice PDF pattern follows documented WeasyPrint + Celery patterns; scaffolder pattern follows 4 existing identical implementations in `remove.ts`
- Pitfalls: HIGH — WeasyPrint system dep and lazy-import issues verified via official docs and GitHub issues; billing removal edge cases derived from direct codebase inspection of all files that reference billing

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (WeasyPrint has stable API; Celery 5.x has stable `AsyncResult` API)
