"""Tests: pghistory triggers fire on tracked B2B model mutations (AUDIT-01)."""

import pytest


@pytest.mark.req("AUDIT-01")
@pytest.mark.django_db(transaction=True)
def test_org_insert_event(org):
    """Creating an Organization writes an org.created event row."""
    from apps.orgs.models import OrganizationEvent

    # org fixture already created one — verify the insert trigger fired
    assert OrganizationEvent.objects.filter(
        pgh_obj=org,
        pgh_label="org.created",
    ).exists(), "Expected org.created event row after Organization creation"


@pytest.mark.req("AUDIT-01")
@pytest.mark.django_db(transaction=True)
def test_org_delete_event(org):
    """Deleting an Organization writes an org.deleted event row."""
    from apps.orgs.models import OrganizationEvent

    org_id = org.pk
    org.delete()

    assert OrganizationEvent.objects.filter(
        pgh_obj_id=org_id,
        pgh_label="org.deleted",
    ).exists(), "Expected org.deleted event row after Organization deletion"


@pytest.mark.req("AUDIT-01")
@pytest.mark.django_db(transaction=True)
def test_membership_update_event(org, org_member):
    """Updating Membership role writes a membership.updated event row."""
    from apps.orgs.models import Membership, MembershipEvent

    membership = Membership.objects.get(org=org, user=org_member)
    membership.role = Membership.Role.ADMIN
    membership.save()

    assert MembershipEvent.objects.filter(
        pgh_obj=membership,
        pgh_label="membership.updated",
    ).exists(), "Expected membership.updated event row after role change"


@pytest.mark.req("AUDIT-01")
@pytest.mark.django_db(transaction=True)
def test_apikey_insert_event(api_key_instance):
    """Creating an APIKey writes an api_key.created event row."""
    from apps.api_keys.models import APIKeyEvent

    assert APIKeyEvent.objects.filter(
        pgh_obj=api_key_instance,
        pgh_label="api_key.created",
    ).exists(), "Expected api_key.created event row after APIKey creation"


@pytest.mark.req("AUDIT-01")
@pytest.mark.django_db(transaction=True)
def test_webhook_endpoint_insert_event(webhook_endpoint_instance):
    """Creating a WebhookEndpoint writes a webhook_endpoint.created event row."""
    from apps.webhooks.models import WebhookEndpointEvent

    assert WebhookEndpointEvent.objects.filter(
        pgh_obj=webhook_endpoint_instance,
        pgh_label="webhook_endpoint.created",
    ).exists(), "Expected webhook_endpoint.created event row after WebhookEndpoint creation"
