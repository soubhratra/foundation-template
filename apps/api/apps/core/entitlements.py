"""Public feature entitlement API.

This module is always present regardless of whether the billing module is installed.
When billing is absent (--without billing scaffolder flag), has_feature() returns True
for every key — no features are gated when there is no billing system.

Usage:
    from apps.core.entitlements import has_feature

    if not has_feature(request.user, "advanced_analytics"):
        raise PermissionDenied("Advanced analytics not available on your plan.")
"""


def has_feature(user, key: str) -> bool:
    """Return True if user's plan includes the named feature flag.

    When billing module is not installed, returns True for every key — features
    are fully accessible and no import errors occur.

    Args:
        user: Django user instance.
        key: Feature flag key to check (e.g. "api_access").

    Returns:
        True if the feature is enabled for the user's plan, or if billing is absent.
        False if the feature is explicitly disabled for the user's plan.
    """
    try:
        from apps.billing.entitlements import _has_feature

        return _has_feature(user, key)
    except ImportError:
        return True


def has_org_feature(user, org, key: str) -> bool:
    """Return True if the org's plan (or the user's personal plan) includes the named feature.

    Checks org-level entitlements first. Falls back to the user's personal plan when the
    org has no active subscription. Returns True when billing module is not installed.

    Cache key: ``entitlements:org:{org.pk}:{user.pk}`` — kept separate from the personal
    key ``entitlements:{user.pk}`` so org and personal caches can be invalidated independently.

    Args:
        user: Django user instance (used for personal-plan fallback).
        org: Organization instance whose billing plan should be checked first.
        key: Feature flag key to check (e.g. "advanced_analytics").

    Returns:
        True if the feature is enabled on the applicable plan, or if billing is absent.
        False if the feature is explicitly disabled for the applicable plan.
    """
    try:
        from django.core.cache import cache

        from apps.billing.entitlements import _flags_for_plan
        from apps.orgs.services import _resolve_org_plan_id

        cache_key = f"entitlements:org:{org.pk}:{user.pk}"
        cached = cache.get(cache_key)
        if cached is None:
            org_plan_id = _resolve_org_plan_id(org)
            if org_plan_id is not None:
                cached = _flags_for_plan(org_plan_id)
            else:
                from apps.billing.entitlements import _resolve_plan_id

                personal_plan_id = _resolve_plan_id(user)
                cached = _flags_for_plan(personal_plan_id)
            from django.conf import settings

            ENTITLEMENT_CACHE_TTL = getattr(settings, "ENTITLEMENT_CACHE_TTL", 300)
            cache.set(cache_key, cached, timeout=ENTITLEMENT_CACHE_TTL)
        return cached.get(key, False)
    except ImportError:
        return True
