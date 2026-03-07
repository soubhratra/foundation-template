from django.contrib import admin

from .models import (
    Customer,
    Payment,
    PlanProviderMapping,
    ProcessedWebhookEvent,
    Subscription,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_customer_id", "created_at")
    search_fields = ("user__email", "stripe_customer_id")
    raw_id_fields = ("user",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("customer", "status", "cancel_at_period_end", "current_period_end")
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("customer__user__email", "stripe_subscription_id")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("customer", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("customer__user__email", "stripe_payment_intent_id")


@admin.register(ProcessedWebhookEvent)
class ProcessedWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "processed_at")
    search_fields = ("event_id",)


@admin.register(PlanProviderMapping)
class PlanProviderMappingAdmin(admin.ModelAdmin):
    list_display = ("plan_id", "provider", "price_id", "billing_period")
