# Background Tasks (Celery)

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses Celery with a Redis broker for asynchronous background task processing. Celery handles tasks that are too slow for the request/response cycle: embedding generation for the AI module, transactional email delivery, and periodic maintenance jobs. The Celery worker runs as an optional Docker Compose service (via profiles) so developers who do not need background processing are not burdened by it.

## Specifications

### 1. Celery Application Configuration

The Celery application is defined in `config/celery.py` and loaded automatically when Django starts.

**`config/celery.py`:**

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("foundation")

# Load Celery settings from Django settings, using the CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed Django apps
app.autodiscover_tasks()
```

**`config/__init__.py`:**

```python
from .celery import app as celery_app

__all__ = ["celery_app"]
```

This ensures the Celery app is loaded when Django starts, making `@shared_task` decorators work correctly.

### 2. Django Settings for Celery

All Celery configuration lives in `config/settings/base.py` under the `CELERY_` namespace.

```python
# Celery configuration
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300          # Hard time limit: 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240     # Soft time limit: 4 minutes (raises SoftTimeLimitExceeded)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker after 1000 tasks (prevents memory leaks)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
```

**Settings reference:**

| Setting | Value | Purpose |
|---------|-------|---------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis as message broker. Same Redis instance as cache. |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Store task results in Redis. Enables `.get()` and status polling. |
| `CELERY_ACCEPT_CONTENT` | `["json"]` | Only accept JSON-serialized messages. No unsafe serializers allowed. |
| `CELERY_TASK_SERIALIZER` | `"json"` | Serialize task arguments as JSON. |
| `CELERY_RESULT_SERIALIZER` | `"json"` | Serialize task results as JSON. |
| `CELERY_TIMEZONE` | `"UTC"` | All scheduled times in UTC. Matches Django's `TIME_ZONE`. |
| `CELERY_TASK_TRACK_STARTED` | `True` | Enables `STARTED` state for running tasks. |
| `CELERY_TASK_TIME_LIMIT` | `300` | Hard kill after 5 minutes. Prevents stuck tasks from blocking workers. |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `240` | Raises `SoftTimeLimitExceeded` at 4 minutes. Task can clean up before hard kill. |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | `1000` | Recycle worker processes to prevent memory leaks from long-running workers. |
| `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP` | `True` | Retry Redis connection on worker startup instead of crashing immediately. |

### 3. Redis Service (Docker Compose)

Redis is a required infrastructure service for the Celery broker.

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Redis is shared between Celery (broker + result backend) and Django caching. Database `0` is the default for both. If separation is needed, Celery can use database `1` by changing the URL to `redis://redis:6379/1`.

### 4. Celery Worker (Docker Compose with Profiles)

The Celery worker runs as an optional service using Docker Compose profiles. Developers who do not need background tasks can skip starting the worker.

```yaml
# docker-compose.yml
services:
  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
      target: dev
    volumes:
      - ./apps/api:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/foundation
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A config worker -l info --concurrency=2
    profiles:
      - with-worker
```

**Starting with the worker:**

```bash
# Without worker (default)
docker compose up

# With worker
docker compose --profile with-worker up
```

**Worker command flags:**

| Flag | Value | Purpose |
|------|-------|---------|
| `-A config` | Celery app location | Points to `config.celery:app`. |
| `worker` | Subcommand | Run as a worker process. |
| `-l info` | Log level | Info-level logging. Use `debug` for troubleshooting. |
| `--concurrency=2` | Worker processes | 2 concurrent task workers for development. Scale up in production. |

### 5. Task Definition Patterns

All tasks use the `@shared_task` decorator so they are not tied to a specific Celery app instance. Tasks live in `tasks.py` within each Django app.

#### 5.1 Basic Task

```python
# apps/core/tasks.py
from celery import shared_task


@shared_task(name="core.send_email")
def send_email_task(subject: str, body: str, recipient: str) -> dict:
    """Send a transactional email asynchronously."""
    from django.core.mail import send_mail

    send_mail(
        subject=subject,
        message=body,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[recipient],
    )
    return {"status": "sent", "recipient": recipient}
```

#### 5.2 Task with Retry Logic

```python
# apps/ai/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    name="ai.generate_embedding",
    bind=True,
    max_retries=3,
    default_retry_delay=10,    # 10 seconds between retries
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,        # Exponential backoff: 10s, 20s, 40s
    retry_backoff_max=120,     # Cap backoff at 2 minutes
)
def generate_embedding_task(self, document_id: int) -> dict:
    """Generate a vector embedding for a document."""
    from .services import EmbeddingService

    try:
        service = EmbeddingService()
        embedding = service.generate_and_store(document_id=document_id)
        return {
            "status": "completed",
            "document_id": document_id,
            "dimensions": len(embedding),
        }
    except Exception as exc:
        logger.error(
            "Embedding generation failed for document %s: %s",
            document_id,
            str(exc),
        )
        raise self.retry(exc=exc)
```

#### 5.3 Task with Soft Time Limit Handling

```python
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded


@shared_task(name="ai.batch_embed", bind=True, soft_time_limit=180)
def batch_embed_task(self, document_ids: list[int]) -> dict:
    """Generate embeddings for multiple documents."""
    from .services import EmbeddingService

    service = EmbeddingService()
    completed = []
    failed = []

    for doc_id in document_ids:
        try:
            service.generate_and_store(document_id=doc_id)
            completed.append(doc_id)
        except SoftTimeLimitExceeded:
            # Clean up and report partial progress
            failed.extend([d for d in document_ids if d not in completed])
            return {
                "status": "partial",
                "completed": completed,
                "failed": failed,
                "reason": "time_limit_exceeded",
            }
        except Exception as exc:
            failed.append(doc_id)

    return {
        "status": "completed" if not failed else "partial",
        "completed": completed,
        "failed": failed,
    }
```

**Task definition rules:**

| Rule | Description |
|------|-------------|
| `@shared_task` | Always use `@shared_task`, never `@app.task`. Shared tasks are decoupled from the Celery app instance. |
| `name` parameter | Always provide an explicit `name` string. Auto-generated names break when modules are moved. |
| `bind=True` | Use `bind=True` when the task needs access to `self` for retries or task metadata. |
| JSON-serializable arguments | All task arguments MUST be JSON-serializable (str, int, float, bool, list, dict, None). No Django model instances, no datetime objects. Pass IDs and re-query in the task. |
| Import inside task body | Import Django models and services inside the task function body, not at module level. This avoids circular imports and ensures the Django app registry is ready. |
| Return value | Return a dict with at least a `status` field for observability. |

### 6. Embedding Generation Task (AI Module)

The primary AI-related background task generates vector embeddings for documents and stores them in PGVector.

**Task flow:**

```
1. Content is created/updated in Django
2. Django signal or explicit call dispatches generate_embedding_task.delay(document_id)
3. Celery worker picks up the task
4. EmbeddingService calls the embedding API (OpenAI, local model, etc.)
5. Resulting vector is stored in the document's VectorField column
6. HNSW index is automatically updated by PGVector
```

**Dispatching from a service:**

```python
# apps/ai/services.py
from .tasks import generate_embedding_task


class DocumentService:
    def create_document(self, user, data) -> "Document":
        document = Document.objects.create(owner=user, **data.dict())
        # Dispatch embedding generation asynchronously
        generate_embedding_task.delay(document.id)
        return document
```

**Dispatching from a Django signal (alternative):**

```python
# apps/ai/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document
from .tasks import generate_embedding_task


@receiver(post_save, sender=Document)
def trigger_embedding_on_save(sender, instance, created, **kwargs):
    if created or instance.content_changed:
        generate_embedding_task.delay(instance.id)
```

### 7. Email Sending Task

Transactional emails are sent asynchronously to avoid blocking the request/response cycle.

```python
# apps/core/tasks.py
from celery import shared_task


@shared_task(
    name="core.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_email_task(self, subject: str, body: str, recipient: str, html_body: str = None) -> dict:
    """Send a transactional email."""
    from django.core.mail import EmailMultiAlternatives

    email = EmailMultiAlternatives(
        subject=subject,
        body=body,
        to=[recipient],
    )
    if html_body:
        email.attach_alternative(html_body, "text/html")

    email.send()
    return {"status": "sent", "recipient": recipient}
```

**Usage from a service:**

```python
from apps.core.tasks import send_email_task

send_email_task.delay(
    subject="Welcome to Foundation",
    body="Thanks for signing up!",
    recipient="user@example.com",
    html_body="<h1>Welcome!</h1><p>Thanks for signing up!</p>",
)
```

In development (`config/settings/development.py`), Django's console email backend prints emails to the terminal. In production, emails are sent via SMTP. The task is identical in both environments; only the Django `EMAIL_BACKEND` setting changes.

### 8. Periodic Tasks (Celery Beat)

Celery Beat schedules recurring tasks. Configuration lives in Django settings.

```python
# config/settings/base.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "cleanup-expired-sessions": {
        "task": "core.cleanup_expired_sessions",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    "reindex-stale-embeddings": {
        "task": "ai.reindex_stale_embeddings",
        "schedule": crontab(hour="*/6", minute=0),  # Every 6 hours
    },
}
```

**Beat worker Docker Compose service:**

```yaml
# docker-compose.yml
services:
  beat:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
      target: dev
    volumes:
      - ./apps/api:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/foundation
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=config.settings.development
    depends_on:
      redis:
        condition: service_healthy
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    profiles:
      - with-worker
```

**Periodic task example:**

```python
# apps/core/tasks.py
from celery import shared_task


@shared_task(name="core.cleanup_expired_sessions")
def cleanup_expired_sessions_task() -> dict:
    """Remove expired Django sessions from the database."""
    from django.core.management import call_command

    call_command("clearsessions")
    return {"status": "completed"}
```

**Beat rules:**

| Rule | Description |
|------|-------------|
| Beat runs as a separate process | Never combine beat and worker in the same process. Use `--beat` flag on worker only for single-machine development. |
| Schedule in UTC | All cron schedules use UTC. This is enforced by `CELERY_TIMEZONE = "UTC"`. |
| Idempotent periodic tasks | Periodic tasks MUST be idempotent. Beat may fire a task twice if the scheduler restarts. |
| `with-worker` profile | Beat is part of the same Docker profile as the worker. They are started together. |

### 9. Task Error Handling and Retry Strategy

**Retry configuration hierarchy:**

| Configuration | Scope | Description |
|---------------|-------|-------------|
| `max_retries` | Per-task | Maximum number of retry attempts. Default: `3`. |
| `default_retry_delay` | Per-task | Base delay between retries in seconds. Default: varies. |
| `autoretry_for` | Per-task | Tuple of exception classes that trigger automatic retry. |
| `retry_backoff` | Per-task | When `True`, uses exponential backoff (delay doubles each retry). |
| `retry_backoff_max` | Per-task | Maximum backoff delay in seconds. Caps exponential growth. |
| `CELERY_TASK_TIME_LIMIT` | Global | Hard time limit. Worker process is killed after this. |
| `CELERY_TASK_SOFT_TIME_LIMIT` | Global | Raises `SoftTimeLimitExceeded`. Task can clean up. |

**Error handling pattern:**

```python
@shared_task(
    name="example.task",
    bind=True,
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=120,
)
def example_task(self, item_id: int) -> dict:
    try:
        # Task logic here
        return {"status": "completed", "item_id": item_id}
    except (ConnectionError, TimeoutError):
        # autoretry_for handles these automatically
        raise
    except Exception as exc:
        # Log non-retryable errors
        logger.exception("Unexpected error in example_task for item %s", item_id)
        return {"status": "failed", "item_id": item_id, "error": str(exc)}
```

**Dead letter pattern:** Tasks that exhaust all retries are logged. The template does not implement a dead letter queue by default, but the retry callback pattern enables it:

```python
@shared_task(bind=True, name="example.with_final_failure", max_retries=3)
def task_with_final_failure_handling(self, item_id: int):
    try:
        # ... task logic ...
        pass
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            # Final retry exhausted -- log for manual review
            logger.critical(
                "Task %s permanently failed for item %s after %d retries",
                self.name,
                item_id,
                self.max_retries,
            )
            return {"status": "permanently_failed", "item_id": item_id}
        raise self.retry(exc=exc)
```

### 10. Task Monitoring and Observability

**Logging:**

All tasks use Celery's task logger for structured output:

```python
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
```

Task logs include the task name, task ID, and arguments automatically via Celery's log format.

**Task state tracking:**

Celery tracks task states in the result backend (Redis):

| State | Meaning |
|-------|---------|
| `PENDING` | Task is waiting in the queue. |
| `STARTED` | Task has been picked up by a worker (requires `CELERY_TASK_TRACK_STARTED = True`). |
| `SUCCESS` | Task completed successfully. |
| `FAILURE` | Task raised an exception (after all retries exhausted). |
| `RETRY` | Task is waiting to be retried. |
| `REVOKED` | Task was cancelled. |

**Querying task status (from Django):**

```python
from celery.result import AsyncResult

result = AsyncResult(task_id)
print(result.state)    # "PENDING", "STARTED", "SUCCESS", "FAILURE"
print(result.result)   # Return value (if SUCCESS) or exception (if FAILURE)
```

**Flower (optional monitoring):**

For production monitoring, Flower provides a web UI for Celery. It is NOT included in the base template but can be added:

```yaml
# docker-compose.yml (optional)
services:
  flower:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
      target: dev
    command: celery -A config flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    profiles:
      - with-monitoring
```

### 11. Task Invocation Patterns

| Pattern | Code | When to Use |
|---------|------|-------------|
| Fire and forget | `my_task.delay(arg1, arg2)` | Most common. Do not need the result. |
| With result tracking | `result = my_task.apply_async(args=[arg1], kwargs={"key": val})` | When you need to poll for task completion. |
| Delayed execution | `my_task.apply_async(args=[arg1], countdown=60)` | Execute 60 seconds from now. |
| Scheduled execution | `my_task.apply_async(args=[arg1], eta=datetime)` | Execute at a specific datetime. |
| Chain (sequential) | `chain(task_a.s(arg), task_b.s())()` | Run tasks in sequence, passing results. |
| Group (parallel) | `group(task_a.s(id) for id in ids)()` | Run multiple tasks in parallel. |

### 12. Testing Tasks

Tasks are tested synchronously in pytest using `CELERY_TASK_ALWAYS_EAGER = True`.

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def celery_eager_mode(settings):
    """Run Celery tasks synchronously in tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
```

**Test example:**

```python
# apps/ai/tests/test_tasks.py
from apps.ai.tasks import generate_embedding_task


def test_generate_embedding_task_success(db, document_factory, mocker):
    document = document_factory()
    mocker.patch(
        "apps.ai.services.EmbeddingService.generate_and_store",
        return_value=[0.1] * 1536,
    )

    result = generate_embedding_task(document.id)

    assert result["status"] == "completed"
    assert result["document_id"] == document.id
    assert result["dimensions"] == 1536


def test_generate_embedding_task_retries_on_connection_error(
    db, document_factory, mocker
):
    document = document_factory()
    mocker.patch(
        "apps.ai.services.EmbeddingService.generate_and_store",
        side_effect=ConnectionError("API unavailable"),
    )

    with pytest.raises(ConnectionError):
        generate_embedding_task(document.id)
```

## Scenarios

### GIVEN the Celery worker is running and connected to Redis
### WHEN `generate_embedding_task.delay(document_id)` is called from a Django service
### THEN the task is placed in the Redis queue, picked up by the worker, and the embedding is generated and stored in the document's VectorField

---

### GIVEN a task is configured with `max_retries=3` and `retry_backoff=True`
### WHEN the task raises a `ConnectionError` on the first attempt
### THEN the task is retried after 10 seconds, then 20 seconds, then 40 seconds, and if all retries fail, the task status is `FAILURE`

---

### GIVEN the soft time limit is 240 seconds
### WHEN a task exceeds 240 seconds of execution time
### THEN `SoftTimeLimitExceeded` is raised, allowing the task to clean up and return a partial result before the hard limit kills the process

---

### GIVEN Docker Compose is started without the `with-worker` profile
### WHEN a task is dispatched via `.delay()`
### THEN the task sits in the Redis queue indefinitely (no worker to process it) and the API request that dispatched it returns immediately without blocking

---

### GIVEN Docker Compose is started with `--profile with-worker`
### WHEN the worker container starts
### THEN the Celery worker connects to Redis and begins processing queued tasks

---

### GIVEN `CELERY_TASK_ALWAYS_EAGER = True` is set in test settings
### WHEN a test calls `my_task.delay(arg)`
### THEN the task executes synchronously in the test process, and the return value is available immediately

---

### GIVEN a periodic task is configured in `CELERY_BEAT_SCHEDULE`
### WHEN the Celery Beat scheduler reaches the cron schedule time
### THEN the task is dispatched to the worker queue according to the schedule

---

### GIVEN the development environment uses Django's console email backend
### WHEN `send_email_task.delay(subject, body, recipient)` executes
### THEN the email content is printed to the Celery worker's terminal output (not actually sent)

---

### GIVEN the production environment uses SMTP email backend
### WHEN `send_email_task.delay(subject, body, recipient)` executes
### THEN the email is sent via the configured SMTP server, and the task retries up to 3 times on transient failures

## Constraints

- Task arguments MUST be JSON-serializable. Do NOT pass Django model instances, querysets, or datetime objects as task arguments. Pass primary keys and re-query inside the task.
- All tasks MUST have an explicit `name` parameter. Auto-generated names based on module paths break when code is refactored.
- Tasks MUST NOT import Django models or services at module level. Imports go inside the task function body to avoid app registry issues.
- Only JSON serialization is permitted. `CELERY_ACCEPT_CONTENT` is restricted to `["json"]` for security. No other serializers are allowed.
- The Celery worker is an optional service. The API MUST function correctly when no worker is running (tasks queue but do not execute).
- Periodic tasks MUST be idempotent. Running the same task twice in a row MUST produce the same result.
- The hard time limit (`CELERY_TASK_TIME_LIMIT = 300`) MUST NOT be disabled. Stuck tasks block worker capacity.
- Redis is a required infrastructure dependency (for broker and result backend). The API server does not start Celery workers; it only dispatches tasks.
- Embedding generation MUST be asynchronous (via Celery). Synchronous embedding in the request cycle adds 200-500ms latency per request.
- Task results stored in Redis expire after 24 hours by default (`CELERY_RESULT_EXPIRES = 86400`). Do NOT rely on result backend for permanent storage.

## References

- `.planning/research/ARCHITECTURE.md` -- Docker Compose service architecture: worker service with profiles, Redis service
- `.planning/research/ARCHITECTURE.md` -- AI Module Data Flow: embedding pipeline via Celery tasks
- `.planning/research/ARCHITECTURE.md` -- Scaling Considerations: Celery worker scaling at different user counts
- `.planning/research/STACK.md` -- Celery as background task queue, Redis as broker
- `.planning/research/PITFALLS.md` -- Performance trap: embedding generation in request cycle adds 200-500ms latency
- `.planning/PROJECT.md` -- Optional AI module with embedding pipeline requirement
