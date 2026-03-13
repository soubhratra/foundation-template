"""Models for the orgs B2B module.

Provides four models:
- Organization: the core multi-tenant entity (name, slug, owner)
- Membership: user membership in an org with owner/admin/member roles
- Invitation: email-based invite with 72-hour token expiry
- OrgCustomer: per-org Stripe customer record, mirrors apps/billing/models.py Customer

These models are the data foundation for all Phase 26+ B2B features.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

INVITATION_EXPIRY_HOURS = 72


class Organization(models.Model):
    """A multi-tenant organization.

    Each Organization has a unique slug used in all URL paths
    (e.g. /api/v1/org/{slug}/). The owner field records which user
    created the org; Membership is the authoritative role source.
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_orgs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_organization"

    def __str__(self) -> str:
        return f"Organization({self.slug})"


class Membership(models.Model):
    """A user's membership in an organization with an explicit role.

    unique_together enforces one membership per (org, user) pair at
    the database level, preventing duplicate memberships.
    """

    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_membership"
        unique_together = [("org", "user")]

    def __str__(self) -> str:
        return f"Membership({self.user.email} -> {self.org.slug} as {self.role})"


class Invitation(models.Model):
    """An email-based invitation to join an Organization.

    Tokens are generated with secrets.token_urlsafe(48) (cryptographically
    random). Invitations expire after INVITATION_EXPIRY_HOURS (72h).
    is_valid() is the canonical check before accepting.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        EXPIRED = "expired", _("Expired")
        REVOKED = "revoked", _("Revoked")

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orgs_invitation"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["email", "status"]),
        ]

    def is_valid(self) -> bool:
        """Return True if this invitation is still pending and not expired."""
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()

    @staticmethod
    def generate_token() -> str:
        """Generate a cryptographically random URL-safe token (64 chars)."""
        return secrets.token_urlsafe(48)

    @staticmethod
    def make_expiry() -> "timezone.datetime":
        """Return the expiry datetime for a new invitation (now + 72h)."""
        return timezone.now() + timedelta(hours=INVITATION_EXPIRY_HOURS)


class OrgCustomer(models.Model):
    """Per-org Stripe customer record.

    Mirrors apps/billing/models.py Customer exactly — one-to-one with
    Organization. Auto-created via post_save signal in apps/orgs/signals.py
    so that a Stripe customer is always available when an org exists.
    """

    org = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="billing_customer",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orgs_orgcustomer"

    def __str__(self) -> str:
        return f"OrgCustomer({self.org.slug})"
