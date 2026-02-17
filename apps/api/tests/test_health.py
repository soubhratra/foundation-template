"""Unit tests for health check endpoint."""

import pytest


@pytest.mark.django_db
def test_health_check_returns_200(api_client):
    """Health check endpoint returns 200 OK."""
    response = api_client.get("/api/v1/health", HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


@pytest.mark.django_db
def test_health_check_includes_database_status(api_client):
    """Health check includes database connectivity status."""
    response = api_client.get("/api/v1/health", HTTP_ACCEPT="application/json")
    data = response.json()
    assert data["database"] == "connected"
