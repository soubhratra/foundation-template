"""Tests for health probe endpoints (plain Django views, not Ninja versioned).

The old /api/v1/health endpoint (HealthController) was removed in Phase 15-02.
These tests now cover the new probe paths at /api/health/.
"""

import pytest


@pytest.mark.django_db
def test_live_probe_returns_200(api_client):
    """Liveness probe returns 200 OK with status=alive."""
    response = api_client.get("/api/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.django_db
def test_ready_probe_includes_all_checks(api_client):
    """Readiness probe response includes postgres, redis, and celery check keys."""
    response = api_client.get("/api/health/ready")
    # May be 200 (all deps up) or 503 (some deps down in test env) — both are valid
    assert response.status_code in (200, 503)
    data = response.json()
    assert "checks" in data
    checks = data["checks"]
    assert "postgres" in checks
    assert "redis" in checks
    assert "celery" in checks
