"""Tests: AuditContextMiddleware.get_context() attaches org_id to pghistory context (AUDIT-01)."""


def test_middleware_adds_org_id():
    """get_context() includes org_id as string when request.org is set."""
    raise AssertionError(
        "not implemented: mock request.org, call get_context(), assert org_id in result"
    )


def test_middleware_null_org_id():
    """get_context() omits org_id when request has no .org attribute."""
    raise AssertionError(
        "not implemented: mock plain request, call get_context(), assert org_id absent"
    )
