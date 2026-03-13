from datetime import datetime

from django.conf import settings
from ninja import Schema
from pydantic import field_validator


class APIKeyIn(Schema):
    """Request body for POST /me/api-keys/."""

    name: str = ""
    scopes: list[str]

    @field_validator("scopes")
    @classmethod
    def scopes_must_be_valid(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("scopes must contain at least one scope.")
        valid = set(getattr(settings, "API_KEY_SCOPES", {}).keys())
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Unknown scopes: {sorted(invalid)}. Valid scopes: {sorted(valid)}")
        return v


class APIKeyCreateOut(Schema):
    """Returned ONLY from POST /me/api-keys/ — includes raw key shown once."""

    id: str
    name: str
    scopes: list[str]
    prefix: str  # e.g. "ft_a1b2c3d4" — human-visible identifier in list views
    is_active: bool
    created_at: datetime
    key: str  # Raw key — COPY AND STORE IMMEDIATELY; never shown again


class APIKeyOut(Schema):
    """Returned for list and management operations — NO key field."""

    id: str
    name: str
    scopes: list[str]
    prefix: str
    is_active: bool
    last_used_at: datetime | None
    usage_count: int
    created_at: datetime
