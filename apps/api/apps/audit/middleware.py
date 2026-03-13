"""Audit context middleware for pghistory.

AuditContextMiddleware extends pghistory's HistoryMiddleware to inject the
current organization's ID into the pghistory context on every request.

What HistoryMiddleware provides:
- Wraps each request in a pghistory.context() call automatically
- Populates context with user ID (from request.user) and a request URL
- Saves a Context row linking all events fired during the request

What this subclass adds:
- Reads request.org (set by OrgSlugMiddleware / IsOrgMember permission)
- Adds org_id as a string to the context dict when present
- Omits org_id safely for non-org requests (user management, billing, etc.)
"""

import pghistory.middleware


class AuditContextMiddleware(pghistory.middleware.HistoryMiddleware):
    """Extends HistoryMiddleware to include org_id in the pghistory context.

    For B2B requests where request.org is set, the Context row will include
    org_id so audit queries can be filtered by organisation without joining
    through the tracked model's org FK.
    """

    def get_context(self, request):
        ctx = super().get_context(request)
        org = getattr(request, "org", None)
        if org is not None:
            ctx["org_id"] = str(org.id)
        return ctx
