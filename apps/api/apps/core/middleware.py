"""RequestContextMiddleware, ObservabilityMiddleware, and AuthRateLimitMiddleware.

RequestContextMiddleware — injects request context into structlog for every request.
Binds: request_id (UUID4), user_id (pk or "anonymous"), method, path.
After response: binds status_code, duration_ms.
Echoes X-Request-ID as a response header for API client bug reports.

No raw client IP — avoids GDPR friction. Per-project opt-in if needed.

Insert RequestContextMiddleware AFTER allauth.account.middleware.AccountMiddleware
in MIDDLEWARE so request.user is populated before user_id is read.

ObservabilityMiddleware — auto-captures unhandled Django exceptions.
Insert AFTER RequestContextMiddleware in MIDDLEWARE.

AuthRateLimitMiddleware — path-scoped rate limiting for /api/v1/auth/ routes.
Insert AFTER ObservabilityMiddleware in MIDDLEWARE.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from django.http import HttpRequest, HttpResponse
from django_ratelimit.core import is_ratelimited

from apps.core.observability import get_observability_adapter

logger = structlog.get_logger(__name__)


class RequestContextMiddleware:
    """Bind request metadata into structlog context for every Django request."""

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid.uuid4())

        # Clear stale context from the previous request on this thread.
        # CRITICAL: must call clear_contextvars() before bind_contextvars()
        # to prevent context leaking between requests on gunicorn sync workers.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=(
                str(request.user.pk)
                if hasattr(request, "user") and request.user.is_authenticated
                else "anonymous"
            ),
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


class ObservabilityMiddleware:
    """Auto-capture unhandled Django exceptions via the configured adapter.

    Sits after RequestContextMiddleware so request.user is already populated.
    Returns None to continue Django's normal 500 flow (DEBUG pages, logging, etc.).
    Does NOT re-raise — Django propagates the exception naturally after process_exception
    returns None.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Capture exception with user context.

        Returns None to continue Django's normal 500 flow.
        """
        context: dict[str, Any] = {
            "user_id": (
                str(request.user.pk)
                if hasattr(request, "user") and request.user.is_authenticated
                else "anonymous"
            ),
            "path": request.path,
            "method": request.method,
            "exc_type": type(exception).__name__,
        }
        get_observability_adapter().capture_exception(exception, context)
        # Return None — Django continues its normal exception processing chain.
        # The exception propagates, gets logged, and the 500 response is generated normally.
        return None


# Auth endpoint URL prefixes subject to rate limiting.
# Covers both browser-session and app (JWT) allauth headless flows.
_AUTH_RATE_LIMIT_PATHS = (
    "/api/v1/auth/browser/v1/",
    "/api/v1/auth/app/v1/",
)


class AuthRateLimitMiddleware:
    """Rate-limit allauth headless auth endpoints via is_ratelimited() helper.

    Applied as middleware (not @ratelimit decorator) because allauth's headless
    views are registered internally and are not owned code.

    RATELIMIT_FAIL_OPEN = True means requests pass through if Redis is
    unreachable — auth availability is prioritised over strict enforcement
    during cache outages.

    Disabled in tests via conftest autouse fixture:
        settings.RATELIMIT_ENABLE = False
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith(_AUTH_RATE_LIMIT_PATHS):
            from django.conf import settings

            rate = getattr(settings, "RATELIMIT_AUTH_LOGIN", "5/m")
            limited = is_ratelimited(
                request,
                group="auth",
                key="ip",
                rate=rate,
                increment=True,
            )
            if limited:
                from apps.core.ratelimit import ratelimited_error

                return ratelimited_error(request)
        return self.get_response(request)
