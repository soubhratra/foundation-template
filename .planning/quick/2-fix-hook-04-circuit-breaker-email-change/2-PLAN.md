---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - apps/api/apps/webhooks/tasks.py
  - apps/api/tests/webhooks/test_tasks.py
autonomous: true
requirements: [HOOK-04]

must_haves:
  truths:
    - "Circuit breaker email uses template name 'webhooks/endpoint_disabled.html' (with .html extension)"
    - "Test asserts template_arg == 'webhooks/endpoint_disabled.html'"
    - "send_email_task can resolve the template at runtime without TemplateDoesNotExist"
  artifacts:
    - path: "apps/api/apps/webhooks/tasks.py"
      provides: "_handle_terminal_failure with corrected template_name"
      contains: "webhooks/endpoint_disabled.html"
    - path: "apps/api/tests/webhooks/test_tasks.py"
      provides: "Updated assertion matching new template_name"
      contains: "webhooks/endpoint_disabled.html"
  key_links:
    - from: "apps/api/apps/webhooks/tasks.py"
      to: "apps/api/apps/notifications/templates/email/webhooks/endpoint_disabled.html"
      via: "send_email(template_name=...) → send_email_task → render_to_string(f'email/{template_name}')"
      pattern: "webhooks/endpoint_disabled\\.html"
---

<objective>
Fix the circuit breaker notification email: the `template_name` argument passed to `send_email()` in `_handle_terminal_failure()` is missing the `.html` extension. At runtime `send_email_task` renders `f"email/{template_name}"`, so passing `"webhooks/endpoint_disabled"` causes a `TemplateDoesNotExist` error because the file on disk is `endpoint_disabled.html`. The fix changes the value to `"webhooks/endpoint_disabled.html"` and aligns the test assertion.

Purpose: Prevent silent email dispatch failure when a webhook endpoint is auto-disabled by the circuit breaker.
Output: Corrected `tasks.py` + matching test assertion.
</objective>

<execution_context>
@/Users/soubhratra/.claude/get-shit-done/workflows/execute-plan.md
@/Users/soubhratra/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix template_name in _handle_terminal_failure and update test assertion</name>
  <files>apps/api/apps/webhooks/tasks.py, apps/api/tests/webhooks/test_tasks.py</files>
  <action>
In `apps/api/apps/webhooks/tasks.py`, inside `_handle_terminal_failure()`, change the `send_email()` call:

BEFORE: template_name="webhooks/endpoint_disabled",
AFTER: template_name="webhooks/endpoint_disabled.html",

The `send_email_task` renders `f"email/{template_name}"`, so the full resolved path becomes `email/webhooks/endpoint_disabled.html`, which matches the file at `apps/api/apps/notifications/templates/email/webhooks/endpoint_disabled.html`.

In `apps/api/tests/webhooks/test_tasks.py`, update the assertion at line 239:

BEFORE: assert template_arg == "webhooks/endpoint_disabled"
AFTER: assert template_arg == "webhooks/endpoint_disabled.html"

No other changes needed. The STATE.md decision note for Phase 27 already documents the correct path (`email/webhooks/endpoint_disabled.html`) — this is a bug where the implementation diverged from the documented intent.
</action>
<verify>
<automated>cd /Users/soubhratra/workspace/foundation-template/apps/api && python -m pytest tests/webhooks/test_tasks.py -x -q 2>&1 | tail -20</automated>
</verify>
<done>All tests in test_tasks.py pass. The template_name argument in \_handle_terminal_failure is "webhooks/endpoint_disabled.html" with the .html extension.</done>
</task>

</tasks>

<verification>
Run the webhook task test suite:
  cd apps/api && python -m pytest tests/webhooks/test_tasks.py -v

All tests pass including the circuit breaker email test that asserts the template_name value.
</verification>

<success_criteria>

- `_handle_terminal_failure()` passes `template_name="webhooks/endpoint_disabled.html"` to `send_email()`
- Test assertion updated to `assert template_arg == "webhooks/endpoint_disabled.html"`
- `python -m pytest tests/webhooks/test_tasks.py -x` exits 0
  </success_criteria>

<output>
After completion, create `.planning/quick/2-fix-hook-04-circuit-breaker-email-change/2-SUMMARY.md`
</output>
