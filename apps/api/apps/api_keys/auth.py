import hashlib
import hmac

from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from ninja.security import HttpBearer
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

from apps.api_keys.models import APIKey


class ApiKeyAuth(HttpBearer):
    """Resolve Bearer token to User; set request.api_key for downstream middleware.

    Ninja calls authenticate(request, token) after extracting the token from
    the Authorization: Bearer <token> header. Returns None to fail auth (Ninja
    tries the next configured backend). Returns the User to succeed.

    Side effects on success:
    - Sets request.api_key = api_key (used by RequireScope and rate limit middleware)
    - Sets request.user = api_key.user (IsAuthenticated passes; all user-based logic works)
    - Updates last_used_at and increments usage_count via partial UPDATE (AKEY-03)
    """

    def authenticate(self, request: HttpRequest, token: str) -> object | None:
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        try:
            # select_related to prevent N+1 on api_key.user access
            api_key = APIKey.objects.select_related("user").get(key_hash=key_hash, is_active=True)
        except APIKey.DoesNotExist:
            return None

        # Timing-safe comparison — defense-in-depth even though DB lookup already found by hash
        if not hmac.compare_digest(api_key.key_hash, key_hash):
            return None

        # Update usage tracking (AKEY-03) — partial UPDATE avoids lock on unrelated fields
        APIKey.objects.filter(pk=api_key.pk).update(
            last_used_at=timezone.now(),
            usage_count=models.F("usage_count") + 1,
        )
        api_key.refresh_from_db(fields=["last_used_at", "usage_count"])

        # Set on request for RequireScope and ApiKeyRateLimitMiddleware
        request.api_key = api_key  # type: ignore[attr-defined]
        request.user = api_key.user  # type: ignore[attr-defined]
        return api_key.user


class RequireScope(BasePermission):
    """Gate access to API key requests that carry the required scope.

    CRITICAL: Rejects session-authenticated requests entirely.
    A request with a valid session cookie but no API key Bearer token
    is rejected with HTTP 403 — there is NO auth fallback.
    This matches success criteria AKEY-01 exactly.

    Usage:
        permissions=[IsAuthenticated, RequireScope("read")]

    IsAuthenticated MUST appear first in the list. RequireScope raises
    PermissionDenied (-> 403) if:
    - request.api_key is absent (session-only request)
    - request.api_key.scopes does not include the required scope
    """

    def __init__(self, scope: str) -> None:
        self.scope = scope

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        api_key = getattr(request, "api_key", None)
        if api_key is None:
            # Session-authenticated request — no API key Bearer token present
            raise PermissionDenied
        if self.scope not in (api_key.scopes or []):
            raise PermissionDenied
        return True
