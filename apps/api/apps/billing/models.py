from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    PAST_DUE = "past_due", _("Past Due")
    CANCELED = "canceled", _("Canceled")
    TRIALING = "trialing", _("Trialing")
    INCOMPLETE = "incomplete", _("Incomplete")
    INCOMPLETE_EXPIRED = "incomplete_expired", _("Incomplete Expired")
    UNPAID = "unpaid", _("Unpaid")


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_customer",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self) -> str:
        return f"Customer({self.user.email})"


class Subscription(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=50,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.INCOMPLETE,
    )
    cancel_at_period_end = models.BooleanField(default=False)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    plan_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self) -> str:
        return f"Subscription({self.customer.user.email}, {self.status})"


class Payment(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="usd")
    status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Payment({self.customer.user.email}, {self.amount} {self.currency})"


class ProcessedWebhookEvent(models.Model):
    provider = models.CharField(max_length=50)
    event_id = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Processed Webhook Event"
        verbose_name_plural = "Processed Webhook Events"
        unique_together = [("provider", "event_id")]

    def __str__(self) -> str:
        return f"WebhookEvent({self.provider}:{self.event_id})"


class PlanProviderMapping(models.Model):
    """Maps internal plan IDs to provider-specific price IDs at runtime.

    This table decouples internal plan identifiers from provider price IDs,
    preventing provider coupling in application code. The service layer resolves
    prices via this table rather than hardcoding Stripe price IDs on models.
    """

    BILLING_PERIOD_MONTHLY = "monthly"
    BILLING_PERIOD_ANNUAL = "annual"
    BILLING_PERIOD_CHOICES = [
        (BILLING_PERIOD_MONTHLY, "Monthly"),
        (BILLING_PERIOD_ANNUAL, "Annual"),
    ]

    plan_id = models.CharField(max_length=50, help_text="Internal plan identifier, e.g. 'pro'")
    provider = models.CharField(max_length=50, help_text="Payment provider, e.g. 'stripe'")
    price_id = models.CharField(
        max_length=255, help_text="Provider price ID, e.g. Stripe price_xxx"
    )
    billing_period = models.CharField(
        max_length=10,
        choices=BILLING_PERIOD_CHOICES,
        default=BILLING_PERIOD_MONTHLY,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan Provider Mapping"
        verbose_name_plural = "Plan Provider Mappings"
        unique_together = [("plan_id", "provider", "billing_period")]
        indexes = [
            models.Index(fields=["plan_id", "provider"]),
        ]

    def __str__(self) -> str:
        return f"{self.plan_id}/{self.provider}/{self.billing_period} → {self.price_id}"
