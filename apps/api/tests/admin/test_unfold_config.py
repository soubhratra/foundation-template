"""ADMIN-01 config tests: UNFOLD settings sidebar is correctly structured.

Tests will fail until Plan 02 adds the UNFOLD dict to base.py.
"""

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_unfold_settings_exist():
    """UNFOLD settings dict must be present in Django settings."""
    assert hasattr(settings, "UNFOLD"), "settings.UNFOLD not configured"
    assert isinstance(settings.UNFOLD, dict)


@pytest.mark.django_db
def test_unfold_sidebar_has_b2b_section():
    """UNFOLD sidebar must contain a B2B section with required model links."""
    sidebar = settings.UNFOLD.get("SIDEBAR", {})
    navigation = sidebar.get("navigation", [])
    b2b_sections = [s for s in navigation if s.get("title") == "B2B"]
    assert len(b2b_sections) == 1, "Expected exactly one B2B section in sidebar"
    b2b_items = b2b_sections[0].get("items", [])
    item_titles = {item["title"] for item in b2b_items}
    required = {"Organizations", "Memberships", "API Keys", "Webhooks", "Audit Log"}
    assert required.issubset(item_titles), (
        f"B2B section missing items. Found: {item_titles}, required: {required}"
    )


@pytest.mark.django_db
def test_unfold_sidebar_has_users_section():
    """UNFOLD sidebar must contain a Users & Auth section."""
    sidebar = settings.UNFOLD.get("SIDEBAR", {})
    navigation = sidebar.get("navigation", [])
    titles = [s.get("title") for s in navigation]
    assert "Users & Auth" in titles, f"Users & Auth section missing. Found: {titles}"


@pytest.mark.django_db
def test_unfold_sidebar_has_billing_section():
    """UNFOLD sidebar must contain a Billing section."""
    sidebar = settings.UNFOLD.get("SIDEBAR", {})
    navigation = sidebar.get("navigation", [])
    titles = [s.get("title") for s in navigation]
    assert "Billing" in titles, f"Billing section missing. Found: {titles}"


@pytest.mark.django_db
def test_unfold_sidebar_has_system_section():
    """UNFOLD sidebar must contain a System section."""
    sidebar = settings.UNFOLD.get("SIDEBAR", {})
    navigation = sidebar.get("navigation", [])
    titles = [s.get("title") for s in navigation]
    assert "System" in titles, f"System section missing. Found: {titles}"


@pytest.mark.django_db
def test_unfold_sidebar_has_org_billing_link():
    """UNFOLD B2B section must include an Org Billing sidebar item (BILL-01)."""
    sidebar = settings.UNFOLD.get("SIDEBAR", {})
    navigation = sidebar.get("navigation", [])
    b2b_sections = [s for s in navigation if s.get("title") == "B2B"]
    assert len(b2b_sections) == 1, "Expected exactly one B2B section"
    b2b_items = b2b_sections[0].get("items", [])
    item_titles = {item["title"] for item in b2b_items}
    assert "Org Billing" in item_titles, f"B2B section missing 'Org Billing'. Found: {item_titles}"
