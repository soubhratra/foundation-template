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
