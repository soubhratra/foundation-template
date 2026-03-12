"""RED test stubs for OBS-04: Kubernetes health probe endpoints.

These tests are intentionally in RED state — apps.core.health does not exist yet.
Plan 15-02 will create that module and turn these GREEN.

Endpoints under test (plain Django views, not Ninja versioned):
  GET /api/health/live     -> liveness probe
  GET /api/health/ready    -> readiness probe
  GET /api/health/startup  -> startup probe
"""

import unittest.mock

import pytest


@pytest.mark.django_db
def test_live_returns_200(api_client):
    """Liveness probe returns 200 with status=alive when process is running."""
    from apps.core import health as _health  # noqa: F401 — RED: module not yet created

    response = api_client.get("/api/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.django_db
def test_ready_returns_200_when_all_deps_ok(api_client):
    """Readiness probe returns 200 with all checks ok when all dependencies healthy."""
    from apps.core import health as _health  # noqa: F401 — RED: module not yet created

    response = api_client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["postgres"] == "ok"
    assert data["checks"]["redis"] == "ok"
    assert data["checks"]["celery"] == "ok"


@pytest.mark.django_db
def test_ready_returns_503_when_postgres_failing(api_client):
    """Readiness probe returns 503 with degraded status when postgres check fails."""
    from apps.core import health as _health  # noqa: F401 — RED: module not yet created

    with unittest.mock.patch(
        "apps.core.health._check_postgres", side_effect=Exception("connection refused")
    ):
        response = api_client.get("/api/health/ready")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert "checks" in data
    assert "error" in data["checks"]["postgres"]
    assert data["checks"]["redis"] == "ok"
    assert data["checks"]["celery"] == "ok"


@pytest.mark.django_db
def test_startup_returns_200_when_no_pending_migrations(api_client):
    """Startup probe returns 200 when no pending migrations exist."""
    from apps.core import health as _health  # noqa: F401 — RED: module not yet created

    with unittest.mock.patch("apps.core.health._count_pending_migrations", return_value=0):
        response = api_client.get("/api/health/startup")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["pending_migrations"] == 0


@pytest.mark.django_db
def test_startup_returns_503_when_migrations_pending(api_client):
    """Startup probe returns 503 when pending migrations exist."""
    from apps.core import health as _health  # noqa: F401 — RED: module not yet created

    with unittest.mock.patch("apps.core.health._count_pending_migrations", return_value=3):
        response = api_client.get("/api/health/startup")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "pending"
    assert data["pending_migrations"] == 3
