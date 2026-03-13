"""Audit app models.

Contains plain Django models for audit-related data that is not tracked via
pghistory (pghistory tracks ORM model mutations; impersonation events are
session operations that would never trigger pghistory triggers).
"""

from django.db import models


# B2B_START — ImpersonationEvent (plain model, not pghistory-tracked)
class ImpersonationEvent(models.Model):
    """Records every hijack start and end event.

    Written by hijack_started / hijack_ended signal handlers in apps.audit.apps.
    Plain Django model — NOT pghistory-tracked (hijack events are session ops,
    not ORM model mutations, so pghistory triggers would never fire for them).
    """

    class Action(models.TextChoices):
        START = "start", "Start"
        END = "end", "End"

    action = models.CharField(max_length=10, choices=Action.choices)
    hijacker = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="hijack_sessions_as_hijacker",
    )
    hijacked = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="hijack_sessions_as_hijacked",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_impersonation_event"
        ordering = ["-timestamp"]
        verbose_name = "Impersonation Event"
        verbose_name_plural = "Impersonation Events"

    def __str__(self) -> str:
        return f"{self.action} — {self.hijacker} → {self.hijacked} at {self.timestamp}"


# B2B_END
