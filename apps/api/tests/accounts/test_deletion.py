"""GDPR-01: RED test stubs for account hard-delete endpoint and cascade task.

Tests the DELETE /api/v1/account/ endpoint and the delete_user_account Celery task.
Both the endpoint and task do not exist yet — every test fails RED when the
import is attempted inside the test body.

Cascade order (per 21-CONTEXT.md):
  1. BillingService.cancel_subscription() — cancel active Stripe sub immediately
  2. PaymentAdapter.delete_customer() — delete Stripe customer object
  3. ObservabilityAdapter.delete_person() — delete PostHog person record
  4. user.delete() — Django ORM cascade for all related tables
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def test_user(db):
    """Create a test user with a known password for deletion tests."""
    return User.objects.create_user(
        username="gdpr_test_user",
        email="gdpr@example.com",
        password="correct-password-123",  # pragma: allowlist secret
        first_name="GDPR",
        last_name="Tester",
    )


# ---------------------------------------------------------------------------
# Endpoint tests — DELETE /api/v1/account/
# ---------------------------------------------------------------------------


class TestDeleteAccountEndpoint:
    """GDPR-01 endpoint tests: DELETE /api/v1/account/"""

    @pytest.mark.req("GDPR-01", "GDPR-03")
    def test_delete_account_returns_202(self, db, test_user) -> None:
        """Authenticated DELETE with correct password returns HTTP 202 and confirmation message."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with AccountController "
                "that includes DELETE /api/v1/account/ returning 202"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(test_user)
        response = client.delete("/", json={"password": "correct-password-123"})

        assert response.status_code == 202, (
            f"Expected 202, got {response.status_code}. "
            "DELETE /api/v1/account/ must return 202 (Accepted) when password is correct."
        )
        data = response.json()
        assert "message" in data, "Response must include a 'message' key"
        assert data["message"] == "Account deletion initiated.", (
            f"Expected 'Account deletion initiated.', got '{data['message']}'"
        )

    @pytest.mark.req("GDPR-01")
    def test_delete_wrong_password_returns_400(self, db, test_user) -> None:
        """Authenticated DELETE with wrong password returns HTTP 400."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with DELETE /api/v1/account/"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        client.force_login(test_user)
        response = client.delete("/", json={"password": "WRONG-password"})

        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. "
            "DELETE /api/v1/account/ must return 400 when password is incorrect."
        )

    @pytest.mark.req("GDPR-01")
    def test_delete_unauthenticated_returns_401(self, db) -> None:
        """Unauthenticated DELETE /api/v1/account/ returns HTTP 401."""
        try:
            from apps.accounts.controllers import AccountController
        except ImportError:
            pytest.fail(
                "AccountController not yet implemented — "
                "create apps/accounts/controllers.py with DELETE /api/v1/account/"
            )

        from ninja.testing import TestClient

        client = TestClient(AccountController)
        # No force_login — unauthenticated request
        response = client.delete("/", json={"password": "any-password"})

        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}. "
            "DELETE /api/v1/account/ must return 401 for unauthenticated requests."
        )


# ---------------------------------------------------------------------------
# Task cascade tests — delete_user_account Celery task
# ---------------------------------------------------------------------------


class TestDeletionTaskCascade:
    """GDPR-01 task tests: delete_user_account.run(user_pk) cascade verification."""

    @pytest.mark.req("GDPR-01")
    def test_deletion_task_cascade(self, db, test_user) -> None:
        """delete_user_account.run(user.pk) calls cancel_subscription, delete_customer,
        delete_person, and user.delete() in that exact order."""
        try:
            from apps.accounts.tasks import delete_user_account
        except ImportError:
            pytest.fail(
                "delete_user_account task not yet implemented — "
                "create apps/accounts/tasks.py with delete_user_account Celery task"
            )

        with (
            patch("apps.accounts.tasks.BillingService") as MockBillingService,
            patch("apps.accounts.tasks.PaymentAdapter") as MockPaymentAdapter,
            patch("apps.accounts.tasks.ObservabilityAdapter") as MockObservabilityAdapter,
        ):
            mock_billing_instance = MagicMock()
            MockBillingService.return_value = mock_billing_instance

            mock_adapter_instance = MagicMock()
            MockPaymentAdapter.return_value = mock_adapter_instance

            mock_obs_instance = MagicMock()
            MockObservabilityAdapter.return_value = mock_obs_instance

            # Track call order across all mocks
            manager = MagicMock()
            manager.attach_mock(mock_billing_instance.cancel_subscription, "cancel_subscription")
            manager.attach_mock(mock_adapter_instance.delete_customer, "delete_customer")
            manager.attach_mock(mock_obs_instance.delete_person, "delete_person")

            delete_user_account.run(test_user.pk)

        # Verify cascade order
        call_names = [c[0] for c in manager.mock_calls]
        assert "cancel_subscription" in call_names, (
            "BillingService.cancel_subscription() must be called"
        )
        assert "delete_customer" in call_names, "PaymentAdapter.delete_customer() must be called"
        assert "delete_person" in call_names, "ObservabilityAdapter.delete_person() must be called"

        cancel_idx = call_names.index("cancel_subscription")
        delete_customer_idx = call_names.index("delete_customer")
        delete_person_idx = call_names.index("delete_person")

        assert cancel_idx < delete_customer_idx, (
            "cancel_subscription must be called before delete_customer"
        )
        assert delete_customer_idx < delete_person_idx, (
            "delete_customer must be called before delete_person"
        )

        # Verify user is deleted (can no longer be retrieved)
        user_pk = test_user.pk
        assert not User.objects.filter(pk=user_pk).exists(), (
            "user.delete() must be called — user should not exist after task runs"
        )

    @pytest.mark.req("GDPR-01")
    def test_deletion_task_idempotent(self, db) -> None:
        """delete_user_account.run(non_existent_user_pk) returns None without raising."""
        try:
            from apps.accounts.tasks import delete_user_account
        except ImportError:
            pytest.fail(
                "delete_user_account task not yet implemented — create apps/accounts/tasks.py"
            )

        # Use a PK that cannot exist
        non_existent_pk = 999_999_999

        try:
            result = delete_user_account.run(non_existent_pk)
        except Exception as exc:
            pytest.fail(
                f"delete_user_account.run() raised {type(exc).__name__} for non-existent user PK. "
                "Task must be idempotent — return None without raising."
            )

        assert result is None, (
            f"delete_user_account.run() must return None for non-existent user, got {result!r}"
        )

    @pytest.mark.req("GDPR-01")
    def test_deletion_task_continues_on_stripe_failure(self, db, test_user) -> None:
        """If BillingService.cancel_subscription() raises, the task still calls user.delete()."""
        try:
            from apps.accounts.tasks import delete_user_account
        except ImportError:
            pytest.fail(
                "delete_user_account task not yet implemented — create apps/accounts/tasks.py"
            )

        with (
            patch("apps.accounts.tasks.BillingService") as MockBillingService,
            patch("apps.accounts.tasks.ObservabilityAdapter") as MockObservabilityAdapter,
        ):
            mock_billing_instance = MagicMock()
            mock_billing_instance.cancel_subscription.side_effect = Exception("Stripe API timeout")
            MockBillingService.return_value = mock_billing_instance

            mock_obs_instance = MagicMock()
            MockObservabilityAdapter.return_value = mock_obs_instance

            # Should not raise even though cancel_subscription raises
            delete_user_account.run(test_user.pk)

        # User must still be deleted despite Stripe failure
        assert not User.objects.filter(pk=test_user.pk).exists(), (
            "user.delete() must be called even when BillingService.cancel_subscription() raises. "
            "Stripe failure must not abort the deletion cascade."
        )
