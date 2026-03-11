from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self) -> None:
        from apps.core.logging import configure_structlog

        configure_structlog()

        # OTel instrumentation added in Phase 13 Plan 03
        # from apps.core.tracing import configure_otel
        # from opentelemetry.instrumentation.django import DjangoInstrumentor
        # from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        # configure_otel()
        # DjangoInstrumentor().instrument()
        # PsycopgInstrumentor().instrument()
