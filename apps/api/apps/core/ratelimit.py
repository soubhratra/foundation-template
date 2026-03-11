"""Custom 429 handler for rate-limited requests.

Per RFC 6585, rate-limited responses use HTTP 429 (Too Many Requests)
with a Retry-After header indicating when the client may retry.

Wire via: RATELIMIT_VIEW = "apps.core.ratelimit.ratelimited_error" in settings.
"""

from django.http import HttpRequest, JsonResponse


def ratelimited_error(request: HttpRequest, exception: Exception | None = None) -> JsonResponse:
    """Return RFC 6585 compliant 429 response with Retry-After header.

    The Retry-After value is the rate window length in seconds.
    Default 60 seconds matches the '5/m' (per-minute) window.
    Projects using tighter windows (e.g., '5/s') should override this view
    or compute the value from RATELIMIT_AUTH_LOGIN dynamically.
    """
    response = JsonResponse(
        {
            "error": {
                "code": "RATE_001",
                "message": "Too many requests. Please try again later.",
            }
        },
        status=429,
    )
    response["Retry-After"] = "60"  # seconds — matches '5/m' window
    return response
