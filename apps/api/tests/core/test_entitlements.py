import pytest


class TestBillingOffFallback:
    """ENT-03: has_feature() returns True for all keys when billing is not installed."""

    def test_returns_true_when_billing_absent(self, user):
        try:
            from apps.core.entitlements import has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/core/entitlements.py missing — implement has_feature()")
        # When billing module is absent (ImportError from billing), has_feature returns True
        pytest.fail("not implemented")

    def test_no_import_error(self, user):
        try:
            from apps.core.entitlements import has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/core/entitlements.py missing — implement has_feature()")
        # has_feature(user, any_key) does not raise ImportError even if billing absent
        pytest.fail("not implemented")
