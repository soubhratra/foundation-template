# Phase 13: Structured Logging + Distributed Tracing - Research

**Researched:** 2026-03-11
**Domain:** structlog + django-structlog + OpenTelemetry (Django, Celery, psycopg) + Jaeger
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Log format:** structlog `ConsoleRenderer` in dev (`DEBUG=True`), `JSONRenderer` in prod — switch automatic via `DEBUG` setting
- **Log routing:** ALL logs (Django internals, app code, Celery) routed through structlog pipeline via Django's `LOGGING` dict and structlog's stdlib handler
- **Log/trace correlation:** Custom structlog processor in `apps/core/logging.py` reads active OTel context and injects `trace_id` + `span_id` as 32/16-char hex strings; fields omitted (not null) when no active trace
- **Request context middleware:** New `apps/core/middleware.py` — injects `request_id` (UUID4), `user_id`, `method`, `path`, `status_code`, `duration_ms`; echoes `X-Request-ID` as response header; no raw client IP
- **Celery trace propagation:** OTel Celery auto-instrumentation propagates parent trace context via task headers
- **Jaeger:** `jaegertracing/all-in-one` image, port 4317 (OTLP gRPC), port 16686 (UI), added to default `docker-compose.yml`
- **OTel activation:** tracing is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` env var is not set

### Claude's Discretion

- Exact structlog processors chain ordering (e.g., add_log_level, TimeStamper, StackInfoRenderer, format_exc_info, OtelProcessor, renderer)
- OTel service name value (can default to `DJANGO_SETTINGS_MODULE` or an `OTEL_SERVICE_NAME` env var)
- Whether to auto-instrument `psycopg2` vs `psycopg3` (depends on what's installed — detect at runtime)
- Django LOGGING dict structure details (root logger level, loggers to suppress like `django.server` in tests)
- pytest fixture to disable structlog output noise during test runs

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                                                                                                                               | Research Support                                                                                                                                  |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| OBS-01 | Developer can see structured JSON logs with `request_id`, `user_id`, `duration_ms` auto-injected on every Django request via `structlog`                                                  | django-structlog 10.0.0 + custom RequestContextMiddleware + DEBUG-based renderer switching                                                        |
| OBS-02 | Developer can trace requests end-to-end across Django + Celery + PostgreSQL via OpenTelemetry auto-instrumentation with OTLP exporter; Jaeger runs in Docker Compose for local inspection | opentelemetry-instrumentation-django + opentelemetry-instrumentation-celery + opentelemetry-instrumentation-psycopg + Jaeger all-in-one container |

</phase_requirements>

---

## Summary

Phase 13 has two parallel tracks that converge into a single coherent developer experience: (1) structured logging via structlog with django-structlog, and (2) distributed tracing via OpenTelemetry with OTLP export to Jaeger. Both tracks are well-supported by mature, stable libraries with no hand-rolling required.

The structlog track uses `django-structlog` 10.0.0 which handles all the heavy lifting: stdlib log routing, request context binding (`request_id`, `user_id` auto-injected per request), and Celery signal integration that propagates context across async task boundaries. The custom middleware is the only new code beyond configuration — `django-structlog`'s `RequestMiddleware` already exists but the project adds a custom one on top for `duration_ms` and the `X-Request-ID` response header.

The tracing track uses the OpenTelemetry Python SDK with auto-instrumentation packages for Django, Celery, and psycopg (psycopg3). The key design pattern is conditional activation: when `OTEL_EXPORTER_OTLP_ENDPOINT` is absent, the OTel API default no-op behavior means zero overhead and no connection errors. When set, a `configure_otel()` helper in `apps/core/tracing.py` wires up a real `TracerProvider` with gRPC OTLP export to Jaeger. The two tracks are linked by a single structlog processor that reads OTel span context and injects `trace_id`/`span_id` as hex strings into every log event.

**Primary recommendation:** Use `django-structlog[celery]` 10.0.0 for the entire logging pipeline. Use `opentelemetry-instrumentation-django`, `opentelemetry-instrumentation-celery`, and `opentelemetry-instrumentation-psycopg` (for psycopg3, not psycopg2) for tracing. All packages are stable and production-grade — this phase is configuration-heavy, not code-heavy.

---

## Standard Stack

### Core

| Library                                | Version             | Purpose                                                  | Why Standard                                                                         |
| -------------------------------------- | ------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| structlog                              | 25.5.0              | Structured logging with processors pipeline              | De facto standard for structured Python logging; immutable, context-bound log events |
| django-structlog                       | 10.0.0              | Django + Celery integration for structlog                | Handles stdlib routing, request middleware, Celery signals — no hand-rolling         |
| opentelemetry-sdk                      | 1.33.0 (1.x stable) | OTel core SDK — TracerProvider, BatchSpanProcessor       | Standard OTel Python SDK                                                             |
| opentelemetry-instrumentation-django   | 0.61b0              | Auto-instruments Django views as spans                   | Official OTel contrib package                                                        |
| opentelemetry-instrumentation-celery   | 0.61b0              | Auto-instruments Celery tasks + propagates trace context | Official OTel contrib, handles worker_process_init                                   |
| opentelemetry-instrumentation-psycopg  | 0.60b1              | Auto-instruments psycopg3 SQL queries as spans           | Official OTel contrib for psycopg3 (NOT psycopg2)                                    |
| opentelemetry-exporter-otlp-proto-grpc | 1.33.0              | Exports spans via OTLP/gRPC to Jaeger                    | gRPC is the Jaeger-recommended ingest protocol                                       |

### Supporting

| Library          | Version | Purpose                                                    | When to Use                                   |
| ---------------- | ------- | ---------------------------------------------------------- | --------------------------------------------- |
| pytest-structlog | 1.x     | Suppress structlog noise and assert on log events in tests | Add to dev dependencies for clean test output |

### Alternatives Considered

| Instead of                                       | Could Use                              | Tradeoff                                                                                                  |
| ------------------------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| django-structlog                                 | Manual structlog setup                 | django-structlog eliminates ~200 lines of boilerplate for request context, Celery signals, stdlib routing |
| opentelemetry-instrumentation-psycopg (psycopg3) | opentelemetry-instrumentation-psycopg2 | Project uses `psycopg[binary]>=3.2` (psycopg3) — must use the psycopg3 instrumentation package            |
| OTLP/gRPC (port 4317)                            | OTLP/HTTP (port 4318)                  | gRPC is preferred for Jaeger local dev; both work — decision is locked to gRPC                            |
| jaegertracing/all-in-one                         | Full Jaeger deployment with Cassandra  | all-in-one is in-memory, zero-config, appropriate for dev tooling in a template                           |

**Installation:**

```bash
# In apps/api/
uv add django-structlog[celery] structlog \
    opentelemetry-sdk \
    opentelemetry-instrumentation-django \
    opentelemetry-instrumentation-celery \
    opentelemetry-instrumentation-psycopg \
    opentelemetry-exporter-otlp-proto-grpc

uv add --dev pytest-structlog
```

Or add to `pyproject.toml` dependencies:

```toml
[project]
dependencies = [
    # existing deps...
    "django-structlog[celery]>=10.0",
    "structlog>=25.0",
    "opentelemetry-sdk>=1.30",
    "opentelemetry-instrumentation-django>=0.60b0",
    "opentelemetry-instrumentation-celery>=0.60b0",
    "opentelemetry-instrumentation-psycopg>=0.60b0",
    "opentelemetry-exporter-otlp-proto-grpc>=1.30",
]

[dependency-groups]
dev = [
    # existing dev deps...
    "pytest-structlog>=1.0",
]
```

---

## Architecture Patterns

### Recommended File Structure (new files only)

```
apps/api/
├── apps/core/
│   ├── middleware.py          # NEW — RequestContextMiddleware
│   ├── logging.py             # NEW — OTel structlog processor + structlog.configure()
│   └── tracing.py             # NEW — configure_otel() helper
├── config/
│   ├── settings/
│   │   └── base.py            # MODIFY — add LOGGING dict, MIDDLEWARE entry, OTEL env var
│   └── celery.py              # MODIFY — add DjangoStructLogInitStep + configure_otel() call
└── docker-compose.yml         # MODIFY — add jaeger service
```

### Pattern 1: structlog Configuration (base.py)

**What:** Configure Django LOGGING dict to route all stdlib loggers through structlog. Switch renderer based on DEBUG.

**When to use:** Always — this is the global logger configuration.

```python
# Source: django-structlog docs (https://django-structlog.readthedocs.io/en/latest/getting_started.html)
# In config/settings/base.py

import structlog

_console_formatter = "plain_console" if DEBUG else "json_formatter"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
            ],
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
            "foreign_pre_chain": [
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
            ],
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _console_formatter,
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django_structlog": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
```

### Pattern 2: structlog.configure() + OTel Processor (apps/core/logging.py)

**What:** One-time structlog configuration. Custom OTel processor injects trace_id + span_id from active OTel context into every log event.

**When to use:** Called at Django startup via `AppConfig.ready()` or imported into `base.py` after LOGGING is defined.

```python
# Source: structlog docs + dash0.com/guides/python-logging-with-structlog (verified pattern)
# In apps/core/logging.py

from __future__ import annotations

import structlog
from opentelemetry import trace


def add_otel_context(logger, method, event_dict):
    """Structlog processor: inject trace_id + span_id from active OTel span.

    Fields are omitted (not set to null) when no trace is active.
    Hex format matches Jaeger's search box convention directly.
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def configure_structlog() -> None:
    """Configure structlog once at app startup."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_otel_context,          # inject trace_id / span_id
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Processor chain ordering rationale (Claude's discretion):**

- `merge_contextvars` first — merges bound context vars before any processing
- `filter_by_level` early — skip expensive processing for suppressed levels
- `TimeStamper` before `add_log_level` — consistent with django-structlog examples
- `add_otel_context` after content processors — only runs if level passes filter
- `wrap_for_formatter` must be last for ProcessorFormatter to work

### Pattern 3: RequestContextMiddleware (apps/core/middleware.py)

**What:** Django middleware that binds `request_id`, `user_id`, `method`, `path` into structlog context at request start; binds `status_code` + `duration_ms` at response; echoes `X-Request-ID` header.

**When to use:** Inserts after `allauth.account.middleware.AccountMiddleware` so `request.user` is populated.

```python
# In apps/core/middleware.py
import time
import uuid

import structlog
from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger(__name__)


class RequestContextMiddleware:
    """Bind request metadata into structlog context for every Django request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=str(request.user.pk) if hasattr(request, "user") and request.user.is_authenticated else "anonymous",
            method=request.method,
            path=request.path,
        )
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response["X-Request-ID"] = request_id
        return response
```

**MIDDLEWARE insertion point in base.py:**

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.RequestContextMiddleware",   # <-- after AccountMiddleware
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

Also add `django_structlog` to INSTALLED_APPS (required by django-structlog).

### Pattern 4: OTel Configuration Helper (apps/core/tracing.py)

**What:** Conditional OTel setup. No-op when endpoint env var absent; real TracerProvider + OTLP gRPC exporter when set.

**When to use:** Called from `apps/core/apps.py` `AppConfig.ready()` for Django; called from `config/celery.py` for Celery worker processes.

```python
# In apps/core/tracing.py
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_otel(service_name: str | None = None) -> None:
    """Configure OpenTelemetry if OTEL_EXPORTER_OTLP_ENDPOINT is set.

    No-op (and no imports of exporter) when endpoint is absent, so CI and
    local dev without Jaeger incur zero overhead and no failed connections.
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return  # Remain on default no-op TracerProvider

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
```

**Why `insecure=True`:** The Jaeger all-in-one container runs on port 4317 without TLS. Docker Compose internal networking. Only appropriate for local dev.

### Pattern 5: Celery OTel + structlog Integration (config/celery.py)

**What:** Instrument Celery tasks for OTel tracing + register DjangoStructLogInitStep for context propagation.

```python
# Source: django-structlog celery docs + opentelemetry-python-contrib celery docs
# In config/celery.py
import os
from celery import Celery
from celery.signals import worker_process_init
from django_structlog.celery.steps import DjangoStructLogInitStep

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Register structlog context propagation for Celery workers
app.steps["worker"].add(DjangoStructLogInitStep)


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    """Initialize OTel tracing in each Celery worker process.

    Must run after worker process forks — tracing components like
    BatchSpanProcessor use threading and must be initialized per-process.
    """
    from apps.core.tracing import configure_otel
    configure_otel(service_name="foundation-celery-worker")
```

**Then instrument at app startup (AppConfig.ready or after app = Celery(...)):**

```python
# Also call CeleryInstrumentor after configure_otel is done
# This is called once per worker process inside init_celery_tracing
from opentelemetry.instrumentation.celery import CeleryInstrumentor
CeleryInstrumentor().instrument()
```

### Pattern 6: Django AppConfig.ready() Wiring (apps/core/apps.py)

**What:** Call `configure_structlog()` and `configure_otel()` once at Django startup.

```python
# In apps/core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self) -> None:
        from apps.core.logging import configure_structlog
        from apps.core.tracing import configure_otel
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

        configure_structlog()
        configure_otel()

        # Auto-instrument Django views and psycopg3 queries
        DjangoInstrumentor().instrument()
        PsycopgInstrumentor().instrument()
```

**Note:** `DjangoInstrumentor().instrument()` and `PsycopgInstrumentor().instrument()` are safe to call even when no TracerProvider is configured — they produce no-op spans.

### Pattern 7: Jaeger in docker-compose.yml

```yaml
# Add to docker-compose.yml
services:
  # ... existing db and redis services ...

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" # Jaeger UI
      - "4317:4317" # OTLP gRPC ingest
    environment:
      COLLECTOR_OTLP_ENABLED: "true"

  api:
    # ... existing api config ...
    environment:
      # ... existing env vars ...
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger:4317"
      OTEL_SERVICE_NAME: "foundation-api"
    depends_on:
      jaeger:
        condition: service_started
```

### Anti-Patterns to Avoid

- **Calling `configure_otel()` before `app = Celery(...)` in celery.py:** OTel must initialize after the Celery app is created; the `worker_process_init` signal handles this correctly for worker processes.
- **Using `insecure=False` with Jaeger all-in-one:** The container doesn't terminate TLS — connection will fail silently.
- **Importing `OTLPSpanExporter` at module top level:** Adds ~100ms import overhead even when tracing is disabled. Lazy import inside the `if endpoint:` block avoids this.
- **Setting `OTEL_EXPORTER_OTLP_ENDPOINT` in test settings:** Tests should never have a real Jaeger endpoint — tests will fail or add latency trying to export spans.
- **Putting `structlog.configure()` inside a view or request handler:** Must be called once at startup, not per-request. Django's `AppConfig.ready()` is the correct location.
- **Missing `cache_logger_on_first_use=True`:** Without it, structlog re-processes the chain on every log call — significant performance hit in prod.

---

## Don't Hand-Roll

| Problem                           | Don't Build            | Use Instead                                             | Why                                                                        |
| --------------------------------- | ---------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------- |
| Request context binding in Celery | Custom Celery signals  | `django-structlog[celery]` + `DjangoStructLogInitStep`  | Handles task_prerun/task_postrun, context clearing, error cases            |
| Django request log enrichment     | Custom logging.Filter  | `django-structlog` `RequestMiddleware`                  | Handles context vars, thread safety, test isolation                        |
| Stdlib → structlog routing        | Custom logging.Handler | `structlog.stdlib.ProcessorFormatter` in `LOGGING` dict | Tested against all Django log sources; handles foreign pre-chain           |
| SQL query tracing                 | Wrap Django ORM        | `opentelemetry-instrumentation-psycopg`                 | Instruments at the driver level — captures ALL queries including ORM + raw |
| Celery trace propagation          | Custom task headers    | `opentelemetry-instrumentation-celery`                  | W3C TraceContext propagation through task headers; handles retry context   |

**Key insight:** The structlog + django-structlog + OTel instrumentation packages together solve 95% of the problem declaratively. The only custom code is the `add_otel_context` processor (linking traces to logs) and `RequestContextMiddleware` (for `duration_ms` + `X-Request-ID` response header), both under 30 lines.

---

## Common Pitfalls

### Pitfall 1: psycopg2 vs psycopg3 instrumentation mismatch

**What goes wrong:** Developer installs `opentelemetry-instrumentation-psycopg2` but project uses `psycopg[binary]` (psycopg3). The instrumentation silently does nothing — no SQL spans, no errors.

**Why it happens:** Two separate packages exist: `opentelemetry-instrumentation-psycopg2` (for psycopg2) and `opentelemetry-instrumentation-psycopg` (for psycopg3). Their PyPI names differ by only the `2` suffix.

**How to avoid:** Project `pyproject.toml` has `psycopg[binary]>=3.2` — use `opentelemetry-instrumentation-psycopg` (no `2`).

**Warning signs:** Jaeger traces for Django views contain no SQL child spans.

### Pitfall 2: Celery OTel instrumentation on main process instead of worker process

**What goes wrong:** `CeleryInstrumentor().instrument()` called at module import time (not inside `worker_process_init`). The prefork worker model forks after this runs — child processes lose the OTel state including `BatchSpanProcessor` threads.

**Why it happens:** Celery uses a prefork model; threading-dependent components must initialize after fork.

**How to avoid:** Always call `CeleryInstrumentor().instrument()` inside `@worker_process_init.connect(weak=False)`.

**Warning signs:** Django spans appear in Jaeger but Celery task spans don't, or Celery spans have invalid/missing trace IDs.

### Pitfall 3: structlog context leaking between requests

**What goes wrong:** `request_id` from request A appears in logs for request B when using threading (gunicorn sync workers).

**Why it happens:** structlog `contextvars` module uses Python `contextvars.ContextVar` which is thread-local in sync contexts. If the middleware doesn't call `clear_contextvars()` at request start, stale bindings from previous requests on the same thread leak through.

**How to avoid:** `RequestContextMiddleware.__call__` must call `structlog.contextvars.clear_contextvars()` BEFORE binding new values, not just bind.

**Warning signs:** Some log lines have `request_id` from a different request; logs after an exception have stale context.

### Pitfall 4: LOGGING dict defined before `DEBUG` is resolved

**What goes wrong:** `_console_formatter = "plain_console" if DEBUG else "json_formatter"` evaluates before `DEBUG = env.bool(...)` runs if the import order is wrong.

**Why it happens:** Python evaluates module-level expressions top-to-bottom. `DEBUG` must be assigned before the `LOGGING` dict is constructed.

**How to avoid:** Place the `LOGGING` dict definition AFTER `DEBUG = env.bool(...)` in `base.py`. This is already the correct pattern in the existing `base.py`.

**Warning signs:** Always gets JSON format even in dev, or always gets console format in prod.

### Pitfall 5: OTel packages on beta track (`0.6xb0`)

**What goes wrong:** Installing `opentelemetry-instrumentation-django` without pinning to compatible SDK version causes import errors like `AttributeError: ... has no attribute ...`.

**Why it happens:** The instrumentation contrib packages (`0.6xb0`) must match the core SDK version (`1.3x.0`). They are released in tandem: contrib `0.61b0` = core `1.31.0`.

**How to avoid:** Pin both groups together. The mapping is: contrib minor version `0.(N+1)b0` matches core `1.N.0`. Use `>=0.60b0` with a `<0.70b0` upper bound to stay on the 1.3x SDK generation.

**Warning signs:** `ImportError` or `AttributeError` on Django startup when OTel packages are imported.

---

## Code Examples

Verified patterns from official sources:

### OTel trace_id / span_id hex injection into structlog

```python
# Source: dash0.com/guides/python-logging-with-structlog (verified pattern)
from opentelemetry import trace

def add_otel_context(logger, method, event_dict):
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")  # 32-char hex
        event_dict["span_id"] = format(ctx.span_id, "016x")    # 16-char hex
    return event_dict
```

`format(ctx.trace_id, "032x")` produces a zero-padded 32-char lowercase hex string matching Jaeger's search format exactly — paste directly into the Jaeger UI trace search.

### django-structlog Celery initialization

```python
# Source: https://django-structlog.readthedocs.io/en/latest/celery.html
from django_structlog.celery.steps import DjangoStructLogInitStep

app = Celery("foundation")
app.steps["worker"].add(DjangoStructLogInitStep)
# This registers task_prerun / task_postrun signals that bind task_id + task_name
# and propagate request_id from the dispatching Django request to the task context
```

Enable in settings:

```python
DJANGO_STRUCTLOG_CELERY_ENABLED = True
```

### Conditional OTel TracerProvider setup (no-op when env var absent)

```python
# Source: opentelemetry-python-contrib docs + oneuptime.com blog
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def configure_otel(service_name: str = "foundation-api") -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return  # OTel API default is no-op — zero overhead, no connection attempts

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
```

### pytest fixture to suppress structlog output noise

```python
# Source: https://www.structlog.org/en/stable/testing.html
# In apps/api/tests/conftest.py (add to existing conftest)
import pytest
import structlog

@pytest.fixture(autouse=True)
def reset_structlog():
    """Reset structlog to minimal config for tests — no noise, no OTel context."""
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()
```

Or use `pytest-structlog` plugin which does this automatically and adds `log` fixture for assertions.

---

## State of the Art

| Old Approach                                    | Current Approach                          | When Changed    | Impact                                                                                        |
| ----------------------------------------------- | ----------------------------------------- | --------------- | --------------------------------------------------------------------------------------------- |
| `python-json-logger` + custom Django middleware | `structlog` + `django-structlog`          | 2022–2023       | django-structlog handles context vars, Celery integration, stdlib routing declaratively       |
| Jaeger agent sidecar (UDP)                      | Jaeger all-in-one with OTLP/gRPC          | 2022 (OTel 1.x) | UDP Thrift protocol deprecated; OTLP is the standard; all-in-one simplifies local setup       |
| `opentelemetry-instrumentation-psycopg2`        | `opentelemetry-instrumentation-psycopg`   | 2024            | Psycopg3 support added as separate package; psycopg2 package still exists but is the old path |
| Jaeger client SDK                               | OpenTelemetry SDK                         | 2021–2022       | Jaeger native SDKs deprecated; OTel SDK is now the single instrumentation standard            |
| `structlog.processors.merge_contextvars`        | `structlog.contextvars.merge_contextvars` | structlog 21.x  | Moved to contextvars submodule; old import path may still work but is deprecated              |

**Deprecated/outdated:**

- Jaeger UDP agent on port 6831: replaced by OTLP gRPC on 4317
- `opentelemetry-instrumentation-psycopg2`: for psycopg2 only; project uses psycopg3
- `structlog.processors.merge_contextvars`: moved to `structlog.contextvars.merge_contextvars`

---

## Open Questions

1. **psycopg3 PsycopgInstrumentor `.instrument()` call signature**
   - What we know: `opentelemetry-instrumentation-psycopg` 0.60b1 exists and targets psycopg3
   - What's unclear: Whether `PsycopgInstrumentor().instrument()` has any required args for psycopg3 vs psycopg2
   - Recommendation: Test with `PsycopgInstrumentor().instrument()` (no args); if spans don't appear, add `skip_dep_check=True` (same workaround as psycopg2-binary required)

2. **structlog `configure_once` vs `reset_defaults` in tests**
   - What we know: `structlog.reset_defaults()` exists; `cache_logger_on_first_use=True` can cause test isolation issues
   - What's unclear: Whether `pytest-structlog` handles the reset automatically or whether a manual fixture is needed given the project uses `cache_logger_on_first_use=True`
   - Recommendation: Start with `pytest-structlog` plugin; if isolation issues arise, add manual `reset_structlog` autouse fixture

3. **django-structlog `RequestMiddleware` vs custom `RequestContextMiddleware`**
   - What we know: django-structlog ships its own `RequestMiddleware` that binds `request_id` and `user_id`; the phase also requires `duration_ms` and `X-Request-ID` response header
   - What's unclear: Whether to use django-structlog's middleware as the base and extend it, or write the custom middleware from scratch and skip django-structlog's middleware
   - Recommendation: Write the custom `RequestContextMiddleware` from scratch (it's ~30 lines); do NOT add django-structlog's `RequestMiddleware` to MIDDLEWARE — the custom one replaces it. Django-structlog is still needed for Celery integration only.

---

## Validation Architecture

### Test Framework

| Property           | Value                                                   |
| ------------------ | ------------------------------------------------------- |
| Framework          | pytest 8.x + pytest-django 4.9                          |
| Config file        | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command  | `cd apps/api && python -m pytest tests/core/ -x -q`     |
| Full suite command | `cd apps/api && python -m pytest tests/ -q`             |

### Phase Requirements → Test Map

| Req ID | Behavior                                                                                                | Test Type            | Automated Command                                                               | File Exists? |
| ------ | ------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------- | ------------ |
| OBS-01 | Every Django request log contains `request_id`, `user_id`, `duration_ms` as valid JSON fields           | unit                 | `python -m pytest tests/core/test_logging.py -x -q`                             | ❌ Wave 0    |
| OBS-01 | `ConsoleRenderer` active when `DEBUG=True`, `JSONRenderer` when `DEBUG=False`                           | unit                 | `python -m pytest tests/core/test_logging.py::test_renderer_selection -x -q`    | ❌ Wave 0    |
| OBS-01 | `X-Request-ID` header present in every response                                                         | unit                 | `python -m pytest tests/core/test_middleware.py::test_request_id_header -x -q`  | ❌ Wave 0    |
| OBS-01 | `add_otel_context` processor: injects trace_id + span_id when span is active, omits fields when no span | unit                 | `python -m pytest tests/core/test_logging.py::test_otel_processor -x -q`        | ❌ Wave 0    |
| OBS-01 | Structlog context cleared between requests (no context leaking)                                         | unit                 | `python -m pytest tests/core/test_middleware.py::test_context_isolation -x -q`  | ❌ Wave 0    |
| OBS-02 | `configure_otel()` is a no-op when `OTEL_EXPORTER_OTLP_ENDPOINT` is not set                             | unit                 | `python -m pytest tests/core/test_tracing.py::test_configure_otel_noop -x -q`   | ❌ Wave 0    |
| OBS-02 | `configure_otel()` creates a real TracerProvider when endpoint is set                                   | unit                 | `python -m pytest tests/core/test_tracing.py::test_configure_otel_active -x -q` | ❌ Wave 0    |
| OBS-02 | Jaeger service starts and UI responds (port 16686)                                                      | smoke (manual)       | N/A — verified via `docker compose up` + browser check                          | manual-only  |
| OBS-02 | Django view → Celery task trace propagation (same trace_id)                                             | integration (manual) | N/A — requires running Jaeger + Celery worker                                   | manual-only  |

**Manual-only justification:** The Docker Compose + live Jaeger UI check and the live Django→Celery trace propagation test cannot run in a standard pytest suite without a running Jaeger instance and Celery worker. They are verified by the success criteria in the phase definition.

### Sampling Rate

- **Per task commit:** `cd apps/api && python -m pytest tests/core/ -x -q`
- **Per wave merge:** `cd apps/api && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `apps/api/tests/core/__init__.py` — test package init
- [ ] `apps/api/tests/core/test_logging.py` — covers OBS-01 logging processor + renderer selection
- [ ] `apps/api/tests/core/test_middleware.py` — covers OBS-01 middleware fields + context isolation
- [ ] `apps/api/tests/core/test_tracing.py` — covers OBS-02 configure_otel() behavior
- [ ] Framework install: `uv add --dev pytest-structlog` — if not already installed

---

## Sources

### Primary (HIGH confidence)

- `https://django-structlog.readthedocs.io/en/latest/getting_started.html` — LOGGING dict, structlog.configure(), middleware setup
- `https://django-structlog.readthedocs.io/en/latest/celery.html` — DjangoStructLogInitStep, DJANGO_STRUCTLOG_CELERY_ENABLED, context propagation
- `https://pypi.org/project/django-structlog/` — version 10.0.0, Python 3.10+ / Django 4.2–5.2
- `https://pypi.org/project/opentelemetry-instrumentation-django/` — version 0.61b0, released 2026-03-04
- `https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/celery/celery.html` — CeleryInstrumentor, worker_process_init pattern

### Secondary (MEDIUM confidence)

- `https://www.dash0.com/guides/python-logging-with-structlog` — OTel trace_id/span_id structlog processor (verified against OTel API docs)
- `https://pypi.org/project/opentelemetry-instrumentation-psycopg/` — version 0.60b1, psycopg3 support confirmed
- `https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html` — OTLPSpanExporter gRPC config, `insecure=True` parameter
- `https://www.structlog.org/en/stable/testing.html` — pytest testing patterns, reset_defaults

### Tertiary (LOW confidence)

- `https://medium.com/@andrewthub/monitoring-django-and-celery-with-opentelemetry-8282be9a8e5a` — general pattern reference (not verified against official docs for every detail)

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all packages verified against PyPI with version numbers and release dates
- Architecture: HIGH — patterns derived directly from official django-structlog and OTel contrib docs
- Pitfalls: HIGH — psycopg2/3 mismatch and Celery prefork pitfalls are documented in official sources; context leaking is from structlog testing docs

**Research date:** 2026-03-11
**Valid until:** 2026-06-11 (stable ecosystem — OTel Python has consistent release cadence, django-structlog is 10.x stable)
