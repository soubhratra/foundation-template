# B2B_START
"""Admin registrations for the orgs B2B module."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Membership, Organization, OrgCustomer


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "slug", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "slug", "owner__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Membership)
class MembershipAdmin(ModelAdmin):
    list_display = ("user", "org", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__email", "org__name", "org__slug")
    readonly_fields = ("created_at",)


@admin.register(OrgCustomer)
class OrgCustomerAdmin(ModelAdmin):
    list_display = ("org", "stripe_customer_id", "created_at")
    search_fields = ("org__name", "org__slug", "stripe_customer_id")
    readonly_fields = ("created_at", "updated_at")


# B2B_END
