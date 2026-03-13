"""Tests: audit_context() degrades to no-op when pghistory not in INSTALLED_APPS (AUDIT-01)."""


def test_audit_context_noop():
    """audit_context() runs as no-op context manager when pghistory not installed."""
    raise AssertionError(
        "not implemented: patch is_installed('pghistory') -> False, verify no error"
    )
