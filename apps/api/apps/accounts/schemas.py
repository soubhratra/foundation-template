from datetime import datetime

from ninja import Field, Schema


class UserOut(Schema):
    id: int
    email: str
    full_name: str | None = Field(None, max_length=255)

    @staticmethod
    def resolve_full_name(user):
        if hasattr(user, "full_name"):
            value = (user.full_name or "").strip()
            if value:
                return value
        if hasattr(user, "get_full_name"):
            value = (user.get_full_name() or "").strip()
            if value:
                return value
        if hasattr(user, "first_name"):
            value = (user.first_name or "").strip()
            if value:
                return value
        return None


class UserUpdateIn(Schema):
    full_name: str | None = Field(None, max_length=255)


# ---------------------------------------------------------------------------
# RBAC schemas — AdminController (Phase 22-03)
# ---------------------------------------------------------------------------


class AdminUserOut(Schema):
    """User representation for admin listing endpoints."""

    id: int
    email: str
    first_name: str
    last_name: str
    groups: list[str]
    date_joined: datetime

    @staticmethod
    def resolve_groups(user):
        return [g.name for g in user.groups.all()]


class RoleAssignIn(Schema):
    """Payload for role assignment requests."""

    role: str


class UserRoleOut(Schema):
    """Role listing response for a single user."""

    user_id: int
    roles: list[str]
