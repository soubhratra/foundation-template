import pytest
from django.core.cache import cache


class TestHasFeature:
    """ENT-01: has_feature() returns True/False based on billing plan feature_flags."""

    def test_returns_true_for_enabled_flag(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        user = subscription.customer.user
        # Pro plan has api_access=True in feature_flags
        subscription.plan_id = "pro"
        subscription.save(update_fields=["plan_id"])
        cache.clear()

        result = _has_feature(user, "api_access")
        assert result is True

    def test_returns_false_for_disabled_flag(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        user = subscription.customer.user
        # Pro plan has white_label=False in feature_flags
        subscription.plan_id = "pro"
        subscription.save(update_fields=["plan_id"])
        cache.clear()

        result = _has_feature(user, "white_label")
        assert result is False

    def test_missing_key_returns_false(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        user = subscription.customer.user
        subscription.plan_id = "pro"
        subscription.save(update_fields=["plan_id"])
        cache.clear()

        result = _has_feature(user, "nonexistent_key")
        assert result is False

    def test_no_subscription_uses_free_plan(self, user):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        # user has no billing_customer → treated as free plan → api_access=False
        cache.clear()
        result = _has_feature(user, "api_access")
        assert result is False

    def test_unknown_plan_id_falls_back_to_free(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        user = subscription.customer.user
        # "legacy" is not in BILLING_PLANS → falls back to free plan → api_access=False
        subscription.plan_id = "legacy"
        subscription.save(update_fields=["plan_id"])
        cache.clear()

        result = _has_feature(user, "api_access")
        assert result is False


class TestCaching:
    """ENT-02: Cache-aside — second call within TTL hits cache, not DB."""

    def test_second_call_uses_cache(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
        except ImportError:
            pytest.fail("apps/billing/entitlements.py missing — implement _has_feature()")

        from apps.billing.entitlements import _has_feature

        user = subscription.customer.user
        subscription.plan_id = "pro"
        subscription.save(update_fields=["plan_id"])
        cache.clear()

        # First call — populates cache
        first_result = _has_feature(user, "api_access")

        # Corrupt the DB value so we can confirm the second call reads from cache
        subscription.plan_id = "free"
        subscription.save(update_fields=["plan_id"])

        # Second call — must return cached (pro plan) value, not the new DB value
        second_result = _has_feature(user, "api_access")

        assert first_result is True
        assert second_result is True  # still True because cache holds pro plan flags


class TestCacheInvalidation:
    """ENT-02: Cache deleted immediately when customer.subscription.updated fires."""

    def test_cache_invalidated_on_subscription_updated(self, subscription):
        try:
            from apps.billing.entitlements import _has_feature  # noqa: F401
            from apps.billing.tasks import _handle_subscription_updated  # noqa: F401
        except ImportError:
            pytest.fail(
                "apps/billing/entitlements.py or apps/billing/tasks.py missing required symbols"
            )
        # Seed cache, fire webhook handler, assert cache is empty afterward.
        pytest.fail("not implemented")
