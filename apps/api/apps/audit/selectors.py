"""Audit log query selectors.

OrgAuditEvents proxy model, cursor pagination, and get_audit_log_page().

DB index recommendation (add as manual migration after Wave 3):
    CREATE INDEX CONCURRENTLY IF NOT EXISTS pghistory_context_org_id_created_id_idx
    ON pghistory_context ((metadata->>'org_id'), created_at DESC, id DESC);
This composite index optimises the org-scoped keyset pagination query.
"""

import base64
from datetime import datetime

import pghistory
from django.contrib.auth import get_user_model
from django.db import models as dj_models
from pghistory import models as pgh_models

from apps.audit.schemas import AuditEntryOut

User = get_user_model()


# ---------------------------------------------------------------------------
# OrgAuditEvents proxy — MiddlewareEvents filtered by org_id context key
# ---------------------------------------------------------------------------


class OrgAuditEvents(pgh_models.MiddlewareEvents):
    """Proxy over pghistory's MiddlewareEvents adding an org_id ProxyField.

    ProxyField surfaces pgh_context__org_id as a filterable annotation
    without adding a real column to the underlying Context table.
    """

    org_id = pghistory.ProxyField("pgh_context__org_id", dj_models.TextField(null=True))

    class Meta:
        proxy = True


# ---------------------------------------------------------------------------
# Cursor encode / decode on (pgh_created_at, pgh_id)
# ---------------------------------------------------------------------------


def encode_cursor(ts: datetime, pgh_id: int) -> str:
    """Encode a cursor from a (timestamp, id) pair."""
    raw = f"{ts.isoformat()}:{pgh_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int] | None:
    """Decode a cursor string into (timestamp, id). Returns None on any error."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts_str, id_str = raw.rsplit(":", 1)
        return datetime.fromisoformat(ts_str), int(id_str)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Actor email bulk lookup (avoids N+1)
# ---------------------------------------------------------------------------


def enrich_with_actor_emails(events: list) -> dict:
    """Return {user_pk: email} for all actor pks in events.

    Single bulk query — no N+1 even with 200-item pages.
    pgh_context may be None for events created outside HTTP requests
    (management commands, tests without context). Guard: ctx = e.pgh_context or {}
    """
    actor_pks = set()
    for e in events:
        ctx = e.pgh_context or {}
        uid = ctx.get("user")
        if uid is not None:
            try:
                actor_pks.add(int(uid))
            except (ValueError, TypeError):
                pass
    if not actor_pks:
        return {}
    return dict(User.objects.filter(pk__in=actor_pks).values_list("pk", "email"))


# ---------------------------------------------------------------------------
# AuditEntryOut builder helper
# ---------------------------------------------------------------------------


def _to_entry_out(event, email_map: dict) -> AuditEntryOut:
    """Convert a pghistory event row into an AuditEntryOut instance.

    Intentionally excludes impersonator — stored in context metadata but
    never surfaced in the API response (Phase 30 staff-only feature).
    """
    ctx = event.pgh_context or {}

    # actor_id — stored as int in context["user"]
    raw_actor = ctx.get("user")
    actor_id: str | None = None
    actor_pk: int | None = None
    if raw_actor is not None:
        try:
            actor_pk = int(raw_actor)
            actor_id = str(actor_pk)
        except (ValueError, TypeError):
            pass

    actor_email: str | None = None
    if actor_pk is not None:
        actor_email = email_map.get(actor_pk)

    # model_name — strip "Event" suffix from class name
    cls_name = event.__class__.__name__
    model_name = cls_name[: -len("Event")] if cls_name.endswith("Event") else cls_name

    # object_id — pgh_obj_id when available, otherwise pgh_obj (FK)
    if hasattr(event, "pgh_obj_id"):
        object_id = str(event.pgh_obj_id)
    else:
        object_id = str(event.pgh_obj)

    return AuditEntryOut(
        id=event.pgh_id,
        timestamp=event.pgh_created_at,
        action=event.pgh_label,
        model_name=model_name,
        object_id=object_id,
        actor_id=actor_id,
        actor_email=actor_email,
        url=ctx.get("url"),
    )


# ---------------------------------------------------------------------------
# get_audit_log_page — main query function
# ---------------------------------------------------------------------------


def get_audit_log_page(
    org,
    *,
    actor_id: int | None = None,
    action: str | None = None,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
    cursor: str | None = None,
    page_size: int = 50,
) -> tuple[list[AuditEntryOut], str | None]:
    """Return a page of audit events for an org.

    Uses across() to union OrganizationEvent, MembershipEvent, APIKeyEvent,
    and WebhookEndpointEvent tables — this is the only way APIKey events
    (which have no FK to org) appear correctly.

    The across() label strings are verified from 29-02-SUMMARY.md:
    - "orgs.OrganizationEvent"
    - "orgs.MembershipEvent"
    - "api_keys.APIKeyEvent"
    - "webhooks.WebhookEndpointEvent"

    Filter by org_id from the pghistory context (not a model FK) to include
    all models regardless of whether they reference org directly.

    Returns:
        (items, next_cursor) — next_cursor is None on the last page.
    """
    # Build base queryset across all tracked event models
    qs = OrgAuditEvents.objects.across(
        "orgs.OrganizationEvent",
        "orgs.MembershipEvent",
        "api_keys.APIKeyEvent",
        "webhooks.WebhookEndpointEvent",
    )

    # Filter to this org's events via context org_id
    qs = qs.filter(org_id=str(org.id))

    # Optional filters
    if actor_id is not None:
        qs = qs.filter(pgh_context__user=actor_id)
    if action is not None:
        qs = qs.filter(pgh_label=action)
    if from_ts is not None:
        qs = qs.filter(pgh_created_at__gte=from_ts)
    if to_ts is not None:
        qs = qs.filter(pgh_created_at__lte=to_ts)

    # Keyset pagination (newest first, compound key for stability)
    decoded = decode_cursor(cursor) if cursor else None
    if decoded is not None:
        cur_ts, cur_id = decoded
        qs = qs.filter(pgh_created_at__lt=cur_ts) | qs.filter(
            pgh_created_at=cur_ts, pgh_id__lt=cur_id
        )

    # Order newest first; fetch page_size+1 to detect has_more without COUNT
    qs = qs.order_by("-pgh_created_at", "-pgh_id")
    page_rows = list(qs[: page_size + 1])

    has_more = len(page_rows) > page_size
    page = page_rows[:page_size]

    # Bulk email lookup — single query, no N+1
    email_map = enrich_with_actor_emails(page)

    items = [_to_entry_out(event, email_map) for event in page]

    next_cursor: str | None = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(last.pgh_created_at, last.pgh_id)

    return items, next_cursor
