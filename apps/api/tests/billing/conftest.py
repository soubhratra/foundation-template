import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """A basic authenticated User instance."""
    return User.objects.create_user(
        username="billingtest",
        email="billingtest@example.com",
        password="testpass123",
    )


@pytest.fixture
def customer(user):
    """A Customer linked to the test user.

    Uses importorskip so this fixture is skipped if the billing module
    is not yet installed — Wave 1 enables it.
    """
    billing_models = pytest.importorskip("apps.billing.models")
    customer, _ = billing_models.Customer.objects.get_or_create(user=user)
    return customer
