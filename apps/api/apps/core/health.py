"""Kubernetes-style health probe view functions.

Plain Django views (not Ninja) so probes work even if the Ninja app is
misconfigured. No auth, no middleware overhead.

Endpoints:
  GET /api/health/live     -> liveness probe
  GET /api/health/ready    -> readiness probe
  GET /api/health/startup  -> startup probe
"""

import redis
from django.conf import settings
from django.db import connection
from django.http import HttpRequest, JsonResponse

# ---------------------------------------------------------------------------
# Internal helpers — extracted so tests can mock them cleanly
# ---------------------------------------------------------------------------


def _check_postgres() -> None:
    """Execute a trivial query. Raises on any DB error."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")


def _check_redis() -> None:
    """Ping Redis. Raises on connection error."""
    redis.Redis.from_url(settings.REDIS_URL).ping()


def _check_celery() -> None:
    """Ping Celery workers. Raises if no workers respond."""
    from config.celery import app as celery_app  # local import avoids circular

    inspect = celery_app.control.inspect(timeout=1.0)
    pong = inspect.ping()
    if not pong:
        raise RuntimeError("no workers")


def _count_pending_migrations() -> int:
    """Return the number of unapplied migrations."""
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return len(plan)


# ---------------------------------------------------------------------------
# View functions
# ---------------------------------------------------------------------------


def live_view(request: HttpRequest) -> JsonResponse:
    """Liveness probe — returns 200 if the process is running.

    Never makes external calls. If this fails, the process itself is broken.
    """
    return JsonResponse({"status": "alive"}, status=200)


def ready_view(request: HttpRequest) -> JsonResponse:
    """Readiness probe — checks Postgres, Redis, and Celery.

    Returns 200 with all checks "ok" when all dependencies are reachable.
    Returns 503 with "status": "degraded" and the failing check named when
    any dependency is down.
    """
    checks: dict[str, str] = {}

    # Postgres
    try:
        _check_postgres()
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    # Redis
    try:
        _check_redis()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    # Celery
    try:
        _check_celery()
        checks["celery"] = "ok"
    except Exception as exc:
        checks["celery"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    body = {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
    }
    return JsonResponse(body, status=status_code)


def startup_view(request: HttpRequest) -> JsonResponse:
    """Startup probe — checks that all migrations are applied.

    Returns 200 with pending_migrations=0 when fully migrated.
    Returns 503 with the pending count when migrations are outstanding.
    Returns 503 with pending_migrations=-1 if the database is unreachable.
    """
    try:
        pending = _count_pending_migrations()
    except Exception:
        return JsonResponse({"status": "error", "pending_migrations": -1}, status=503)

    if pending == 0:
        return JsonResponse({"status": "ready", "pending_migrations": 0}, status=200)
    return JsonResponse({"status": "pending", "pending_migrations": pending}, status=503)
