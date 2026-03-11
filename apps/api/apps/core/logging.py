"""Structlog configuration and OTel-aware log processor for Phase 13.

Call configure_structlog() once at Django startup via CoreConfig.ready().
add_otel_context is a structlog processor that injects trace_id + span_id
from the active OpenTelemetry span into every log event.
Fields are omitted (not set to None) when no trace is active.
"""

from __future__ import annotations

import structlog
from opentelemetry import trace


def add_otel_context(logger, method, event_dict: dict) -> dict:
    """Structlog processor: inject trace_id + span_id from active OTel span.

    Hex format (032x / 016x) matches Jaeger search box — paste directly.
    Fields are omitted when no trace is active so log parsers see clean events.
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def configure_structlog() -> None:
    """Configure structlog once at app startup.

    Processor chain ordering:
    1. merge_contextvars — merge bound context vars before any processing
    2. filter_by_level — skip expensive processing for suppressed levels early
    3. TimeStamper — ISO timestamp before add_log_level (django-structlog convention)
    4. add_logger_name — module name for log routing
    5. add_log_level — level string
    6. PositionalArgumentsFormatter — %s-style format args
    7. StackInfoRenderer — captures stack info if requested
    8. format_exc_info — formats exception info
    9. add_otel_context — inject trace_id/span_id (after level filter to avoid waste)
    10. UnicodeDecoder — ensure all values are unicode
    11. wrap_for_formatter — MUST be last; hands off to ProcessorFormatter in LOGGING dict
    """
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
            add_otel_context,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
