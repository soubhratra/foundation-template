"""Pytest configuration and shared fixtures."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


@pytest.fixture(scope="session", autouse=True)
def enable_pgvector_for_tests(django_db_setup, django_db_blocker):
    """Install pgvector extension in test database before migrations run."""
    # This runs after test database is created but we need to ensure extension exists
    # The migrations will handle creating it via IF NOT EXISTS
    pass


@pytest.fixture
def api_client(db):
    """Provide Django test client for API testing."""
    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Provide authenticated API client."""
    api_client.force_login(user=user)
    return api_client
