"""
Tests for billing signals.
Covers: CUST-02 (Customer auto-created on User post_save)
"""

import pytest
from django.contrib.auth import get_user_model

# importorskip skips this entire file if the billing signal or models cannot be imported.
# Handles both:
# 1. Module not on disk (ImportError) — Wave 0, billing not yet installed
# 2. Module on disk but app not in INSTALLED_APPS (RuntimeError from Django metaclass)
try:
    pytest.importorskip("apps.billing.signals")
    billing_models = pytest.importorskip("apps.billing.models")
except RuntimeError as exc:
    pytest.skip(f"apps.billing not registered in INSTALLED_APPS: {exc}", allow_module_level=True)

Customer = billing_models.Customer

User = get_user_model()


@pytest.mark.req("BILL-01")
@pytest.mark.django_db
def test_customer_auto_created_on_user_creation():
    """CUST-02: Creating a User automatically creates a linked Customer record."""
    user = User.objects.create_user(
        username="signaltest",
        email="signaltest@example.com",
        password="testpass123",
    )
    assert Customer.objects.filter(user=user).exists(), (
        "Customer must be auto-created via post_save signal when User is created"
    )


@pytest.mark.req("BILL-01")
@pytest.mark.django_db
def test_customer_not_duplicated_on_user_save():
    """CUST-02: Saving an existing User does not create a second Customer."""
    user = User.objects.create_user(
        username="signaltest2",
        email="signaltest2@example.com",
        password="testpass123",
    )
    user.first_name = "Updated"
    user.save()
    count = Customer.objects.filter(user=user).count()
    assert count == 1, f"Expected 1 Customer, got {count} after User re-save"
