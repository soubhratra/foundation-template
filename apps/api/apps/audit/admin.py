# B2B_START
"""Admin registrations for the audit B2B module.

ImpersonationEventAdmin is the staff-visible audit log: it shows every
hijack start/end event written by the hijack signal handlers.
It is intentionally read-only — audit logs are an immutable record.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ImpersonationEvent


class HasImpersonatorFilter(admin.SimpleListFilter):
    title = "Has Impersonator"
    parameter_name = "has_impersonator"

    def lookups(self, request, model_admin):
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(hijacker__isnull=False)
        if self.value() == "no":
            return queryset.filter(hijacker__isnull=True)
        return queryset


@admin.register(ImpersonationEvent)
class ImpersonationEventAdmin(ModelAdmin):
    list_display = ("timestamp", "action", "hijacker_email", "hijacked_email")
    list_filter = ("action", HasImpersonatorFilter)
    search_fields = ("hijacker__email", "hijacked__email")
    readonly_fields = ("timestamp", "action", "hijacker", "hijacked")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Hijacker Email")
    def hijacker_email(self, obj):
        return obj.hijacker.email if obj.hijacker else "—"

    @admin.display(description="Hijacked Email")
    def hijacked_email(self, obj):
        return obj.hijacked.email if obj.hijacked else "—"


# B2B_END
