from django.http import Http404

from apps.api_keys.models import APIKey
from apps.audit.context import audit_context


class APIKeyService:
    @classmethod
    def create(cls, user, name: str, scopes: list[str], org=None) -> tuple[APIKey, str]:
        """Create a new APIKey. Returns (api_key, raw_key).

        raw_key is returned here and NOWHERE ELSE — caller must include in response.
        org_id is injected into pghistory context so the event appears in the org audit log.
        """
        raw_key, stored_prefix, key_hash = APIKey.generate_key()
        with audit_context(user_id=user.pk, org_id=str(org.id) if org else None):
            api_key = APIKey.objects.create(
                user=user,
                org=org,
                prefix=stored_prefix,
                key_hash=key_hash,
                scopes=scopes,
                name=name,
                is_active=True,
            )
        return api_key, raw_key

    @classmethod
    def revoke(cls, user, key_id: str) -> None:
        """Revoke an API key by setting is_active=False.

        Raises Http404 if the key does not exist or does not belong to the user.
        org_id resolved via select_related("org") and injected into pghistory context.
        """
        try:
            api_key = APIKey.objects.select_related("org").get(id=key_id, user=user)
        except APIKey.DoesNotExist:
            raise Http404 from None
        with audit_context(user_id=user.pk, org_id=str(api_key.org.id) if api_key.org_id else None):
            api_key.is_active = False
            api_key.save(update_fields=["is_active"])

    @classmethod
    def list_for_user(cls, user, page: int = 1, page_size: int = 20) -> dict:
        """Return paginated list of active and inactive keys for user."""
        qs = APIKey.objects.filter(user=user).select_related("org").order_by("-created_at")
        total = qs.count()
        start = (page - 1) * page_size
        results = list(qs[start : start + page_size])
        return {
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": results,
        }
