"""Tests: audit_context() degrades to no-op when pghistory not in INSTALLED_APPS (AUDIT-01)."""

from unittest.mock import patch

import pytest


@pytest.mark.req("AUDIT-02")
def test_audit_context_noop():
    """audit_context() runs as no-op context manager when pghistory not installed."""
    from apps.audit.context import audit_context

    with patch("django.apps.apps.is_installed", return_value=False):
        # Must run without raising any error — no-op behaviour
        with audit_context(user_id=1, org_id=42):
            pass  # Should reach here with no exception
