"""AuditLogController — GET /api/v1/org/{slug}/audit-log

IMPORTANT: No `from __future__ import annotations` — breaks Pydantic at runtime
(confirmed Phase 27 anti-pattern for django-ninja-extra controllers).
"""

from typing import Any

from allauth.headless.contrib.ninja.security import jwt_token_auth
from django.http import HttpRequest
from ninja import Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from apps.audit.schemas import AuditLogQueryParams, CursorPageOut
from apps.audit.selectors import get_audit_log_page
from apps.orgs.permissions import IsOrgAdmin, IsOrgMember


@api_controller(
    "/org/{org_slug}/audit-log",
    tags=["Audit Log"],
    auth=[SessionAuth(), jwt_token_auth],
    permissions=[IsAuthenticated, IsOrgMember, IsOrgAdmin],
)
class AuditLogController(ControllerBase):
    @route.get("", response=CursorPageOut)
    def get_audit_log(
        self,
        request: HttpRequest,
        org_slug: str,
        filters: AuditLogQueryParams = Query(...),  # noqa: B008
    ) -> Any:
        """Return paginated audit log entries for this organization.

        Org owners and admins only (IsOrgMember sets request.org, IsOrgAdmin
        verifies OWNER or ADMIN role).

        Impersonator field is never serialised — stored in pghistory context
        metadata but excluded from AuditEntryOut (Phase 30 staff-only feature).
        """
        page_size = min(filters.page_size, 200)
        items, next_cursor = get_audit_log_page(
            org=request.org,  # type: ignore[attr-defined]
            actor_id=filters.actor_id,
            from_ts=filters.from_ts,
            to_ts=filters.to_ts,
            action=filters.action,
            cursor=filters.cursor,
            page_size=page_size,
        )
        return {"items": items, "next_cursor": next_cursor, "page_size": page_size}
