"""ADMIN-01 smoke tests: all ModelAdmin registrations inherit UnfoldModelAdmin.

Tests here will fail (ImportError or AttributeError) until Plan 03 creates
the admin.py files for each domain.
"""

import pytest


@pytest.mark.req("ADMIN-01")
@pytest.mark.req("DOCS-03")
@pytest.mark.django_db
def test_user_admin_inherits_unfold():
    """accounts.UserAdmin must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.accounts.admin import UserAdmin

    assert issubclass(UserAdmin, UnfoldModelAdmin), (
        "UserAdmin must inherit UnfoldModelAdmin (not django.contrib.admin.ModelAdmin)"
    )


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_billing_admins_inherit_unfold():
    """All billing ModelAdmins must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.billing.admin import (
        CustomerAdmin,
        PaymentAdmin,
        PlanProviderMappingAdmin,
        ProcessedWebhookEventAdmin,
        SubscriptionAdmin,
    )

    for cls in [
        CustomerAdmin,
        SubscriptionAdmin,
        PaymentAdmin,
        ProcessedWebhookEventAdmin,
        PlanProviderMappingAdmin,
    ]:
        assert issubclass(cls, UnfoldModelAdmin), f"{cls.__name__} must inherit UnfoldModelAdmin"


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_org_admins_inherit_unfold():
    """All orgs ModelAdmins must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.orgs.admin import MembershipAdmin, OrganizationAdmin

    for cls in [OrganizationAdmin, MembershipAdmin]:
        assert issubclass(cls, UnfoldModelAdmin), f"{cls.__name__} must inherit UnfoldModelAdmin"


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_api_key_admin_inherits_unfold():
    """api_keys.APIKeyAdmin must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.api_keys.admin import APIKeyAdmin

    assert issubclass(APIKeyAdmin, UnfoldModelAdmin)


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_webhook_admins_inherit_unfold():
    """webhooks ModelAdmins must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.webhooks.admin import WebhookDeliveryAdmin, WebhookEndpointAdmin

    for cls in [WebhookEndpointAdmin, WebhookDeliveryAdmin]:
        assert issubclass(cls, UnfoldModelAdmin), f"{cls.__name__} must inherit UnfoldModelAdmin"


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_impersonation_event_admin_inherits_unfold():
    """audit.ImpersonationEventAdmin must inherit from unfold.admin.ModelAdmin."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.audit.admin import ImpersonationEventAdmin

    assert issubclass(ImpersonationEventAdmin, UnfoldModelAdmin)


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_impersonation_event_admin_is_readonly():
    """ImpersonationEventAdmin must block all add/change/delete permissions."""
    from django.contrib.admin.sites import AdminSite

    from apps.audit.admin import ImpersonationEventAdmin
    from apps.audit.models import ImpersonationEvent

    site = AdminSite()
    admin_instance = ImpersonationEventAdmin(ImpersonationEvent, site)
    mock_request = type("Request", (), {"user": None})()
    assert admin_instance.has_add_permission(mock_request) is False
    assert admin_instance.has_change_permission(mock_request) is False
    assert admin_instance.has_delete_permission(mock_request) is False


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_org_customer_admin_inherits_unfold():
    """orgs.OrgCustomerAdmin must inherit from unfold.admin.ModelAdmin (BILL-01)."""
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    from apps.orgs.admin import OrgCustomerAdmin

    assert issubclass(OrgCustomerAdmin, UnfoldModelAdmin), (
        "OrgCustomerAdmin must inherit UnfoldModelAdmin"
    )


@pytest.mark.req("ADMIN-01")
@pytest.mark.django_db
def test_org_customer_admin_list_display():
    """OrgCustomerAdmin must display org, stripe_customer_id, created_at columns (BILL-01)."""
    from django.contrib.admin.sites import AdminSite

    from apps.orgs.admin import OrgCustomerAdmin
    from apps.orgs.models import OrgCustomer

    site = AdminSite()
    admin_instance = OrgCustomerAdmin(OrgCustomer, site)
    assert admin_instance.list_display == ("org", "stripe_customer_id", "created_at")
