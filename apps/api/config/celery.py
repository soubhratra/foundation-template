"""
Celery application configuration.

This module creates the Celery app instance and configures it to work with Django.
The app autodiscovers tasks from all installed Django apps.
"""

import os

from celery import Celery

# Set default Django settings module for 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")

# Load configuration from Django settings using CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
