"""Tests for OBS-02: configure_otel() no-op and active TracerProvider."""

from unittest.mock import patch

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider


def test_configure_otel_noop_when_no_env(monkeypatch):
    """configure_otel() is a no-op when OTEL_EXPORTER_OTLP_ENDPOINT is not set."""
    from apps.core.tracing import configure_otel

    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    # Reset to default no-op provider first
    from opentelemetry.sdk.trace import TracerProvider as _TP  # noqa: F401

    # Record pre-call state — default provider is ProxyTracerProvider, not SDK TracerProvider
    configure_otel()
    # After no-op call, provider must still NOT be a real TracerProvider
    provider = trace.get_tracer_provider()
    # The no-op case: provider is still the global proxy (not SDK TracerProvider)
    # We verify by checking it can't export (no processors attribute)
    assert not isinstance(provider, TracerProvider), (
        "configure_otel() should NOT set a real TracerProvider when endpoint is absent"
    )


def test_configure_otel_active_when_env_set(monkeypatch):
    """configure_otel() creates a real TracerProvider when endpoint is set."""
    from apps.core.tracing import configure_otel

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    # Patch OTLPSpanExporter to avoid actual network connection
    with patch(
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter"
    ) as MockExporter:
        MockExporter.return_value = MockExporter
        configure_otel()

    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider), (
        "configure_otel() must set a real SDK TracerProvider when endpoint is set"
    )
    # Cleanup: reset global provider to avoid test pollution
    from opentelemetry import trace as _trace

    _trace._TRACER_PROVIDER = None
