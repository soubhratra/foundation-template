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
