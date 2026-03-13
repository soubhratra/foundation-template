import sys
from unittest.mock import MagicMock, patch

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


# BILL-02: has_org_feature tests


def test_has_org_feature_org_plan_takes_precedence(db):
    """BILL-02: When org has active subscription, org plan result is returned (not personal)."""
    from apps.core.entitlements import has_org_feature

    org = MagicMock()
    org.pk = 42
    user = MagicMock()
    user.pk = 7

    with (
        patch(
            "apps.orgs.services._resolve_org_plan_id", return_value="pro_plan"
        ) as mock_resolve_org,
        patch(
            "apps.billing.entitlements._flags_for_plan", return_value={"advanced_analytics": True}
        ) as mock_flags,
        patch("apps.billing.entitlements._resolve_plan_id") as mock_resolve_personal,
    ):
        result = has_org_feature(user, org, "advanced_analytics")

    assert result is True
    mock_resolve_org.assert_called_once_with(org)
    mock_flags.assert_called_once_with("pro_plan")
    # Personal plan path must NOT have been called
    mock_resolve_personal.assert_not_called()


def test_has_org_feature_personal_fallback(db):
    """BILL-02: When org has no active subscription, falls back to personal plan."""
    from apps.core.entitlements import has_org_feature

    org = MagicMock()
    org.pk = 43
    user = MagicMock()
    user.pk = 8

    with (
        patch("apps.orgs.services._resolve_org_plan_id", return_value=None),
        patch(
            "apps.billing.entitlements._resolve_plan_id", return_value="free"
        ) as mock_resolve_personal,
        patch(
            "apps.billing.entitlements._flags_for_plan", return_value={"some_feature": True}
        ) as mock_flags,
    ):
        result = has_org_feature(user, org, "some_feature")

    assert result is True
    # Personal plan path must have been consulted
    mock_resolve_personal.assert_called_once_with(user)
    mock_flags.assert_called_once_with("free")
