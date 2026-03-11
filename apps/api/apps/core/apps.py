from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self) -> None:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

        from apps.core.logging import configure_structlog
        from apps.core.tracing import configure_otel

        configure_structlog()
        configure_otel()

        # Auto-instrument Django views (creates spans for each request)
        # and psycopg3 SQL queries (creates child spans for each DB query).
        # Both are safe to call with the default no-op ProxyTracerProvider
        # when OTEL_EXPORTER_OTLP_ENDPOINT is absent — they produce no-op spans.
        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
