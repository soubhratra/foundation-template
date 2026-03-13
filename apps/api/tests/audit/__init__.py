"""Audit test suite.

Module-level import ensures collection fails with ImportError until
apps.audit is fully implemented (Phase 29 Wave 2).
"""

from apps.audit.context import audit_context  # noqa: F401
