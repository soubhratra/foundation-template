## MODIFIED Requirements

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

## ADDED Requirements

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
