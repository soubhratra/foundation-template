"""Request/response schemas for the orgs B2B module.

All schemas use Ninja's Schema base class (Pydantic v2 under the hood).
OrgIn slug validator enforces lowercase-alphanumeric-hyphen format at the
API boundary; service layer normalises to lowercase for defence in depth.
"""

import re
from datetime import datetime

from ninja import Schema
from pydantic import field_validator


class OrgIn(Schema):
    """Request body for creating an org."""

    name: str
    slug: str

    @field_validator("slug")
    @classmethod
    def slug_must_be_lowercase_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v.lower()


class OrgOut(Schema):
    """Response schema for an Organization."""

    id: int
    name: str
    slug: str
    created_at: datetime


class OrgUpdateIn(Schema):
    """Request body for updating an org (PATCH — all fields optional)."""

    name: str | None = None


class MemberOut(Schema):
    """Response schema for a Membership row.

    email maps from membership.user.email (select_related join).
    joined_at maps from membership.created_at (alias set via model_validator).
    """

    user_id: int
    email: str
    role: str
    joined_at: datetime


class RoleUpdateIn(Schema):
    """Request body for changing a member's role."""

    role: str  # "owner" | "admin" | "member" — range validated in service layer


class TransferOwnershipIn(Schema):
    """Request body for transferring org ownership."""

    new_owner_user_id: int


class InviteIn(Schema):
    """Request body for sending an invitation."""

    email: str


class InviteOut(Schema):
    """Response schema for an Invitation."""

    id: int
    invited_email: str  # maps from invitation.email (alias)
    status: str
    expires_at: datetime
    created_at: datetime


class AcceptInviteOut(Schema):
    """Response schema for invitation acceptance."""

    redirect: str | None = None
    message: str | None = None
    status: str | None = None
