import hashlib
import secrets
import uuid

from django.conf import settings
from django.db import models


class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    prefix = models.CharField(max_length=32, unique=True)
    key_hash = models.CharField(max_length=64)  # SHA-256 hex — 64 chars
    scopes = models.JSONField(default=list)
    name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_keys_key"
        indexes = [
            models.Index(fields=["key_hash"]),  # Auth lookup — high cardinality
            models.Index(fields=["user", "is_active"]),  # List keys for user
            models.Index(fields=["prefix"]),  # Display lookups
        ]

    def __str__(self) -> str:
        return f"{self.prefix} ({self.name or 'unnamed'})"

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Return (raw_key, stored_prefix, key_hash).

        raw_key:        full key shown once to user — NEVER stored
        stored_prefix:  API_KEY_PREFIX + first 8 chars of random (e.g. ft_a1b2c3d4)
        key_hash:       SHA-256 hex of raw_key — stored for auth backend lookup

        Security: 64 hex chars from secrets.token_hex(32) = 256 bits entropy.
        Using secrets module (CSPRNG), not random. Identical approach to Phase 27
        WebhookEndpoint.generate_secret().
        """
        prefix_setting: str = getattr(settings, "API_KEY_PREFIX", "ft_")
        random_part: str = secrets.token_hex(32)  # 64 lowercase hex chars
        raw_key = f"{prefix_setting}{random_part}"
        stored_prefix = f"{prefix_setting}{random_part[:8]}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, stored_prefix, key_hash
