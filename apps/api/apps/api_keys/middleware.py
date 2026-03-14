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
        # Check for API key BEFORE calling the view (handles middleware-level attachment).
        # If not set yet, call the view first — Django Ninja authentication sets
        # request.api_key inside the view dispatch cycle — then check again after.
        api_key = getattr(request, "api_key", None)
        if api_key is not None:
            return self._apply_rate_limit(request, api_key)

        # Call the view — authentication happens here (sets request.api_key on success)
        view_response = self.get_response(request)

        # Check again after the view — api_key may now be set by ApiKeyAuth.authenticate()
        api_key = getattr(request, "api_key", None)
        if api_key is None:
            # Session-authenticated or unauthenticated request — no rate limit headers
            return view_response

        # Key was authenticated during view dispatch; enforce rate limit and inject headers.
        # increment=True counts this request and enforces the limit.
        # If exceeded, replace the view response with a 429.
        rate: str = getattr(settings, "API_KEY_RATE_LIMIT", "1000/h")
        usage = get_usage(
            request,
            group="api_key",
            key=lambda g, r: api_key.prefix,
            rate=rate,
            increment=True,
        )

        if usage and usage["should_limit"]:
            from apps.core.ratelimit import ratelimited_error

            response = ratelimited_error(request)
            self._inject_headers(response, usage, rate)
            return response

        if usage:
            self._inject_headers(view_response, usage, rate)
        return view_response

    def _apply_rate_limit(self, request: HttpRequest, api_key) -> HttpResponse:  # type: ignore[type-arg]
        """Apply rate limiting for a pre-authenticated request (api_key already on request)."""
        rate: str = getattr(settings, "API_KEY_RATE_LIMIT", "1000/h")
        usage = get_usage(
            request,
            group="api_key",
            key=lambda g, r: api_key.prefix,
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
