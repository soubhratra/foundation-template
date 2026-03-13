"""Fixtures for admin backoffice tests."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture
def staff_user(db):
    user = User.objects.create_user(
        username="staff@test.com",
        email="staff@test.com",
        password="testpass123",  # pragma: allowlist secret
        is_staff=True,
    )
    return user


@pytest.fixture
def regular_user(db):
    user = User.objects.create_user(
        username="regular@test.com",
        email="regular@test.com",
        password="testpass123",  # pragma: allowlist secret
        is_staff=False,
        is_superuser=False,
    )
    return user


@pytest.fixture
def superuser(db):
    user = User.objects.create_superuser(
        username="super@test.com",
        email="super@test.com",
        password="testpass123",  # pragma: allowlist secret
    )
    return user


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.force_login(staff_user)
    return client
