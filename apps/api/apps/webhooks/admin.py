# B2B_START
"""Admin registrations for the webhooks B2B module."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import WebhookDelivery, WebhookEndpoint


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(ModelAdmin):
    list_display = ("name", "org", "url", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "url", "org__name", "org__slug")
    readonly_fields = ("id", "signing_key", "secret_hash", "created_at", "updated_at")


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(ModelAdmin):
    list_display = ("id", "endpoint", "event_type", "status", "created_at")
    list_filter = ("status", "event_type")
    search_fields = ("endpoint__name", "event_type")
    readonly_fields = ("id", "created_at")


# B2B_END
