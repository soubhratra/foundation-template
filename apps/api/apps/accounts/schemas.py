from typing import Optional

from ninja import Field, Schema


class UserOut(Schema):
    id: int
    email: str
    full_name: Optional[str] = Field(None, max_length=255)

    @staticmethod
    def resolve_full_name(user):
        if hasattr(user, "full_name"):
            value = (getattr(user, "full_name") or "").strip()
            if value:
                return value
        if hasattr(user, "get_full_name"):
            value = (user.get_full_name() or "").strip()
            if value:
                return value
        if hasattr(user, "first_name"):
            value = (getattr(user, "first_name") or "").strip()
            if value:
                return value
        return None


class UserUpdateIn(Schema):
    full_name: Optional[str] = Field(None, max_length=255)
