"""ObservabilityAdapter — pluggable exception capture and event tracking.

Adapter pattern: swap providers (PostHog → Sentry, etc.) by changing one
Django setting without touching any view or task code.

Usage:
    from apps.core.observability import get_observability_adapter

    adapter = get_observability_adapter()
    adapter.capture_exception(exc, {"user_id": "42", "path": "/api/v1/..."})
    adapter.capture_event("subscription_created", {"plan": "pro"})

To switch providers:
    OBSERVABILITY_ADAPTER = "apps.core.observability.PostHogAdapter"  # default (NoOp when no key)
    OBSERVABILITY_ADAPTER = "apps.core.observability.SentryAdapter"   # see SentryAdapter stub below
"""

from __future__ import annotations

import abc
from typing import Any

from django.conf import settings
from django.utils.module_loading import import_string


class ObservabilityAdapter(abc.ABC):
    """Abstract base class for all observability adapters.

    Concrete subclasses must implement capture_exception and capture_event.
    """

    @abc.abstractmethod
    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        """Capture an unhandled exception with optional context.

        Args:
            exc: The exception instance to capture.
            context: Dict with keys such as user_id, path, method, exc_type.
        """

    @abc.abstractmethod
    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        """Capture a named product analytics event.

        Args:
            event: Event name (e.g. "subscription_created").
            properties: Arbitrary properties dict. Must include "distinct_id"
                for PostHogAdapter routing; omit for NoOpAdapter.
        """


class PostHogAdapter(ObservabilityAdapter):
    """PostHog adapter using posthog.Posthog instance (thread-safe).

    Reads POSTHOG_API_KEY and POSTHOG_HOST from Django settings on instantiation.
    Do NOT use posthog.api_key = ... global mutation — use this class instead.
    """

    def __init__(self) -> None:
        # Lazy import to avoid ImportError in environments that use NoOpAdapter
        # and have not installed posthog (e.g. CI without PostHog credentials).
        import posthog

        self._client = posthog.Posthog(
            api_key=settings.POSTHOG_API_KEY,
            host=settings.POSTHOG_HOST,
        )

    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        """Capture exception to PostHog with user context."""
        distinct_id = context.get("user_id", "anonymous")
        self._client.capture_exception(exc, distinct_id=distinct_id, properties=context)

    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        """Capture named product analytics event to PostHog."""
        distinct_id = properties.pop("distinct_id", "anonymous")
        self._client.capture(distinct_id, event, properties)


class NoOpAdapter(ObservabilityAdapter):
    """No-op adapter — all calls silently pass with zero overhead.

    Selected by default via OBSERVABILITY_ADAPTER setting so CI and local dev
    without a POSTHOG_API_KEY produce no errors and no network calls.
    """

    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        pass

    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        pass


# ---------------------------------------------------------------------------
# Sentry migration guide:
#
# To swap PostHogAdapter for Sentry:
#   1. pip install sentry-sdk[django,celery]
#   2. Set OBSERVABILITY_ADAPTER = "apps.core.observability.SentryAdapter"
#   3. Set SENTRY_DSN in settings (read from env)
#
# Method mapping:
#   capture_exception(exc, context) → sentry_sdk.capture_exception(exc)
#       Add context via sentry_sdk.push_scope() or with sentry_sdk.new_scope():
#         scope.set_user({"id": context.get("user_id")})
#         scope.set_tag("path", context.get("path"))
#
#   capture_event(event, properties) → sentry_sdk.capture_message(event)
#       Or use custom structured events via sentry_sdk.capture_event({...})
#
# sentry_sdk.init() should be called in CoreConfig.ready() alongside configure_otel().
# ---------------------------------------------------------------------------
class SentryAdapter(ObservabilityAdapter):
    """Sentry adapter stub — not implemented.

    See migration guide comment above this class for how to implement.
    Raise NotImplementedError to make misconfiguration obvious at runtime.
    """

    def capture_exception(self, exc: BaseException, context: dict[str, Any]) -> None:
        raise NotImplementedError(
            "SentryAdapter is a stub. See the migration guide in observability.py "
            "to implement using sentry-sdk."
        )

    def capture_event(self, event: str, properties: dict[str, Any]) -> None:
        raise NotImplementedError(
            "SentryAdapter is a stub. See the migration guide in observability.py "
            "to implement using sentry-sdk."
        )


def get_observability_adapter() -> ObservabilityAdapter:
    """Resolve and instantiate the configured observability adapter.

    Reads OBSERVABILITY_ADAPTER from Django settings (dotted path string).
    Returns a new adapter instance per call — same pattern as get_adapter()
    in apps/billing/utils.py.

    Default: apps.core.observability.NoOpAdapter (zero overhead, no errors
    when POSTHOG_API_KEY is absent).
    """
    adapter_class = import_string(settings.OBSERVABILITY_ADAPTER)
    return adapter_class()
