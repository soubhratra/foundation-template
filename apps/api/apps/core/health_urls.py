"""URL patterns for health probe endpoints.

Mounted at /api/health/ prefix in config/urls.py.
Plain Django views — no Ninja versioning, no auth.
"""

from django.urls import path

from apps.core.health import live_view, ready_view, startup_view

urlpatterns = [
    path("live", live_view, name="health-live"),
    path("ready", ready_view, name="health-ready"),
    path("startup", startup_view, name="health-startup"),
]
