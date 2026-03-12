"""Feature entitlement checks backed by BILLING_PLANS settings and Redis cache."""

import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache  # always use this — tests override to LocMemCache

logger = logging.getLogger(__name__)

ENTITLEMENT_CACHE_TTL = 300  # 5 minutes


def _has_feature(user: Any, key: str, plan_override: str | None = None) -> bool:
    """Return True if user's billing plan includes the named feature flag.

    Args:
        user: Django user instance.
        key: Feature flag key to check (e.g. "api_access").
        plan_override: Internal plan_id to use instead of DB lookup — for test convenience only.

    Returns:
        True if the feature is enabled for the user's plan; False otherwise.
        Missing keys return False (deny by default).
    """
    if plan_override is not None:
        flags = _flags_for_plan(plan_override)
        return flags.get(key, False)

    cache_key = f"entitlements:{user.pk}"
    cached = cache.get(cache_key)

    if cached is None:
        plan_id = _resolve_plan_id(user)
        cached = _flags_for_plan(plan_id)
        cache.set(cache_key, cached, timeout=ENTITLEMENT_CACHE_TTL)

    return cached.get(key, False)


def _resolve_plan_id(user: Any) -> str:
    """Return the internal plan_id for the user, defaulting to 'free'.

    Falls back to free plan if:
    - User has no Customer record
    - Customer has no Subscription record
    - Subscription.plan_id is None or empty
    - plan_id is not in BILLING_PLANS (logs WARNING)
    """
    try:
        plan_id = user.billing_customer.subscription.plan_id
    except Exception:
        return "free"

    if not plan_id:
        return "free"

    billing_plans = settings.BILLING_PLANS
    if plan_id not in billing_plans:
        logger.warning(
            "entitlements: unknown plan_id=%r for user=%s — falling back to free",
            plan_id,
            user.pk,
        )
        return "free"

    return plan_id


def _flags_for_plan(plan_id: str) -> dict:
    """Return the feature_flags dict for the given plan_id.

    Returns empty dict if plan not found or has no feature_flags key.
    """
    billing_plans = settings.BILLING_PLANS
    plan = billing_plans.get(plan_id, billing_plans.get("free", {}))
    return plan.get("feature_flags", {})
