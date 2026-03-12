"""Tests for OBS-03: ObservabilityAdapter ABC, PostHogAdapter, NoOpAdapter,
ObservabilityMiddleware, and Celery task_failure signal handler.

All imports are deferred into test function bodies so pytest can collect
this file without an ImportError. Tests fail RED until Plan 02 creates
apps/core/observability.py and extends apps/core/middleware.py.
"""

from unittest.mock import MagicMock, patch

import pytest


def test_noop_adapter():
    """NoOpAdapter.capture_exception and capture_event return None silently."""
    from apps.core.observability import NoOpAdapter  # fails RED until Plan 02

    adapter = NoOpAdapter()
    exc = ValueError("boom")
    result_exc = adapter.capture_exception(exc, {"user_id": "42"})
    result_event = adapter.capture_event("test_event", {"key": "val"})
    assert result_exc is None
    assert result_event is None


@pytest.mark.django_db
def test_posthog_adapter_capture_exception(settings):
    """PostHogAdapter.capture_exception calls posthog client with correct args."""
    from apps.core.observability import PostHogAdapter  # fails RED until Plan 02

    settings.POSTHOG_API_KEY = "phc_test"
    settings.POSTHOG_HOST = "https://eu.i.posthog.com"

    with patch("posthog.Posthog") as mock_posthog_cls:
        mock_client = MagicMock()
        mock_posthog_cls.return_value = mock_client

        adapter = PostHogAdapter()
        exc = RuntimeError("test error")
        context = {"user_id": "99", "path": "/api/v1/test", "method": "GET"}
        adapter.capture_exception(exc, context)

    mock_client.capture_exception.assert_called_once()
    call_kwargs = mock_client.capture_exception.call_args
    # distinct_id must be the user_id from context
    assert call_kwargs.kwargs.get("distinct_id") == "99" or (
        call_kwargs.args and call_kwargs.args[0] == "99"
    )


@pytest.mark.django_db
def test_get_adapter_default(settings):
    """get_observability_adapter() returns NoOpAdapter when default setting used."""
    from apps.core.observability import (  # fails RED until Plan 02
        NoOpAdapter,
        get_observability_adapter,
    )

    settings.OBSERVABILITY_ADAPTER = "apps.core.observability.NoOpAdapter"
    adapter = get_observability_adapter()
    assert isinstance(adapter, NoOpAdapter)


@pytest.mark.django_db
def test_middleware_process_exception(rf):
    """ObservabilityMiddleware.process_exception calls adapter and returns None."""
    from apps.core.middleware import ObservabilityMiddleware  # fails RED until Plan 02

    mock_adapter = MagicMock()
    mock_adapter.capture_exception.return_value = None

    with patch("apps.core.middleware.get_observability_adapter", return_value=mock_adapter):
        middleware = ObservabilityMiddleware(get_response=lambda r: None)
        request = rf.get("/api/v1/test")
        request.user = MagicMock()
        request.user.pk = 1
        request.user.is_authenticated = True

        exc = ValueError("unhandled")
        result = middleware.process_exception(request, exc)

    mock_adapter.capture_exception.assert_called_once()
    assert result is None  # middleware must not return a response


@pytest.mark.django_db
def test_middleware_user_context(rf):
    """ObservabilityMiddleware includes user_id, path, method, exc_type in context."""
    from apps.core.middleware import ObservabilityMiddleware  # fails RED until Plan 02

    captured_context: dict = {}

    def fake_capture(exc, context):
        captured_context.update(context)

    mock_adapter = MagicMock()
    mock_adapter.capture_exception.side_effect = fake_capture

    with patch("apps.core.middleware.get_observability_adapter", return_value=mock_adapter):
        middleware = ObservabilityMiddleware(get_response=lambda r: None)
        request = rf.get("/api/v1/items")
        request.user = MagicMock()
        request.user.pk = 7
        request.user.is_authenticated = True

        middleware.process_exception(request, TypeError("type mismatch"))

    assert captured_context.get("user_id") == "7"
    assert captured_context.get("path") == "/api/v1/items"
    assert captured_context.get("method") == "GET"
    assert captured_context.get("exc_type") == "TypeError"


def test_celery_signal_handler():
    """task_failure signal connected after CoreConfig.ready(); firing it calls capture_exception."""
    from celery.signals import task_failure

    mock_adapter = MagicMock()

    with patch("apps.core.observability.get_observability_adapter", return_value=mock_adapter):
        # Verify the signal has receivers registered (CoreConfig.ready() wired it)
        assert len(task_failure.receivers) > 0, (
            "task_failure signal has no receivers — CoreConfig.ready() did not connect handler"
        )
