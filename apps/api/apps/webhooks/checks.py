"""Django system checks for the webhooks app.

Validates the WEBHOOK_EVENTS setting at startup.
"""

from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_webhook_events(app_configs, **kwargs):  # type: ignore[no-untyped-def]
    """Validate the WEBHOOK_EVENTS setting structure."""
    errors = []
    webhook_events = getattr(settings, "WEBHOOK_EVENTS", None)
    if webhook_events is None:
        errors.append(
            Warning(
                "WEBHOOK_EVENTS setting is not defined.",
                hint="Add WEBHOOK_EVENTS = {} to your settings or extend the default dict.",
                id="webhooks.W001",
            )
        )
        return errors

    if not isinstance(webhook_events, dict):
        errors.append(
            Warning(
                "WEBHOOK_EVENTS must be a dict mapping event type strings to config dicts.",
                hint=(
                    "Set WEBHOOK_EVENTS = "
                    "{'event.name': {'description': '...', 'example_payload': {...}}}"
                ),
                id="webhooks.W004",
            )
        )
        return errors

    for event_type, config in webhook_events.items():
        if not isinstance(config, dict):
            errors.append(
                Warning(
                    f"WEBHOOK_EVENTS['{event_type}'] must be a dict.",
                    hint=(
                        "Each event type value must be a dict with "
                        "'description' and 'example_payload' keys."
                    ),
                    id="webhooks.W005",
                )
            )
            continue
        if "description" not in config:
            errors.append(
                Warning(
                    f"WEBHOOK_EVENTS['{event_type}'] is missing a 'description' key.",
                    hint="Add a human-readable description for each event type.",
                    id="webhooks.W002",
                )
            )
        if "example_payload" not in config:
            errors.append(
                Warning(
                    f"WEBHOOK_EVENTS['{event_type}'] is missing an 'example_payload' key.",
                    hint="Add an example_payload dict for each event type.",
                    id="webhooks.W003",
                )
            )
    return errors
