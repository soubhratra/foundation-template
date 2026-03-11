"""Celery application configuration.

Registers DjangoStructLogInitStep for structlog context propagation across
Django request -> Celery task boundaries (Phase 13).

OTel tracing for Celery workers is initialized in init_celery_tracing() via
worker_process_init signal (after prefork) to avoid losing BatchSpanProcessor
threads across fork boundaries.
"""

import os

from celery import Celery
from celery.signals import worker_process_init
from django_structlog.celery.steps import DjangoStructLogInitStep

# Set default Django settings module for 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")

# Load configuration from Django settings using CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()

# Register structlog context propagation step.
# Handles task_prerun / task_postrun signals that bind task_id + task_name
# and propagate request_id from the dispatching Django request into the task context.
app.steps["worker"].add(DjangoStructLogInitStep)


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    """Initialize OTel tracing in each Celery worker process after prefork.

    MUST run inside worker_process_init (after fork). Celery uses a prefork model;
    BatchSpanProcessor spawns daemon threads that are lost across fork boundaries.
    Initializing here ensures each worker process has its own live processor threads.
    """
    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    from apps.core.tracing import configure_otel

    configure_otel(service_name="foundation-celery-worker")
    CeleryInstrumentor().instrument()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
