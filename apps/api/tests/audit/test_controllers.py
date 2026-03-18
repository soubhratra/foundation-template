"""Tests: GET /api/v1/org/{slug}/audit-log query API (AUDIT-02)."""

import pghistory
import pytest
from django.test import Client


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_audit_log_admin_200(org, org_admin):
    """GET /api/v1/org/{slug}/audit-log returns 200 for org admin."""
    client = Client()
    client.force_login(org_admin)
    response = client.get(f"/api/v1/org/{org.slug}/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "page_size" in data


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_audit_log_member_403(org, org_member):
    """GET /api/v1/org/{slug}/audit-log returns 403 for plain org member."""
    client = Client()
    client.force_login(org_member)
    response = client.get(f"/api/v1/org/{org.slug}/audit-log")
    assert response.status_code == 403


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_filter_actor_id(org, org_admin):
    """?actor_id= filter returns only entries for that actor."""
    from apps.audit.selectors import get_audit_log_page

    # Create an event with the org_admin as actor
    with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
        org.name = "Updated by admin"
        org.save()

    # Create an event with a different user (the owner is also member via fixture)
    items, _ = get_audit_log_page(
        org=org,
        actor_id=org_admin.pk,
    )
    assert len(items) > 0
    for item in items:
        assert item.actor_id == str(org_admin.pk)


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_filter_action(org, org_admin):
    """?action=org.updated returns only org update events."""
    from apps.audit.selectors import get_audit_log_page

    # Create an update event
    with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
        org.name = "Updated for filter test"
        org.save()

    items, _ = get_audit_log_page(org=org, action="org.updated")
    assert len(items) > 0
    for item in items:
        assert item.action == "org.updated"


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_cursor_pagination(org, org_admin):
    """Cursor pagination: next_cursor present; second page is non-overlapping."""
    from apps.audit.selectors import get_audit_log_page

    # Create multiple events to have enough rows for pagination
    with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
        for i in range(5):
            org.name = f"Update {i}"
            org.save()

    page1_items, next_cursor = get_audit_log_page(org=org, page_size=2)
    assert len(page1_items) == 2
    assert next_cursor is not None

    page2_items, _ = get_audit_log_page(org=org, page_size=2, cursor=next_cursor)
    page1_ids = {item.id for item in page1_items}
    page2_ids = {item.id for item in page2_items}
    assert len(page2_ids) > 0
    assert page1_ids.isdisjoint(page2_ids), "Pages must be non-overlapping"


@pytest.mark.req("AUDIT-03", "AKEY-01")
@pytest.mark.django_db(transaction=True)
def test_apikey_events_in_audit_log(org, org_admin):
    """APIKey create events appear in the org audit log (uses across(), not references())."""
    from apps.api_keys.models import APIKey
    from apps.audit.selectors import get_audit_log_page

    # Create APIKey event under org context
    with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
        raw_key, prefix, hashed = APIKey.generate_key()
        APIKey.objects.create(
            user=org_admin,
            name="Audit test key",
            prefix=prefix,
            key_hash=hashed,
            scopes=["read"],
        )

    items, _ = get_audit_log_page(org=org)
    actions = [item.action for item in items]
    assert "api_key.created" in actions, f"Expected api_key.created in {actions}"


@pytest.mark.req("AUDIT-03")
@pytest.mark.django_db(transaction=True)
def test_impersonator_not_exposed(org, org_admin):
    """AuditEntryOut response body does NOT contain an impersonator field."""
    # Create an event so there's something in the log
    with pghistory.context(user=org_admin.pk, org_id=str(org.id)):
        org.name = "Impersonator test"
        org.save()

    client = Client()
    client.force_login(org_admin)
    response = client.get(f"/api/v1/org/{org.slug}/audit-log")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert "impersonator" not in item, f"impersonator field leaked into response: {item}"
