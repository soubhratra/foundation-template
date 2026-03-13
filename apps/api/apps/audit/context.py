"""Audit context manager for pghistory.

Provides audit_context() which wraps pghistory.context() when pghistory is
installed, and degrades to a no-op context manager when pghistory is absent
(e.g. in non-B2B deployments that exclude it from INSTALLED_APPS).
"""

from contextlib import contextmanager, nullcontext


@contextmanager
def audit_context(user_id=None, org_id=None):
    """Context manager that attaches user_id and org_id to pghistory events.

    When pghistory is installed, all ORM mutations inside this context will
    have user and org_id populated in the pghistory.Context row.

    When pghistory is not in INSTALLED_APPS (non-B2B mode), this is a no-op.
    """
    from django.apps import apps as django_apps

    if not django_apps.is_installed("pghistory"):
        with nullcontext():
            yield
        return
    import pghistory

    with pghistory.context(
        user=user_id,
        org_id=str(org_id) if org_id is not None else None,
    ):
        yield
