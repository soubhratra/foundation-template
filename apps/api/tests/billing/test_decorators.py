"""
Unit tests for apps.billing.decorators.require_active_subscription.

Test pattern:
  - Build a minimal Django view decorated with @require_active_subscription.
  - Use RequestFactory to produce a GET request with request.user set.
  - Assert 200 for passing cases; assert PermissionDenied raised for failing cases.
"""

import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from apps.billing.decorators import require_active_subscription

# ---------------------------------------------------------------------------
# Minimal decorated view used by all tests
# ---------------------------------------------------------------------------


@require_active_subscription
def _protected_view(request):
    return HttpResponse("ok", status=200)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_request(user):
    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    return request


# ---------------------------------------------------------------------------
# Passing cases
# ---------------------------------------------------------------------------


def test_active_user_passes(db, user, active_subscription):
    """User with ACTIVE subscription must reach the view (HTTP 200)."""
    response = _protected_view(_make_request(user))
    assert response.status_code == 200


def test_trialing_user_passes(db, user, trialing_subscription):
    """User with TRIALING subscription must reach the view (HTTP 200)."""
    response = _protected_view(_make_request(user))
    assert response.status_code == 200


def test_cancel_at_period_end_passes(db, user, cancel_at_period_end_subscription):
    """User with ACTIVE + cancel_at_period_end=True is paid through the period — must pass."""
    response = _protected_view(_make_request(user))
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Blocking cases — all must raise PermissionDenied
# ---------------------------------------------------------------------------


def test_past_due_user_blocked(db, user, past_due_subscription):
    """User with PAST_DUE subscription must be blocked (PermissionDenied)."""
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(user))


def test_unpaid_user_blocked(db, user, unpaid_subscription):
    """User with UNPAID subscription must be blocked (PermissionDenied)."""
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(user))


def test_canceled_user_blocked(db, user, canceled_subscription):
    """User with CANCELED subscription must be blocked (PermissionDenied)."""
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(user))


def test_incomplete_user_blocked(db, user, incomplete_subscription):
    """User with INCOMPLETE subscription must be blocked (PermissionDenied)."""
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(user))


def test_no_customer_blocked(db, user):
    """User with no Customer record at all must be blocked (PermissionDenied)."""
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(user))


def test_no_subscription_blocked(db, customer):
    """Customer exists but has no Subscription record — must be blocked (PermissionDenied)."""
    # customer fixture creates the Customer but no Subscription.
    with pytest.raises(PermissionDenied):
        _protected_view(_make_request(customer.user))
