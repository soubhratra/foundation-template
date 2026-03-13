"""Audit log response schemas.

IMPORTANT: No `from __future__ import annotations` — breaks Pydantic QueryParams
in django-ninja-extra (confirmed Phase 27 anti-pattern).
"""

from datetime import datetime

from ninja import Schema


class AuditEntryOut(Schema):
    id: int  # pgh_id — auto-increment within event table
    timestamp: datetime  # pgh_created_at (serialised as ISO 8601 UTC)
    action: str  # pgh_label e.g. "org.updated"
    model_name: str  # e.g. "Organization"
    object_id: str  # pgh_obj_id as string
    actor_id: str | None  # user pk from pgh_context["user"], None if deleted
    actor_email: str | None  # resolved via bulk User lookup, None if deleted
    url: str | None  # from pgh_context["url"]
    # impersonator intentionally omitted — staff-only; populated in Phase 30


class CursorPageOut(Schema):
    items: list[AuditEntryOut]
    next_cursor: str | None
    page_size: int


class AuditLogQueryParams(Schema):
    """Query parameters for the audit log endpoint.

    NOTE: ninja_extra.QueryParams does not exist in ninja_extra 0.x — use
    ninja.Schema with individual controller function params instead.
    Bound via Query(...) in the controller signature.
    """

    actor_id: int | None = None  # user pk (int, not UUID — pghistory stores pk as BigAutoField int)
    action: str | None = None  # exact match e.g. "org.updated"
    from_ts: datetime | None = None  # ISO 8601, maps to pgh_created_at__gte
    to_ts: datetime | None = None  # ISO 8601, maps to pgh_created_at__lte
    cursor: str | None = None
    page_size: int = 50
