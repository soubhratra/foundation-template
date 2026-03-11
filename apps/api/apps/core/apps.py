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

        # Connect task_failure signal to auto-capture Celery task exceptions.
        # weak=False prevents the handler from being garbage collected.
        # Lazy import of get_observability_adapter inside handler body avoids
        # circular import at module level.
        from celery.signals import task_failure

        @task_failure.connect(weak=False)
        def handle_task_failure(  # type: ignore[misc]
            sender,
            task_id,
            exception,
            args,
            kwargs,
            traceback,
            einfo,
            **extra,
        ) -> None:
            from apps.core.observability import get_observability_adapter

            context = {
                "task_name": (sender.__name__ if hasattr(sender, "__name__") else str(sender)),
                "task_id": task_id,
                "task_args": str(args),
                "user_id": "celery",
            }
            get_observability_adapter().capture_exception(exception, context)
