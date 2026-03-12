## ADDED Requirements

### Requirement: Celery Application Configuration

The backend SHALL configure Celery with Redis as the message broker and result backend for asynchronous task processing.

#### Scenario: Celery application initialized with Django settings

- **WHEN** the Django application starts
- **THEN** the Celery app MUST be defined in `config/celery.py`
- **AND** Celery MUST load configuration from Django settings using the `CELERY_` namespace
- **AND** Celery MUST auto-discover `tasks.py` modules in all installed Django apps
- **AND** the Celery app MUST be imported in `config/__init__.py` to ensure early loading

#### Scenario: Redis broker connection configured

- **WHEN** the Celery worker starts
- **THEN** the worker MUST connect to Redis using the URL from `CELERY_BROKER_URL`
- **AND** the broker connection MUST retry on startup instead of crashing immediately
- **AND** both broker and result backend MUST use the same Redis instance
- **AND** only JSON serialization MUST be accepted for security

### Requirement: Background Task Definition Patterns

All Celery tasks SHALL use the `@shared_task` decorator and follow strict definition patterns for reliability and maintainability.

#### Scenario: Basic task with explicit name

- **WHEN** a developer defines a new Celery task
- **THEN** the task MUST use the `@shared_task` decorator
- **AND** the task MUST have an explicit `name` parameter (e.g., `"core.send_email"`)
- **AND** task arguments MUST be JSON-serializable (no Django model instances or datetime objects)
- **AND** Django models and services MUST be imported inside the task function body

#### Scenario: Task with automatic retry logic

- **WHEN** a task is configured with retry settings
- **THEN** the task MUST specify `max_retries` (default: 3)
- **AND** the task MUST specify `autoretry_for` with exception classes that trigger automatic retry
- **AND** retry delays MUST use exponential backoff when `retry_backoff=True` is set
- **AND** the backoff delay MUST be capped by `retry_backoff_max`

#### Scenario: Task with soft time limit handling

- **WHEN** a task exceeds the soft time limit
- **THEN** Celery MUST raise `SoftTimeLimitExceeded` exception
- **AND** the task MUST be allowed to clean up and return partial results
- **AND** the hard time limit MUST kill the worker process if exceeded after soft limit

### Requirement: Embedding Generation Pipeline

The AI module SHALL generate vector embeddings asynchronously using Celery to avoid blocking API request cycles.

#### Scenario: Document created triggers embedding generation

- **WHEN** a new document is created via the API
- **THEN** the controller MUST dispatch `generate_embedding` task asynchronously using `.delay()`
- **AND** the API MUST return 201 immediately without waiting for embedding generation
- **AND** the Celery worker MUST pick up the task from the Redis queue
- **AND** the worker MUST generate the embedding and store it in the document's VectorField

#### Scenario: Idempotent embedding generation with content hash

- **WHEN** the embedding generation task runs for a document
- **THEN** the task MUST compute a SHA-256 hash of the document content
- **AND** the task MUST compare the new hash with the stored `content_hash`
- **AND** if the hashes match, the task MUST skip re-embedding
- **AND** if the hashes differ, the task MUST generate a new embedding

#### Scenario: Embedding API failure with retry

- **WHEN** the embedding API call fails due to rate limit or network error
- **THEN** the task MUST raise an exception
- **AND** Celery MUST retry the task up to 3 times with 60-second delays
- **AND** if all retries fail, the task MUST be marked as failed
- **AND** the document's embedding field MUST remain null or stale

### Requirement: Email Notification Task

The system SHALL send transactional emails asynchronously using Celery to avoid blocking request cycles.

#### Scenario: Email sent in development environment

- **WHEN** the `send_email_task` executes in development
- **THEN** Django's console email backend MUST be used
- **AND** the email content MUST be printed to the Celery worker's terminal output
- **AND** no actual email MUST be sent

#### Scenario: Email sent in production environment with retry

- **WHEN** the `send_email_task` executes in production
- **THEN** the email MUST be sent via the configured SMTP server
- **AND** the task MUST retry up to 3 times on transient failures
- **AND** the task MUST return a status dict with `status` and `recipient` fields

### Requirement: Periodic Task Scheduling

The system SHALL support periodic task scheduling using Celery Beat for recurring maintenance jobs.

#### Scenario: Periodic tasks configured in Django settings

- **WHEN** periodic tasks are defined in `CELERY_BEAT_SCHEDULE`
- **THEN** each task MUST specify a `task` name and a `schedule` (cron or interval)
- **AND** all schedules MUST be defined in UTC timezone
- **AND** Celery Beat MUST run as a separate process from the worker
- **AND** Beat MUST dispatch tasks to the worker queue according to the schedule

#### Scenario: Periodic task is idempotent

- **WHEN** a periodic task is executed by Celery Beat
- **THEN** running the same task twice in a row MUST produce the same result
- **AND** the task MUST handle potential duplicate executions gracefully
- **AND** the task MUST not cause side effects if executed multiple times

### Requirement: Celery Worker Docker Compose Integration

The Celery worker SHALL run as an always-on Docker Compose service (not profile-gated) in the v1.2 template baseline, ensuring background task processing is available by default.

#### Scenario: Docker Compose started without profile flags

- **WHEN** Docker Compose is started with `docker compose up`
- **THEN** the `celery-worker` service MUST start automatically
- **AND** the worker MUST connect to Redis and begin processing queued tasks
- **AND** the worker MUST use 2 concurrent processes in development
- **AND** the worker MUST depend on both database and Redis health checks passing

#### Scenario: Celery worker no longer profile-gated

- **WHEN** the docker-compose.yml is read
- **THEN** the `celery-worker` service MUST NOT have a `profiles` key restricting it
- **AND** starting the full Compose stack MUST include the worker without any additional flags

### Requirement: Task Monitoring and Observability

The system SHALL track task states and provide logging for background task execution.

#### Scenario: Task state tracked in result backend

- **WHEN** a task is dispatched and executed
- **THEN** the task state MUST be stored in Redis result backend
- **AND** task states MUST include: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
- **AND** task results MUST expire after 24 hours by default
- **AND** developers MUST be able to query task status using `AsyncResult(task_id)`

#### Scenario: Task logs structured output

- **WHEN** a task executes and logs messages
- **THEN** the task MUST use Celery's task logger via `get_task_logger(__name__)`
- **AND** log output MUST include task name, task ID, and arguments automatically
- **AND** logs MUST be written to the worker's stdout for container log aggregation

### Requirement: Celery Beat with DatabaseScheduler

The system SHALL run Celery Beat as a dedicated Docker Compose service using `django-celery-beat`'s `DatabaseScheduler`, storing periodic task schedules in the Django database rather than in a flat file.

#### Scenario: celery-beat service defined in Docker Compose

- **WHEN** Docker Compose is started
- **THEN** a `celery-beat` service MUST start alongside `celery-worker`
- **AND** the service MUST run `celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel=info`
- **AND** the service MUST depend on the database health check before starting
- **AND** Beat MUST run as a separate container from the worker

#### Scenario: Periodic task schedules managed via Django admin

- **WHEN** `django-celery-beat` is installed and `django_celery_beat` is in `INSTALLED_APPS`
- **THEN** Django admin MUST expose `PeriodicTask`, `CrontabSchedule`, and `IntervalSchedule` models
- **AND** administrators MUST be able to create, modify, and disable periodic tasks without restarting the Celery process
- **AND** schedule changes MUST be picked up by Beat on the next polling interval

#### Scenario: DatabaseScheduler used instead of file-based scheduler

- **WHEN** Celery Beat starts
- **THEN** it MUST use `DatabaseScheduler` and NOT write a `celerybeat-schedule` file
- **AND** the `celerybeat-schedule` file MUST be gitignored if it ever appears locally

### Requirement: Flower Dev Monitoring

The system SHALL provide a Flower monitoring service in Docker Compose for local development visibility into Celery task execution.

#### Scenario: Flower accessible at port 5555 in development

- **WHEN** Docker Compose is started in development
- **THEN** a `flower` service MUST be defined and accessible at `http://localhost:5555`
- **AND** Flower MUST connect to the same Redis broker as the Celery worker
- **AND** Flower MUST display active workers, task history, and queue depths in real time

#### Scenario: Flower excluded from production Compose

- **WHEN** `docker-compose.prod.yml` is used
- **THEN** the `flower` service MUST NOT be present
- **AND** no Flower packages or ports MUST be exposed in production

### Requirement: Example Periodic Task with Retry and Backoff

The template SHALL include a documented example periodic task demonstrating the retry-with-exponential-backoff pattern for developers to copy when building their own periodic tasks.

#### Scenario: Example task registered in CELERY_BEAT_SCHEDULE

- **WHEN** the template is scaffolded
- **THEN** `config/settings/base.py` MUST include a `CELERY_BEAT_SCHEDULE` dict with at least one example entry
- **AND** the example task MUST demonstrate a cron or interval schedule

#### Scenario: Example task uses retry with backoff

- **WHEN** the example periodic task is defined
- **THEN** it MUST use `@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)`
- **AND** the task body MUST include a comment explaining the backoff behavior
- **AND** the task MUST be idempotent (safe to run multiple times)
