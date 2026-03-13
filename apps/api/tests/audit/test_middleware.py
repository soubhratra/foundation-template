"""Tests: AuditContextMiddleware.get_context() attaches org_id to pghistory context (AUDIT-01)."""

from unittest.mock import MagicMock


def test_middleware_adds_org_id():
    """get_context() includes org_id as string when request.org is set."""
    from apps.audit.middleware import AuditContextMiddleware

    middleware = AuditContextMiddleware(get_response=lambda r: None)

    # Build a mock request with request.org set to a mock org with id
    mock_org = MagicMock()
    mock_org.id = 99
    mock_request = MagicMock()
    mock_request.org = mock_org
    mock_request.user = MagicMock()
    mock_request.user.is_authenticated = False

    # get_context() must include org_id as string
    ctx = middleware.get_context(mock_request)
    assert "org_id" in ctx
    assert ctx["org_id"] == "99"


def test_middleware_null_org_id():
    """get_context() omits org_id when request has no .org attribute."""
    from apps.audit.middleware import AuditContextMiddleware

    middleware = AuditContextMiddleware(get_response=lambda r: None)

    # Build a plain mock request with no .org attribute
    # Specify attributes explicitly to prevent .org from being auto-created by MagicMock
    mock_request = MagicMock(spec=["user", "path"])
    mock_request.user = MagicMock()
    mock_request.user.is_authenticated = False
    mock_request.path = "/api/v1/health/"

    ctx = middleware.get_context(mock_request)
    assert "org_id" not in ctx
