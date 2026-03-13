---
phase: 29-audit-logging
plan: "03"
subsystem: audit
tags: [pghistory, audit-logging, cursor-pagination, django-ninja-extra, b2b]
dependency_graph:
  requires: [29-02]
  provides: [audit-log-api, cursor-pagination, org-audit-query]
  affects: [apps/audit]
tech_stack:
  added: []
  patterns:
    [
      OrgAuditEvents proxy model,
      across() cross-model join,
      keyset cursor pagination,
      bulk email lookup,
    ]
key_files:
  created:
    - apps/api/apps/audit/schemas.py
    - apps/api/apps/audit/selectors.py
    - apps/api/apps/audit/controllers.py
  modified:
    - apps/api/tests/audit/test_schemas.py
    - apps/api/tests/audit/test_controllers.py
decisions:
  - "ninja_extra.QueryParams does not exist — AuditLogQueryParams uses ninja.Schema as base class instead"
  - "Query(...) in controller default arg requires # noqa: B008 — ruff B008 fires but functional requirement demands it"
  - "OrgAuditEvents.objects.across() takes positional string args (not a list) — signature: across(*event_models)"
  - "encode_cursor/decode_cursor operate on raw pgh_created_at/pgh_id fields (not AuditEntryOut.timestamp/id) to avoid extra object construction"
  - "DB index for org_id+pgh_created_at+pgh_id deferred — recommend adding as manual RunSQL migration post-Wave 3"
metrics:
  duration_seconds: 848
  completed_date: "2026-03-13"
  tasks_completed: 2
  files_changed: 5
---

# Phase 29 Plan 03: Build Audit Log Query API Summary

Cursor-paginated GET /api/v1/org/{slug}/audit-log endpoint using pghistory across() for cross-model event queries, OrgAuditEvents proxy model, and AuditLogController with IsOrgAdmin permission gate — all 16 AUDIT-02 tests GREEN.

## Tasks Completed

| Task | Description                                                      | Commit  | Status |
| ---- | ---------------------------------------------------------------- | ------- | ------ |
| 1    | Build schemas and selectors (OrgAuditEvents + cursor pagination) | e9d0a5a | DONE   |
| 2    | Build AuditLogController and turn all AUDIT-02 tests GREEN       | d7f5f9b | DONE   |

## Artifacts Delivered

### apps/audit/schemas.py

- `AuditEntryOut`: id, timestamp, action, model_name, object_id, actor_id, actor_email, url — no impersonator field
- `CursorPageOut`: items, next_cursor, page_size
- `AuditLogQueryParams`: actor_id, action, from_ts, to_ts, cursor, page_size (default 50)

### apps/audit/selectors.py

- `OrgAuditEvents`: proxy over `pgh_models.MiddlewareEvents` with `ProxyField("pgh_context__org_id")` for org-scoped filtering
- `encode_cursor(ts, pgh_id)` / `decode_cursor(cursor)`: base64 keyset cursor on (pgh_created_at, pgh_id) for stable newest-first pagination
- `enrich_with_actor_emails(events)`: single bulk `User.objects.filter(pk__in=...)` query — no N+1
- `get_audit_log_page(org, ...)`: main selector using `OrgAuditEvents.objects.across()` across all 4 event model label strings; filters by org_id context; keyset pagination; fetch page_size+1 to detect next page without COUNT query

### apps/audit/controllers.py

- `AuditLogController` at `/org/{org_slug}/audit-log`
- Auth: `[SessionAuth(), jwt_token_auth]` — consistent with orgs/webhooks pattern
- Permissions: `[IsAuthenticated, IsOrgMember, IsOrgAdmin]` — member 403s, admin 200s
- page_size capped at 200 in controller
- Auto-discovered via `auto_discover_controllers()` — no URL wiring needed

## DB Index Recommendation (deferred)

Add this as a manual RunSQL migration after Wave 3 to optimise org-scoped keyset queries:

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS pghistory_context_org_id_created_id_idx
ON pghistory_context ((metadata->>'org_id'), created_at DESC, id DESC);
```

This composite index targets the `pgh_context__org_id` filter combined with the `-pgh_created_at, -pgh_id` ORDER BY used in every audit log page query.

## Test Results

```
tests/audit/test_controllers.py .......   7/7
tests/audit/test_models.py .....          5/5
tests/audit/test_context.py .             1/1
tests/audit/test_middleware.py ..         2/2
tests/audit/test_schemas.py .             1/1

16 passed in 24.16s
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ninja_extra.QueryParams does not exist**

- **Found during:** Task 1 (test collection, ImportError)
- **Issue:** Plan interface code specified `from ninja_extra import QueryParams` but `QueryParams` is not exported by `ninja_extra` in the installed version
- **Fix:** Used `ninja.Schema` as the base class for `AuditLogQueryParams` instead. The schema binding to query params is handled by `Query(...)` in the controller default arg
- **Files modified:** `apps/api/apps/audit/schemas.py`
- **Commit:** e9d0a5a

**2. [Rule 1 - Bug] encode_cursor called on AuditEntryOut instead of raw event object**

- **Found during:** Task 1 (test_cursor_pagination)
- **Issue:** `encode_cursor(last.timestamp, last.id)` — `last` is an `OrgAuditEvents` instance (raw event row), not an `AuditEntryOut`. The event has `pgh_created_at` and `pgh_id`, not `timestamp` and `id`
- **Fix:** Changed to `encode_cursor(last.pgh_created_at, last.pgh_id)` — use raw fields from the event object before schema conversion
- **Files modified:** `apps/api/apps/audit/selectors.py`
- **Commit:** e9d0a5a

**3. [Rule 2 - Lint] ruff B008 on Query(...) in controller default arg**

- **Found during:** Task 2 pre-commit hook
- **Issue:** `ruff` B008 fires on `filters: AuditLogQueryParams = Query(...)` because `Query(...)` is a function call in a default argument
- **Fix:** Added `# noqa: B008` to suppress — `Query(...)` is required by django-ninja to bind the Schema to query params; removing it causes 422 (ninja treats the unbound Schema as request body)
- **Files modified:** `apps/api/apps/audit/controllers.py`
- **Commit:** d7f5f9b

## Self-Check

Verified files exist:

- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/schemas.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/selectors.py` — FOUND
- `/Users/soubhratra/workspace/foundation-template/apps/api/apps/audit/controllers.py` — FOUND

Verified commits exist:

- `e9d0a5a` — Task 1: feat(29-03): build audit schemas and selectors with cursor pagination — FOUND
- `d7f5f9b` — Task 2: feat(29-03): build AuditLogController — all 16 AUDIT-02 tests GREEN — FOUND

## Self-Check: PASSED
