from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .schemas import UserUpdateIn

User = get_user_model()


def invalidate_user_sessions(user_id: int) -> int:
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    deleted = 0
    for session in sessions:
        data = session.get_decoded()
        if str(user_id) == data.get("_auth_user_id"):
            session.delete()
            deleted += 1
    return deleted


def invalidate_user_tokens(user_id: int) -> int:
    """
    Invalidate all JWT tokens for a user by clearing their session data.

    When using stateful JWT validation (HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED),
    JWT refresh tokens are stored in the Django session. By invalidating all
    sessions for the user, we also invalidate all refresh tokens.

    Additionally, we track invalidated access tokens in a blocklist within each
    session to prevent their use even before expiration.

    Returns:
        Number of sessions that had tokens invalidated.
    """
    from allauth.headless.tokens.strategies.jwt import internal as jwt_internal

    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    invalidated = 0

    for session in sessions:
        data = session.get_decoded()
        if str(user_id) != data.get("_auth_user_id"):
            continue

        # Clear refresh tokens from session
        refresh_tokens = data.get("headless_refresh_tokens", {})
        if refresh_tokens:
            # Clear the refresh tokens - this prevents token refresh
            session_data = session.get_decoded()
            session_data["headless_refresh_tokens"] = {}
            # Store invalidated token IDs for access token blocklist
            invalidated_tokens = session_data.get("headless_invalidated_tokens", [])
            invalidated_tokens.extend(refresh_tokens.keys())
            session_data["headless_invalidated_tokens"] = invalidated_tokens

            # Save the modified session data
            session.session_data = Session.objects.encode(session_data)
            session.save()
            invalidated += 1
        elif "headless_refresh_tokens" in data:
            # Refresh tokens key exists but is empty - still count as processed
            invalidated += 1

    return invalidated


class UserService:
    def get_user(self, user_id: int) -> User:
        return get_object_or_404(User, id=user_id)

    def update_user(self, user_id: int, data: UserUpdateIn) -> User:
        user = get_object_or_404(User, id=user_id)
        updates = data.dict(exclude_unset=True)
        fields_to_update: list[str] = []

        if "full_name" in updates:
            value = updates.pop("full_name")
            normalized = (value or "").strip()
            if hasattr(user, "full_name"):
                setattr(user, "full_name", normalized)
                fields_to_update.append("full_name")
            elif hasattr(user, "first_name"):
                setattr(user, "first_name", normalized)
                fields_to_update.append("first_name")

        for field, value in updates.items():
            setattr(user, field, value)
            fields_to_update.append(field)

        if fields_to_update:
            user.save(update_fields=fields_to_update)
        return user
