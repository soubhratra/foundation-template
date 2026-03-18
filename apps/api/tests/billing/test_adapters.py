"""
Tests for PaymentAdapter ABC and StripeAdapter implementation.
Covers: ADPTR-01 (ABC contract), ADPTR-02 (StripeAdapter), ADPTR-03 (settings resolution)
"""

import abc

import pytest

adapters = pytest.importorskip("apps.billing.adapters")
PaymentAdapter = adapters.PaymentAdapter
StripeAdapter = adapters.StripeAdapter


class TestPaymentAdapterContract:
    """ADPTR-01: PaymentAdapter is an ABC with domain-centric method signatures."""

    @pytest.mark.req("BILL-01")
    def test_payment_adapter_is_abstract(self):
        assert abc.ABC in PaymentAdapter.__mro__, "PaymentAdapter must be an ABC"

    @pytest.mark.req("BILL-01")
    def test_cannot_instantiate_abstract_adapter(self):
        with pytest.raises(TypeError):
            PaymentAdapter()  # type: ignore[abstract]

    @pytest.mark.req("BILL-01")
    def test_abstract_methods_defined(self):
        expected = {
            "create_customer",
            "create_checkout_session",
            "create_portal_session",
            "cancel_subscription",
            "modify_subscription",
            "construct_webhook_event",
            "record_usage",
            "list_invoices",
            "preview_proration",
            "get_usage_summary",
            "retrieve_subscription",
            "reactivate_subscription",
            "delete_customer",  # GDPR-01: permanently delete a customer (Article 17)
        }
        abstract_methods = getattr(PaymentAdapter, "__abstractmethods__", set())
        assert expected == abstract_methods, (
            f"Abstract methods mismatch.\nExpected: {expected}\nGot: {abstract_methods}"
        )

    @pytest.mark.req("BILL-01")
    def test_no_stripe_in_abstract_signatures(self):
        """ADPTR-01: The word 'stripe' must not appear in abstract method signatures."""
        import inspect

        for name in PaymentAdapter.__abstractmethods__:
            method = getattr(PaymentAdapter, name)
            sig = str(inspect.signature(method))
            annotations = getattr(method, "__annotations__", {})
            sig_lower = sig.lower()
            assert "stripe" not in sig_lower, (
                f"Abstract method '{name}' contains 'stripe' in signature: {sig}"
            )
            for annotation_value in annotations.values():
                annotation_str = str(annotation_value).lower()
                assert "stripe" not in annotation_str, (
                    f"Abstract method '{name}' has 'stripe' in return/param annotation"
                )


class TestStripeAdapterImplementation:
    """ADPTR-02: StripeAdapter concretely implements PaymentAdapter."""

    @pytest.mark.req("BILL-01")
    def test_stripe_adapter_inherits_payment_adapter(self):
        assert issubclass(StripeAdapter, PaymentAdapter)

    @pytest.mark.req("BILL-01")
    def test_stripe_adapter_is_concrete(self):
        """StripeAdapter must have no abstract methods remaining."""
        abstract = getattr(StripeAdapter, "__abstractmethods__", set())
        assert not abstract, f"StripeAdapter has unimplemented abstract methods: {abstract}"

    @pytest.mark.req("BILL-01")
    def test_stripe_adapter_instantiates(self):
        """StripeAdapter can be constructed (uses STRIPE_SECRET_KEY from settings)."""
        from django.conf import settings

        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            pytest.skip("STRIPE_SECRET_KEY not set — skipping instantiation test")
        adapter = StripeAdapter()
        assert isinstance(adapter, PaymentAdapter)


class TestPaymentAdapterAbstractMethods:
    """HOOK-05: PaymentAdapter defines abstract methods needed for Plan 10-02."""

    @pytest.mark.req("BILL-01")
    def test_abstract_preview_proration_exists(self):
        """PaymentAdapter must declare preview_proration as an abstract method."""
        import inspect

        assert "preview_proration" in PaymentAdapter.__abstractmethods__, (
            "PaymentAdapter is missing abstract method 'preview_proration'"
        )
        method = getattr(PaymentAdapter, "preview_proration", None)
        assert method is not None
        assert inspect.isfunction(method) or callable(method)

    @pytest.mark.req("BILL-01")
    def test_abstract_get_usage_summary_exists(self):
        """PaymentAdapter must declare get_usage_summary as an abstract method."""
        import inspect

        assert "get_usage_summary" in PaymentAdapter.__abstractmethods__, (
            "PaymentAdapter is missing abstract method 'get_usage_summary'"
        )
        method = getattr(PaymentAdapter, "get_usage_summary", None)
        assert method is not None
        assert inspect.isfunction(method) or callable(method)


class TestAdapterResolution:
    """ADPTR-03: Adapter resolved via BILLING_ADAPTER setting."""

    @pytest.mark.req("BILL-01")
    def test_billing_adapter_setting_exists(self):
        from django.conf import settings

        if not hasattr(settings, "BILLING_ADAPTER") or not settings.BILLING_ADAPTER:
            pytest.skip("BILLING_ADAPTER not configured in settings — Wave 1 adds it")
        assert settings.BILLING_ADAPTER, "BILLING_ADAPTER must not be empty"

    @pytest.mark.req("BILL-01")
    def test_billing_adapter_resolves_to_stripe_adapter(self):
        from django.conf import settings
        from django.utils.module_loading import import_string

        if not hasattr(settings, "BILLING_ADAPTER") or not settings.BILLING_ADAPTER:
            pytest.skip("BILLING_ADAPTER not configured in settings — Wave 1 adds it")
        klass = import_string(settings.BILLING_ADAPTER)
        assert issubclass(klass, PaymentAdapter)
