"""Per-key rate limiting middleware for API key authenticated requests.

Implements AKEY-02: enforce per-key rate limits and inject X-RateLimit-*
response headers on all API key authenticated responses.
"""

import time

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django_ratelimit.core import get_usage


class ApiKeyRateLimitMiddleware:
    """Enforce per-key rate limiting and inject X-RateLimit-* response headers.

    Only activates when request.api_key is set (API key authenticated requests).
    Session-authenticated requests pass through unchanged.

    Rate limit key: api_key.prefix (e.g. "ft_a1b2c3d4") — unique per key.
    Rate limit value: settings.API_KEY_RATE_LIMIT (default "1000/h").

    Uses django-ratelimit get_usage() as the single counter source:
    - increment=True: enforces the limit (increments counter)
    - X-RateLimit-* headers derived from same counter — no drift

    PITFALLS:
    - group= parameter is required by get_usage() — raises ImproperlyConfigured if omitted
    - key= MUST be a callable — key=lambda g, r: api_key.prefix (not a string)
    - Inject headers unconditionally when usage is not None (both 200 and 429 paths)
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        api_key = getattr(request, "api_key", None)
        if api_key is None:
            # Session-authenticated request — no rate limit for API key middleware
            return self.get_response(request)

        rate: str = getattr(settings, "API_KEY_RATE_LIMIT", "1000/h")
        usage = get_usage(
            request,
            group="api_key",  # Required — raises ImproperlyConfigured if absent
            key=lambda g, r: api_key.prefix,  # Callable closure — string would fail
            rate=rate,
            increment=True,  # Enforce limit (counts this request)
        )

        if usage and usage["should_limit"]:
            from apps.core.ratelimit import ratelimited_error

            response = ratelimited_error(request)
            if usage:
                self._inject_headers(response, usage, rate)
            return response

        response = self.get_response(request)
        if usage:
            self._inject_headers(response, usage, rate)
        return response

    def _inject_headers(self, response: HttpResponse, usage: dict, rate: str) -> None:
        """Inject X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers."""
        limit: int = usage["limit"]
        count: int = usage["count"]
        remaining: int = max(0, limit - count)
        reset_ts: int = int(time.time()) + max(0, usage["time_left"])
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)
        response["X-RateLimit-Reset"] = str(reset_ts)
