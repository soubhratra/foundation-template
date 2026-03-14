from typing import Any

from django.http import HttpRequest
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import IsAuthenticated

from apps.api_keys.auth import ApiKeyAuth, RequireScope
from apps.api_keys.schemas import APIKeyCreateOut, APIKeyIn, APIKeyOut, PingOut
from apps.api_keys.services import APIKeyService


@api_controller(
    "/me/api-keys",
    tags=["api-keys"],
    permissions=[IsAuthenticated],
)
class APIKeyController(ControllerBase):
    """Manage API keys for the authenticated user.

    Management endpoints use session auth (web UI). The ApiKeyAuth backend
    is registered separately on product endpoints that accept key-based access.
    """

    @route.post("/", response={201: APIKeyCreateOut}, url_name="api_key_create")
    def create_key(self, request: HttpRequest, body: APIKeyIn) -> Any:
        """Create a new API key. Raw key returned ONCE — copy and store immediately."""
        api_key, raw_key = APIKeyService.create(
            user=request.user,
            name=body.name,
            scopes=body.scopes,
        )
        return 201, {
            "id": str(api_key.id),
            "name": api_key.name,
            "scopes": api_key.scopes,
            "prefix": api_key.prefix,
            "is_active": api_key.is_active,
            "created_at": api_key.created_at,
            "key": raw_key,
        }

    @route.get("/", response={200: dict}, url_name="api_key_list")
    def list_keys(self, request: HttpRequest, page: int = 1, page_size: int = 20) -> Any:
        """List all API keys for the authenticated user. Raw key is never returned here."""
        result = APIKeyService.list_for_user(user=request.user, page=page, page_size=page_size)
        # Serialize results using APIKeyOut (no key field)
        result["results"] = [
            APIKeyOut(
                id=str(k.id),
                name=k.name,
                scopes=k.scopes,
                prefix=k.prefix,
                is_active=k.is_active,
                last_used_at=k.last_used_at,
                usage_count=k.usage_count,
                created_at=k.created_at,
            ).model_dump()
            for k in result["results"]
        ]
        return 200, result

    @route.get(
        "/ping/",
        auth=[ApiKeyAuth()],
        permissions=[IsAuthenticated, RequireScope("read")],
        response={200: PingOut},
        url_name="api_key_ping",
    )
    def ping(self, request: HttpRequest) -> Any:
        """Verify the API key is valid and has read scope.

        Returns {"status": "ok"} when the full chain passes:
        ApiKeyAuth (token lookup + usage tracking) -> RequireScope (scope check) ->
        ApiKeyRateLimitMiddleware (rate limit + X-RateLimit-* headers).

        This endpoint stays in every product built from the template — it is a
        standard developer ergonomics affordance for verifying a key is functional.
        """
        return 200, {"status": "ok"}

    @route.delete("/{key_id}/", response={204: None}, url_name="api_key_revoke")
    def revoke_key(self, request: HttpRequest, key_id: str) -> Any:
        """Revoke an API key. Revoked keys cannot authenticate requests."""
        APIKeyService.revoke(user=request.user, key_id=key_id)
        return 204, None
