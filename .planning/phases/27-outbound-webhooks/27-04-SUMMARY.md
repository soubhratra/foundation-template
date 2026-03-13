---
phase: 27-outbound-webhooks
plan: "04"
subsystem: api
tags: [django-ninja-extra, webhooks, pydantic, permissions, crud, pagination]

# Dependency graph
requires:
  - phase: 27-02
    provides: WebhookEndpoint, WebhookDelivery, WebhookDeliveryAttempt models + generate_secret()
  - phase: 27-03
    provides: deliver_webhook Celery task for manual retry enqueue
  - phase: 26-03
    provides: IsOrgMember, IsOrgAdmin permission classes + request.org injection
provides:
  - WebhookEndpointController: POST/GET/PATCH/DELETE endpoints + rotate-secret + paginated delivery list
  - WebhookDeliveryController: delivery detail + manual retry (202)
  - schemas.py: EndpointIn, EndpointOut, EndpointCreateOut, EndpointUpdateIn, RotateSecretOut, DeliveryOut, DeliveryDetailOut, AttemptOut
affects: [28-api-keys, 30-admin-backoffice]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Do NOT use from __future__ import annotations in ninja_extra controllers or schemas — deferred type evaluation causes QueryParams.model_rebuild() PydanticUserError at runtime"
    - "Manual pagination (page: int, page_size: int query params + dict response) instead of @paginate decorator — @paginate is incompatible with ninja_extra controller methods (duplicate request argument)"
    - "Permission composition: IsAuthenticated + IsOrgMember on controller, IsOrgAdmin added per-route for write endpoints — never use IsOrgAdmin alone"
    - "Paginated delivery list annotates attempt_count via models.Count('attempts') on queryset — not stored on model"

key-files:
  created:
    - apps/api/apps/webhooks/schemas.py
    - apps/api/apps/webhooks/controllers.py
  modified:
    - apps/api/tests/webhooks/test_controllers.py

key-decisions:
  - "No from __future__ import annotations in schemas.py or controllers.py — pydantic v2 forward reference resolution breaks ninja's internal QueryParams model builder when annotations are deferred strings"
  - "Manual pagination over @paginate(PageNumberPagination) — ninja_extra routes inject self as first positional arg, causing 'got multiple values for argument request' error with the paginate decorator"
  - "list_deliveries returns dict {'items': [...], 'count': N} with page/page_size query params — consistent with PageNumberPagination response shape without the decorator"
  - "rotate-secret saves update_fields=['signing_key', 'secret_hash', 'updated_at'] — updated_at is auto_now but explicit listing ensures field is included in the partial update"

patterns-established:
  - "EndpointCreateOut vs EndpointOut split: create response has secret field (signing_key shown once), all subsequent reads use EndpointOut with no secret field"
  - "PATCH re-enable pattern: is_active=True → consecutive_failures=0 reset in same save() call via update_fields"

requirements-completed: [HOOK-01, HOOK-02, HOOK-03, HOOK-04]

# Metrics
duration: 11min
completed: 2026-03-13
---

# Phase 27 Plan 04: Outbound Webhooks — API Controllers Summary

**8 webhook HTTP endpoints across two Ninja Extra controllers — full CRUD, secret rotation, paginated delivery history, and manual retry — completing all HOOK requirements**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-03-13T11:42:04Z
- **Completed:** 2026-03-13T11:53:00Z
- **Tasks:** 2 (TDD: RED + GREEN commits)
- **Files modified:** 3

## Accomplishments

- `WebhookEndpointController`: POST /endpoints (create + return secret once), GET /endpoints (list, no secret), PATCH /endpoints/{id} (update + re-enable resets consecutive_failures), DELETE /endpoints/{id}, POST /endpoints/{id}/rotate-secret (new secret returned once), GET /endpoints/{id}/deliveries (paginated with attempt_count)
- `WebhookDeliveryController`: GET /deliveries/{id} (full detail with attempts list), POST /deliveries/{id}/retry (enqueues deliver_webhook.delay() → 202)
- All write endpoints require `IsOrgAdmin`; read endpoints require `IsOrgMember` only — authorization enforced per-route
- HTTPS-only validation on EndpointIn.url (Pydantic field_validator → 422 on http://)
- Both controllers auto-discovered via `api.auto_discover_controllers()` — no manual URL registration needed

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: test_controllers.py** - `8f556c6` (test)
2. **Task 1+2 GREEN: schemas.py + controllers.py** - `cf87853` (feat)

## Files Created/Modified

- `apps/api/apps/webhooks/schemas.py` — All request/response schemas: EndpointIn, EndpointOut, EndpointCreateOut, EndpointUpdateIn, RotateSecretOut, AttemptOut, DeliveryOut, DeliveryDetailOut
- `apps/api/apps/webhooks/controllers.py` — WebhookEndpointController + WebhookDeliveryController
- `apps/api/tests/webhooks/test_controllers.py` — 12-test suite covering all HOOK-01 through HOOK-04 requirements

## Decisions Made

- Removed `from __future__ import annotations` from both schemas.py and controllers.py. Ninja builds a Pydantic `QueryParams` model from the controller method's type annotations; with deferred evaluation the forward reference to `EndpointIn` can't be resolved at model_rebuild() time, causing a runtime `PydanticUserError`. Explicit (non-deferred) type hints resolve cleanly.
- Replaced `@paginate(PageNumberPagination, page_size=20)` with manual pagination. The decorator injects `request` as a keyword argument, but ninja_extra already passes `request` as the first positional arg to controller methods, causing `TypeError: got multiple values for argument 'request'`. Manual `page`/`page_size` query params with a `dict` response shape match PageNumberPagination's `{"items": [...], "count": N}` contract without the decorator.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed from **future** import annotations to fix Pydantic QueryParams forward reference error**

- **Found during:** Task 2 GREEN (first test run after implementation)
- **Issue:** `PydanticUserError: QueryParams is not fully defined; you should define EndpointIn, then call QueryParams.model_rebuild()` — runtime 500 error on POST /endpoints. The plan's provided code template included `from __future__ import annotations` which converts all type annotations to deferred strings. Ninja's internal model builder can't resolve the `EndpointIn` forward reference when building query params.
- **Fix:** Removed `from __future__ import annotations` from both schemas.py and controllers.py. Python 3.12 supports `X | None` syntax natively without the future import, so ruff auto-converted `Optional[str]` to `str | None` equivalents.
- **Files modified:** apps/api/apps/webhooks/schemas.py, apps/api/apps/webhooks/controllers.py
- **Verification:** 2 target tests pass green after fix
- **Committed in:** cf87853 (Task GREEN commit)

**2. [Rule 1 - Bug] Replaced @paginate decorator with manual pagination to fix duplicate request argument TypeError**

- **Found during:** Task 2 GREEN (test_list_deliveries_paginated failure)
- **Issue:** `TypeError: WebhookEndpointController.list_deliveries() got multiple values for argument 'request'` — the `@paginate` decorator from `ninja.pagination` injects `request` as a keyword argument but ninja_extra controller routes already bind `request` as the first positional arg via the controller base class mechanism, creating the duplicate.
- **Fix:** Removed `@paginate` decorator, changed response type from `list[DeliveryOut]` to `dict`, added `page: int = 1` and `page_size: int = 20` query params, manually sliced the queryset and returned `{"items": [...], "count": N}`.
- **Files modified:** apps/api/apps/webhooks/controllers.py
- **Verification:** test_list_deliveries_paginated passes; full 12-test suite green
- **Committed in:** cf87853 (Task GREEN commit)

---

**Total deviations:** 2 auto-fixed (Rule 1 - bugs in plan's provided code template)
**Impact on plan:** Both bugs were in the plan-provided code template (from **future** and @paginate). The behavioral contract (pagination shape, HTTPS validation, secret-once semantics) is fully preserved. No scope creep.

## Issues Encountered

- Pre-existing billing test failures (`test_get_subscription`, `test_services.py`) fail under nplusone guard — pre-existing before this plan, out of scope. Documented in deferred-items.
- ruff auto-converted `Optional[str]` to `str | None` and added type: ignore comments — no semantic change

## Next Phase Readiness

- All 8 webhook API endpoints are live and tested — org admins can register endpoints, rotate secrets, view delivery history, and retry failed deliveries
- `deliver_webhook.delay(str(delivery.id))` pattern established for enqueuing retries
- Phase 28 (API Keys) can build on the same permission and schema patterns established here
- Phase 30 (Admin Backoffice) can register WebhookEndpoint and WebhookDelivery in django-unfold admin

---

_Phase: 27-outbound-webhooks_
_Completed: 2026-03-13_
