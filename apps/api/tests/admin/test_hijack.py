"""ADMIN-02 tests: impersonation permissions, signal handlers, middleware context.

These tests will fail (ImportError or AssertionError) until Plans 02 and 03
create ImpersonationEvent, wire hijack signals, and configure HIJACK_PERMISSION_CHECK.
"""

import pytest
from django.test import RequestFactory

# ---------------------------------------------------------------------------
# Permission check tests
# ---------------------------------------------------------------------------


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_staff_can_hijack_regular_user(staff_user, regular_user):
    """Custom permission function must allow staff to impersonate regular users."""
    from apps.accounts.permissions import staff_can_hijack_regular_users

    assert staff_can_hijack_regular_users(hijacker=staff_user, hijacked=regular_user) is True


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_cannot_hijack_staff(staff_user):
    """Custom permission function must deny impersonation of staff accounts."""
    from apps.accounts.permissions import staff_can_hijack_regular_users

    other_staff = type(staff_user).objects.create_user(
        username="staff2@test.com",
        email="staff2@test.com",
        password="testpass",  # pragma: allowlist secret
        is_staff=True,
    )
    assert staff_can_hijack_regular_users(hijacker=staff_user, hijacked=other_staff) is False


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_cannot_hijack_superuser(staff_user, superuser):
    """Custom permission function must deny impersonation of superuser accounts."""
    from apps.accounts.permissions import staff_can_hijack_regular_users

    assert staff_can_hijack_regular_users(hijacker=staff_user, hijacked=superuser) is False


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_cannot_hijack_inactive_user(staff_user, regular_user):
    """Custom permission function must deny impersonation of inactive accounts."""
    from apps.accounts.permissions import staff_can_hijack_regular_users

    regular_user.is_active = False
    regular_user.save()
    assert staff_can_hijack_regular_users(hijacker=staff_user, hijacked=regular_user) is False


# ---------------------------------------------------------------------------
# Signal handler tests: ImpersonationEvent model
# ---------------------------------------------------------------------------


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_signal_start_writes_event(staff_user, regular_user):
    """hijack_started signal must create an ImpersonationEvent with action='start'."""
    from hijack import signals as hijack_signals

    from apps.audit.models import ImpersonationEvent

    initial_count = ImpersonationEvent.objects.count()

    # Simulate the signal firing
    hijack_signals.hijack_started.send(
        sender=None,
        hijacker=staff_user,
        hijacked=regular_user,
        request=None,
    )

    assert ImpersonationEvent.objects.count() == initial_count + 1
    event = ImpersonationEvent.objects.latest("timestamp")
    assert event.action == "start"
    assert event.hijacker_id == staff_user.pk
    assert event.hijacked_id == regular_user.pk


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_signal_end_writes_event(staff_user, regular_user):
    """hijack_ended signal must create an ImpersonationEvent with action='end'."""
    from hijack import signals as hijack_signals

    from apps.audit.models import ImpersonationEvent

    initial_count = ImpersonationEvent.objects.count()

    hijack_signals.hijack_ended.send(
        sender=None,
        hijacker=staff_user,
        hijacked=regular_user,
        request=None,
    )

    assert ImpersonationEvent.objects.count() == initial_count + 1
    event = ImpersonationEvent.objects.latest("timestamp")
    assert event.action == "end"
    assert event.hijacker_id == staff_user.pk
    assert event.hijacked_id == regular_user.pk


# ---------------------------------------------------------------------------
# Middleware context injection test
# ---------------------------------------------------------------------------


@pytest.mark.req("ADMIN-02")
@pytest.mark.django_db
def test_impersonator_context_injected_during_hijack(staff_user, regular_user):
    """AuditContextMiddleware must add impersonator_id to context when hijack_history present."""
    factory = RequestFactory()
    request = factory.get("/api/some-path/")
    request.user = regular_user
    # Simulate hijack_history: list of original user PKs
    request.hijack_history = [staff_user.pk]

    from apps.audit.middleware import AuditContextMiddleware

    middleware = AuditContextMiddleware(get_response=lambda r: None)
    ctx = middleware.get_context(request)

    assert "impersonator_id" in ctx, "impersonator_id missing from context during hijack session"
    assert ctx["impersonator_id"] == staff_user.pk
