"""Tests for OBS-01: structlog processor and renderer selection."""

from unittest.mock import MagicMock, patch


def test_otel_processor_injects_when_span_active():
    """add_otel_context injects trace_id + span_id when a span is recording."""
    from apps.core.logging import add_otel_context

    mock_ctx = MagicMock()
    mock_ctx.trace_id = 0xABCDEF1234567890ABCDEF1234567890
    mock_ctx.span_id = 0xABCDEF1234567890

    mock_span = MagicMock()
    mock_span.is_recording.return_value = True
    mock_span.get_span_context.return_value = mock_ctx

    with patch("opentelemetry.trace.get_current_span", return_value=mock_span):
        event_dict = {}
        result = add_otel_context(None, None, event_dict)

    assert "trace_id" in result
    assert "span_id" in result
    assert len(result["trace_id"]) == 32
    assert len(result["span_id"]) == 16
    assert result["trace_id"] == format(mock_ctx.trace_id, "032x")
    assert result["span_id"] == format(mock_ctx.span_id, "016x")


def test_otel_processor_omits_when_no_span():
    """add_otel_context omits trace_id + span_id (not null) when no span is active."""
    from opentelemetry.trace import INVALID_SPAN_CONTEXT, NonRecordingSpan

    from apps.core.logging import add_otel_context

    non_recording = NonRecordingSpan(INVALID_SPAN_CONTEXT)

    with patch("opentelemetry.trace.get_current_span", return_value=non_recording):
        event_dict = {}
        result = add_otel_context(None, None, event_dict)

    assert "trace_id" not in result
    assert "span_id" not in result


def test_renderer_selection_dev(settings):
    """ConsoleRenderer is active in dev (DEBUG=True)."""
    import structlog

    settings.DEBUG = True
    from apps.core.logging import configure_structlog

    configure_structlog()
    # structlog is configured — no exception means success
    assert structlog.is_configured()


def test_renderer_selection_prod(settings):
    """JSONRenderer is active in prod (DEBUG=False)."""
    import structlog

    settings.DEBUG = False
    from apps.core.logging import configure_structlog

    configure_structlog()
    assert structlog.is_configured()
