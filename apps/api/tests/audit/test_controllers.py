"""Tests: GET /api/v1/org/{slug}/audit-log query API (AUDIT-02)."""

import pytest


@pytest.mark.django_db
def test_audit_log_admin_200(org, org_admin):
    """GET /api/v1/org/{slug}/audit-log returns 200 for org admin."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_audit_log_member_403(org, org_member):
    """GET /api/v1/org/{slug}/audit-log returns 403 for plain org member."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_filter_actor_id(org, org_admin):
    """?actor_id= filter returns only entries for that actor."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_filter_action(org, org_admin):
    """?action=org.updated returns only org update events."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_cursor_pagination(org, org_admin):
    """Cursor pagination: next_cursor present; second page is non-overlapping."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_apikey_events_in_audit_log(org, org_admin, api_key_instance):
    """APIKey create events appear in the org audit log (uses across(), not references())."""
    raise AssertionError("not implemented")


@pytest.mark.django_db
def test_impersonator_not_exposed(org, org_admin):
    """AuditEntryOut response body does NOT contain an impersonator field."""
    raise AssertionError("not implemented")
