"""Tests: AuditEntryOut schema excludes impersonator field (AUDIT-02)."""

from apps.audit.schemas import AuditEntryOut


def test_impersonator_excluded():
    """AuditEntryOut model_fields does not contain 'impersonator'."""
    assert "impersonator" not in AuditEntryOut.model_fields
