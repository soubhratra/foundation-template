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


# BILL-02: org cache invalidation stub


@pytest.mark.django_db
def test_subscription_updated_invalidates_org_caches(db):
    """BILL-02: Org member entitlement caches are cleared when org subscription updates."""
    pytest.fail("stub — implement after OrgCustomer and org cache extension exists")
