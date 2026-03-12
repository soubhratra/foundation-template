import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .schemas import UserUpdateIn

User = get_user_model()
logger = logging.getLogger(__name__)


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
                user.full_name = normalized
                fields_to_update.append("full_name")
            elif hasattr(user, "first_name"):
                user.first_name = normalized
                fields_to_update.append("first_name")

        for field, value in updates.items():
            setattr(user, field, value)
            fields_to_update.append(field)

        if fields_to_update:
            user.save(update_fields=fields_to_update)
        return user

    # ------------------------------------------------------------------
    # RBAC role management methods (Phase 22-03)
    # ------------------------------------------------------------------

    def list_users(self, page: int = 1, page_size: int = 20):
        """Return a page of all users with their groups prefetched.

        prefetch_related("groups") is required to avoid N+1 queries —
        the global _nplusone_guard fixture in tests/conftest.py will catch
        any violation during tests.
        """
        offset = (page - 1) * page_size
        return User.objects.prefetch_related("groups").order_by("id")[offset : offset + page_size]

    def get_user_roles(self, user_id: int) -> list[str]:
        """Return the list of role (group) names for a user."""
        user = get_object_or_404(User, id=user_id)
        return [g.name for g in user.groups.all()]

    def assign_role(self, user_id: int, role: str) -> Any:
        """Assign a role (Django Group) to a user. Idempotent."""
        from django.contrib.auth.models import Group

        user = get_object_or_404(User, id=user_id)
        group = get_object_or_404(Group, name=role)
        user.groups.add(group)
        return user

    def remove_role(self, user_id: int, role: str) -> Any:
        """Remove a role (Django Group) from a user. Idempotent — no error if not assigned."""
        from django.contrib.auth.models import Group

        user = get_object_or_404(User, id=user_id)
        try:
            group = Group.objects.get(name=role)
            user.groups.remove(group)
        except Group.DoesNotExist:
            pass  # idempotent — removing a non-existent role is a no-op
        return user


class UserDeletionService:
    """Orchestrates the GDPR Article 17 (right to erasure) deletion cascade.

    Steps (executed in order, each wrapped in try/except so later steps
    always run even if earlier ones fail):
      1. Cancel Stripe subscription immediately.
      2. Delete Stripe customer object.
      3. Delete PostHog person record.
      4. Call user.delete() — Django ORM cascades all related tables.
    """

    def execute(self, user: Any) -> None:
        """Execute the full deletion cascade for the given user.

        Args:
            user: Django User instance to permanently delete.
        """
        from apps.billing.models import Customer
        from apps.billing.services import BillingService
        from apps.billing.utils import get_adapter
        from apps.core.observability import get_observability_adapter

        # Step 1: Cancel Stripe subscription immediately
        try:
            BillingService().cancel_subscription(user, cancel_at_period_end=False)
        except Exception as exc:
            logger.warning(
                "gdpr_deletion: cancel_subscription failed user_pk=%s error=%s",
                user.pk,
                exc,
            )

        # Step 2: Delete Stripe customer object
        try:
            stripe_customer_id = user.billing_customer.stripe_customer_id
            if stripe_customer_id:
                get_adapter().delete_customer(stripe_customer_id)
        except Customer.DoesNotExist:
            pass
        except Exception as exc:
            logger.warning(
                "gdpr_deletion: delete_customer failed user_pk=%s error=%s",
                user.pk,
                exc,
            )

        # Step 3: Delete PostHog person record
        try:
            get_observability_adapter().delete_person(str(user.pk))
        except Exception as exc:
            logger.warning(
                "gdpr_deletion: delete_person failed user_pk=%s error=%s",
                user.pk,
                exc,
            )

        # Step 4: Permanently delete the user — cascades all related tables
        user.delete()
        logger.info("gdpr_deletion: user_pk=%s permanently deleted", user.pk)


class AccountExportService:
    """Assembles a GDPR Article 20 (right to data portability) export package.

    Returns a dict with: profile, social_accounts, billing, (exported_at added by controller).
    Does NOT include stripe_customer_id, stripe_subscription_id, or stripe_payment_intent_id.
    """

    def export(self, user: Any) -> dict[str, Any]:
        """Assemble the export data dict for the given user.

        Args:
            user: Django User instance.

        Returns:
            Dict with profile, social_accounts, billing keys.
        """
        from apps.billing.models import Customer

        profile = {
            "email": user.email,
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        # Social accounts — only provider + uid (no tokens)
        try:
            from allauth.socialaccount.models import SocialAccount

            social_accounts = [
                {"provider": sa.provider, "uid": sa.uid}
                for sa in SocialAccount.objects.filter(user=user)
            ]
        except Exception:
            social_accounts = []

        # Billing — subscription and payment history (no raw Stripe IDs)
        try:
            customer = user.billing_customer
            try:
                sub = customer.subscription
                subscription_status = sub.status
                plan_id = sub.plan_id  # Subscription.plan_id added in Phase 23 (migration 0004)
            except Exception:
                subscription_status = None
                plan_id = None

            payments = [
                {
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "status": p.status,
                    "date": p.created_at.isoformat(),
                }
                for p in customer.payments.all()
            ]

            billing: dict[str, Any] = {
                "subscription_status": subscription_status,
                "plan_id": plan_id,
                "payments": payments,
            }
        except Customer.DoesNotExist:
            billing = {
                "subscription_status": None,
                "plan_id": None,
                "payments": [],
            }
        except Exception:
            billing = {
                "subscription_status": None,
                "plan_id": None,
                "payments": [],
            }

        return {
            "profile": profile,
            "social_accounts": social_accounts,
            "billing": billing,
        }
