"""GDPR-02: RED test stubs for data export endpoint.

Tests the GET /api/v1/account/export endpoint which returns a user's personal
data as a JSON download (GDPR Article 20 / CCPA Right to Know).

The AccountController does not yet exist — every test fails RED when the
import is attempted inside the test body.

Export schema (per 21-CONTEXT.md):
  - profile: email, first_name, last_name, date_joined, last_login
  - social_accounts: list of connected providers with provider UID
  - billing: subscription_status, plan_id, payment history (no raw card data)
  - exported_at: ISO 8601 timestamp
"""

from __future__ import annotations

import json

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def export_user(db):
    """Create a test user for export tests."""
    return User.objects.create_user(
        username="export_test_user",
        email="export@example.com",
        password="export-test-pass",  # pragma: allowlist secret
        first_name="Export",
        last_name="Tester",
    )


@pytest.fixture
def export_user_with_billing(db, export_user):
    """Return a test user whose billing Customer row has a Stripe customer ID.

    The billing signal auto-creates a Customer on user save, so we update the
    existing row rather than creating a duplicate (which would violate the
    OneToOne constraint on billing_customer_user_id).
    """
    from apps.billing.models import Customer

    customer, _ = Customer.objects.get_or_create(user=export_user)
    customer.stripe_customer_id = "cus_test123"
    customer.save(update_fields=["stripe_customer_id"])
    return export_user


# ---------------------------------------------------------------------------
# Endpoint tests — GET /api/v1/account/export
# ---------------------------------------------------------------------------


class TestExportEndpoint:
    """GDPR-02 endpoint tests: GET /api/v1/account/export"""

    @pytest.mark.req("GDPR-02")
    def test_export_returns_200(self, db, export_user) -> None:
        """Authenticated GET /api/v1/account/export returns HTTP 200."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with AccountController "
                "that includes GET /api/v1/account/export returning 200"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user)
        response = client.get("/export")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "GET /api/v1/account/export must return 200 for authenticated users."
        )

    @pytest.mark.req("GDPR-02")
    def test_export_schema(self, db, export_user) -> None:
        """Response JSON has top-level keys: profile, social_accounts, billing, exported_at."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with AccountController "
                "including GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user)
        response = client.get("/export")

        data = response.json()
        required_keys = {"profile", "social_accounts", "billing", "exported_at"}
        missing = required_keys - set(data.keys())
        assert not missing, (
            f"Export response missing required top-level keys: {missing}. Got: {list(data.keys())}"
        )

    @pytest.mark.req("GDPR-02")
    def test_export_profile_fields(self, db, export_user) -> None:
        """Profile section contains email, first_name, last_name, date_joined, last_login."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user)
        response = client.get("/export")

        profile = response.json().get("profile", {})
        required_fields = {"email", "first_name", "last_name", "date_joined", "last_login"}
        missing = required_fields - set(profile.keys())
        assert not missing, (
            f"Profile section missing required fields: {missing}. Got: {list(profile.keys())}"
        )

    @pytest.mark.req("GDPR-02")
    def test_export_download_header(self, db, export_user) -> None:
        """Response has Content-Disposition header with 'attachment' and 'my-data.json'."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user)
        response = client.get("/export")

        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition, (
            f"Content-Disposition must include 'attachment'. Got: '{content_disposition}'"
        )
        assert "my-data.json" in content_disposition, (
            f"Content-Disposition must include 'my-data.json'. Got: '{content_disposition}'"
        )

    @pytest.mark.req("GDPR-02")
    def test_export_billing_no_customer(self, db, export_user) -> None:
        """For user with no billing Customer row, billing fields are all null/empty."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user)
        response = client.get("/export")

        billing = response.json().get("billing", {})
        assert billing.get("subscription_status") is None, (
            "billing.subscription_status must be None for user with no Customer row. "
            f"Got: {billing.get('subscription_status')!r}"
        )
        assert billing.get("plan_id") is None, (
            "billing.plan_id must be None for user with no Customer row. "
            f"Got: {billing.get('plan_id')!r}"
        )
        assert billing.get("payments") == [], (
            "billing.payments must be [] for user with no Customer row. "
            f"Got: {billing.get('payments')!r}"
        )

    @pytest.mark.req("GDPR-02")
    def test_export_unauthenticated_returns_401(self, db) -> None:
        """Unauthenticated GET /api/v1/account/export returns HTTP 401."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        # No force_login — unauthenticated request
        response = client.get("/export")

        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. "
            "GET /api/v1/account/export must return 401 for unauthenticated requests."
        )

    @pytest.mark.req("GDPR-02")
    def test_export_excludes_stripe_ids(self, db, export_user_with_billing) -> None:
        """Response JSON must not contain Stripe customer/subscription IDs (cus_/sub_ prefixes)."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with GET /api/v1/account/export"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(export_user_with_billing)
        response = client.get("/export")

        response_text = json.dumps(response.json())
        assert "cus_" not in response_text, (
            "Export response must NOT contain Stripe customer IDs (cus_ prefix). "
            "stripe_customer_id must be excluded from the export payload."
        )
        assert "sub_" not in response_text, (
            "Export response must NOT contain Stripe subscription IDs (sub_ prefix). "
            "stripe_subscription_id must be excluded from the export payload."
        )

    @pytest.mark.req("GDPR-02")
    def test_export_billing_plan_id_round_trip(self, db, export_user_with_plan) -> None:
        """billing.plan_id matches the value stored on Subscription.plan_id (GDPR-02)."""
        from ninja.testing import TestClient

        from apps.accounts.controllers import AccountController

        client = TestClient(AccountController)
        client.force_login(export_user_with_plan)
        response = client.get("/export")

        billing = response.json().get("billing", {})
        assert billing.get("plan_id") == "pro", (
            f"Expected billing.plan_id='pro', got {billing.get('plan_id')!r}. "
            "AccountExportService.export() must read sub.plan_id from the ORM, "
            "not return hardcoded None."
        )


@pytest.fixture
def export_user_with_plan(db, export_user):
    """User with a Customer + Subscription with an explicit plan_id."""
    from apps.billing.models import Customer, Subscription, SubscriptionStatus

    customer, _ = Customer.objects.get_or_create(user=export_user)
    Subscription.objects.update_or_create(
        customer=customer,
        defaults={
            "plan_id": "pro",
            "status": SubscriptionStatus.ACTIVE,
        },
    )
    return export_user
