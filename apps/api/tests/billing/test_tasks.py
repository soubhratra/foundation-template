"""
Tests for the Celery process_stripe_event task (tasks.py).
Covers: HOOK-03 (idempotency), HOOK-04 (Tier-1 event handlers)

Task contract:
- If ProcessedWebhookEvent already exists for (provider, event_id) → return early (idempotency)
- Each Tier-1 event type correctly updates model state
- Unknown event types are silently acknowledged (no error, no DB writes)
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

# importorskip ensures test collection is skipped cleanly if modules don't exist yet
billing_models = pytest.importorskip("apps.billing.models")
billing_tasks = pytest.importorskip("apps.billing.tasks")

Customer = billing_models.Customer
Subscription = billing_models.Subscription
Payment = billing_models.Payment
ProcessedWebhookEvent = billing_models.ProcessedWebhookEvent
SubscriptionStatus = billing_models.SubscriptionStatus
process_stripe_event = billing_tasks.process_stripe_event

# ---------------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------------- #


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="tasktestuser",
        email="tasktest@example.com",
        password="testpass123",
    )


@pytest.fixture
def customer(user):
    c, _ = Customer.objects.get_or_create(
        user=user,
        defaults={"stripe_customer_id": "cus_test_webhook"},
    )
    return c


@pytest.fixture
def subscription(customer):
    sub, _ = Subscription.objects.get_or_create(
        customer=customer,
        defaults={
            "stripe_subscription_id": "sub_test_webhook",
            "status": SubscriptionStatus.INCOMPLETE,
        },
    )
    return sub


# ---------------------------------------------------------------------------- #
# Idempotency
# ---------------------------------------------------------------------------- #


class TestIdempotencyGuard:
    """HOOK-03: Duplicate events are silently ignored."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_idempotency_guard(self, customer, subscription):
        """If ProcessedWebhookEvent already exists for (provider, event_id), task returns early."""
        event_id = "evt_already_processed"

        # Pre-create the deduplication record
        ProcessedWebhookEvent.objects.create(
            provider="stripe",
            event_id=event_id,
        )

        initial_subscription_status = subscription.status

        event_data = {
            "id": subscription.stripe_subscription_id,
            "customer": customer.stripe_customer_id,
            "status": "active",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        # Run task — should return early without modifying subscription
        process_stripe_event(
            event_id=event_id,
            event_type="customer.subscription.updated",
            event_data=event_data,
        )

        # Subscription status should NOT have changed
        subscription.refresh_from_db()
        assert subscription.status == initial_subscription_status

        # No duplicate ProcessedWebhookEvent created
        count = ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).count()
        assert count == 1


# ---------------------------------------------------------------------------- #
# Tier-1 Event Handlers
# ---------------------------------------------------------------------------- #


class TestCheckoutSessionCompleted:
    """HOOK-04: checkout.session.completed creates/updates Subscription with ACTIVE status."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_checkout_session_completed(self, customer):
        """checkout.session.completed → Subscription created/updated with status ACTIVE."""
        event_id = "evt_checkout_completed_001"

        event_data = {
            "customer": customer.stripe_customer_id,
            "subscription": "sub_from_checkout",
            "status": "complete",
        }

        process_stripe_event(
            event_id=event_id,
            event_type="checkout.session.completed",
            event_data=event_data,
        )

        subscription = Subscription.objects.get(customer=customer)
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.stripe_subscription_id == "sub_from_checkout"

        # ProcessedWebhookEvent row was created
        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestSubscriptionCreated:
    """HOOK-04: customer.subscription.created sets subscription fields."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_subscription_created(self, customer):
        """customer.subscription.created → Subscription updated with sub ID and period dates."""
        event_id = "evt_sub_created_001"

        event_data = {
            "id": "sub_created_001",
            "customer": customer.stripe_customer_id,
            "status": "trialing",
            "cancel_at_period_end": False,
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        process_stripe_event(
            event_id=event_id,
            event_type="customer.subscription.created",
            event_data=event_data,
        )

        subscription = Subscription.objects.get(customer=customer)
        assert subscription.stripe_subscription_id == "sub_created_001"
        assert subscription.status == SubscriptionStatus.TRIALING
        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None

        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestSubscriptionUpdated:
    """HOOK-04: customer.subscription.updated updates status and cancel_at_period_end."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_subscription_updated(self, customer, subscription):
        """customer.subscription.updated → status updated; cancel_at_period_end updated."""
        event_id = "evt_sub_updated_001"

        event_data = {
            "id": subscription.stripe_subscription_id,
            "customer": customer.stripe_customer_id,
            "status": "past_due",
            "cancel_at_period_end": True,
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        process_stripe_event(
            event_id=event_id,
            event_type="customer.subscription.updated",
            event_data=event_data,
        )

        subscription.refresh_from_db()
        assert subscription.status == SubscriptionStatus.PAST_DUE
        assert subscription.cancel_at_period_end is True

        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestSubscriptionDeleted:
    """HOOK-04: customer.subscription.deleted sets status to CANCELED."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_subscription_deleted(self, customer, subscription):
        """customer.subscription.deleted → Subscription.status set to CANCELED."""
        event_id = "evt_sub_deleted_001"

        event_data = {
            "id": subscription.stripe_subscription_id,
            "customer": customer.stripe_customer_id,
            "status": "canceled",
        }

        process_stripe_event(
            event_id=event_id,
            event_type="customer.subscription.deleted",
            event_data=event_data,
        )

        subscription.refresh_from_db()
        assert subscription.status == SubscriptionStatus.CANCELED

        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestInvoicePaymentSucceeded:
    """HOOK-04: invoice.payment_succeeded creates Payment with status 'succeeded'."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_invoice_payment_succeeded(self, customer):
        """invoice.payment_succeeded → Payment row created with status 'succeeded'."""
        event_id = "evt_invoice_paid_001"

        event_data = {
            "customer": customer.stripe_customer_id,
            "payment_intent": "pi_test_001",
            "amount_paid": 2999,
            "currency": "usd",
            "status": "paid",
        }

        process_stripe_event(
            event_id=event_id,
            event_type="invoice.payment_succeeded",
            event_data=event_data,
        )

        payment = Payment.objects.filter(
            customer=customer,
            stripe_payment_intent_id="pi_test_001",
        ).first()
        assert payment is not None
        assert payment.status == "succeeded"
        assert payment.currency == "usd"

        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestInvoicePaymentFailed:
    """HOOK-04: invoice.payment_failed sets Subscription to PAST_DUE and creates Payment."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_invoice_payment_failed(self, customer, subscription):
        """invoice.payment_failed → Subscription.status = PAST_DUE; Payment row created."""
        event_id = "evt_invoice_failed_001"

        event_data = {
            "customer": customer.stripe_customer_id,
            "payment_intent": "pi_test_failed_001",
            "amount_due": 2999,
            "currency": "usd",
            "status": "open",
        }

        process_stripe_event(
            event_id=event_id,
            event_type="invoice.payment_failed",
            event_data=event_data,
        )

        subscription.refresh_from_db()
        assert subscription.status == SubscriptionStatus.PAST_DUE

        payment = Payment.objects.filter(
            customer=customer,
            stripe_payment_intent_id="pi_test_failed_001",
        ).first()
        assert payment is not None
        assert payment.status == "failed"

        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


class TestUnknownEventType:
    """HOOK-04: Unrecognized events are silently acknowledged."""

    @pytest.mark.req("BILL-02")
    @pytest.mark.django_db
    def test_unknown_event_type(self, customer):
        """Unknown event_type → returns without error, no DB writes except idempotency record."""
        event_id = "evt_unknown_001"

        initial_payment_count = Payment.objects.filter(customer=customer).count()
        initial_sub_count = Subscription.objects.filter(customer=customer).count()

        process_stripe_event(
            event_id=event_id,
            event_type="payment_link.created",  # Not a Tier-1 event
            event_data={"id": "plink_test", "customer": customer.stripe_customer_id},
        )

        # No new Payments or Subscriptions created
        assert Payment.objects.filter(customer=customer).count() == initial_payment_count
        assert Subscription.objects.filter(customer=customer).count() == initial_sub_count

        # ProcessedWebhookEvent IS created (to prevent reprocessing)
        assert ProcessedWebhookEvent.objects.filter(provider="stripe", event_id=event_id).exists()


# BILL-02: org cache invalidation


@pytest.mark.req("BILL-02")
@pytest.mark.django_db
def test_subscription_updated_invalidates_org_caches(db):
    """BILL-02: Org member entitlement caches are cleared when org subscription updates."""
    from django.contrib.auth import get_user_model
    from django.core.cache import cache

    from apps.billing.tasks import _try_invalidate_org_member_caches
    from apps.orgs.models import Membership, Organization

    User = get_user_model()

    # Create org — post_save signal auto-creates OrgCustomer with empty stripe_customer_id
    org = Organization.objects.create(name="TestCo", slug="testco-bill02")
    stripe_cid = "cus_org_bill02_test"

    # Update the auto-created OrgCustomer with a known stripe_customer_id
    org.billing_customer.stripe_customer_id = stripe_cid
    org.billing_customer.save(update_fields=["stripe_customer_id"])

    # Create 3 members
    members = []
    for i in range(3):
        u = User.objects.create_user(
            username=f"orgmember{i}",
            email=f"member{i}@example.com",
            password="testpass",  # pragma: allowlist secret
        )
        Membership.objects.create(org=org, user=u, role="member")
        members.append(u)

    # Pre-populate org entitlement cache for each member
    for u in members:
        cache_key = f"entitlements:org:{org.pk}:{u.pk}"
        cache.set(cache_key, {"some_feature": True}, timeout=300)
        assert cache.get(cache_key) is not None, f"Cache key not set for user {u.pk}"

    # Also set a personal entitlement cache to confirm it is NOT touched
    personal_key = f"entitlements:{members[0].pk}"
    cache.set(personal_key, {"personal_feature": True}, timeout=300)

    # Call the function under test
    _try_invalidate_org_member_caches(stripe_cid)

    # All org-scoped keys must have been deleted
    for u in members:
        cache_key = f"entitlements:org:{org.pk}:{u.pk}"
        assert cache.get(cache_key) is None, f"Cache key not cleared for user {u.pk}"

    # Personal cache key must NOT have been affected
    assert cache.get(personal_key) == {"personal_feature": True}


# ---------------------------------------------------------------------------- #
# Phase 32: Webhook wiring (RED stub — Plan 32-02 makes GREEN)
# ---------------------------------------------------------------------------- #


@pytest.mark.req("BILL-02")
@pytest.mark.django_db(transaction=True)
def test_subscription_updated_fires_webhook_for_member_orgs(user):
    """HOOK-01: _handle_subscription_updated fires subscription.updated webhook for member orgs."""
    from unittest.mock import patch

    from apps.orgs.models import Membership, Organization

    # post_save signal on User auto-creates Customer — update it with a known stripe ID
    customer, _ = Customer.objects.get_or_create(user=user)
    customer.stripe_customer_id = "cus_test_webhook"
    customer.save(update_fields=["stripe_customer_id"])

    Subscription.objects.get_or_create(customer=customer, defaults={"status": "active"})

    org = Organization.objects.create(name="Test Org", slug="test-org-wh", owner=user)
    Membership.objects.create(org=org, user=user, role="owner")

    event_data = {"customer": "cus_test_webhook", "status": "active"}

    with patch("apps.billing.tasks.fire_webhook_event") as mock_fire:
        billing_tasks._handle_subscription_updated(event_data)

    assert mock_fire.called, "fire_webhook_event should have been called for member orgs"
    event_types = [c.args[1] for c in mock_fire.call_args_list]
    assert any(et == "subscription.updated" for et in event_types), (
        f"Expected 'subscription.updated' in fired events, got: {event_types}"
    )
