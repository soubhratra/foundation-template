import sys
from unittest.mock import patch

import pytest


class TestBillingOffFallback:
    """ENT-03: has_feature() returns True for all keys when billing is not installed."""

    def test_returns_true_when_billing_absent(self, user):
        try:
            from apps.core.entitlements import has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/core/entitlements.py missing — implement has_feature()")

        from apps.core.entitlements import has_feature

        # Simulate billing module absent by patching the import inside has_feature
        with patch.dict(sys.modules, {"apps.billing.entitlements": None}):
            result = has_feature(user, "api_access")

        assert result is True

    def test_no_import_error(self, user):
        try:
            from apps.core.entitlements import has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/core/entitlements.py missing — implement has_feature()")

        from apps.core.entitlements import has_feature

        # With billing present, calling has_feature must not raise any exception
        try:
            has_feature(user, "any_key")
        except Exception as exc:
            pytest.fail(f"has_feature() raised unexpectedly: {exc}")
