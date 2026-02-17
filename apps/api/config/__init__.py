"""
Config package initialization.

Imports the Celery app to ensure it's loaded when Django starts.
This allows Celery to discover tasks in all installed apps.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
