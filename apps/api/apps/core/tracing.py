"""OpenTelemetry configuration helper for Phase 13.

configure_otel() is designed to be called:
- At Django startup via CoreConfig.ready() (for the web process)
- Inside @worker_process_init.connect in config/celery.py (for Celery workers, after fork)

Design: zero-overhead no-op when OTEL_EXPORTER_OTLP_ENDPOINT is absent.
OTLPSpanExporter is imported lazily to avoid ~100ms import cost when tracing is disabled.
insecure=True is correct for Jaeger all-in-one on port 4317 (no TLS in Docker Compose).
"""

from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_otel(service_name: str | None = None) -> None:
    """Configure OpenTelemetry if OTEL_EXPORTER_OTLP_ENDPOINT is set.

    No-op (and no import of OTLPSpanExporter) when endpoint is absent, so CI
    and local dev without Jaeger incur zero overhead and no failed connections.

    Args:
        service_name: Override service name in Jaeger. Falls back to
            OTEL_SERVICE_NAME env var, then DJANGO_SETTINGS_MODULE value,
            then the literal string "foundation-api".
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return  # Remain on default no-op ProxyTracerProvider

    # Lazy import: only pay the import cost when tracing is actually enabled.
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    _service_name = service_name or os.environ.get(
        "OTEL_SERVICE_NAME",
        os.environ.get("DJANGO_SETTINGS_MODULE", "foundation-api"),
    )
    resource = Resource(attributes={SERVICE_NAME: _service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
