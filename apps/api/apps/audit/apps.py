"""Audit app configuration."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    label = "audit"
    verbose_name = "Audit"

    def ready(self) -> None:
        # B2B_START — hijack signal handlers for impersonation event recording
        try:
            from hijack import signals as hijack_signals
        except ImportError:
            # hijack not installed (non-B2B scaffold) — skip signal wiring
            return

        from apps.audit.models import ImpersonationEvent

        def _on_hijack_started(sender, hijacker, hijacked, request, **kwargs):
            ImpersonationEvent.objects.create(
                action=ImpersonationEvent.Action.START,
                hijacker=hijacker,
                hijacked=hijacked,
            )

        def _on_hijack_ended(sender, hijacker, hijacked, request, **kwargs):
            ImpersonationEvent.objects.create(
                action=ImpersonationEvent.Action.END,
                hijacker=hijacker,
                hijacked=hijacked,
            )

        hijack_signals.hijack_started.connect(_on_hijack_started)
        hijack_signals.hijack_ended.connect(_on_hijack_ended)
        # B2B_END
