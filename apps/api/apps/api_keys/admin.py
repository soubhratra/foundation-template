# B2B_START
"""Admin registrations for the api_keys B2B module."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(ModelAdmin):
    list_display = ("prefix", "name", "user", "is_active", "last_used_at", "created_at")
    list_filter = ("is_active",)
    search_fields = ("prefix", "name", "user__email")
    readonly_fields = ("prefix", "key_hash", "created_at", "last_used_at", "usage_count")


# B2B_END
