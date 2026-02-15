# Deployment Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses a Docker-first deployment strategy. All services are containerized with multi-stage Dockerfiles that serve both local development and production. Local development uses a hybrid model: infrastructure services (Postgres, Redis) run in Docker while application code runs on the host for optimal developer experience. Production deployment is cloud-agnostic -- the same Docker images deploy to any container platform.

## Specifications

### Docker Compose Configuration

Three compose files serve distinct purposes:

| File | Purpose | Usage |
|------|---------|-------|
| `docker-compose.yml` | Infrastructure only (default dev) | `docker compose up` -- runs Postgres + Redis. Apps run on host. |
| `docker-compose.full.yml` | Full Docker dev (all services) | `docker compose -f docker-compose.full.yml up` -- runs everything in containers. |
| `docker-compose.prod.yml` | Production overrides | Extends base compose. Uses production Dockerfile stages. Adds restart policies. |

**Default development model (hybrid):**

```yaml
# docker-compose.yml -- Infrastructure only
services:
  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_DB: foundation
      POSTGRES_USER: foundation
      POSTGRES_PASSWORD: foundation
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U foundation"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

volumes:
  postgres_data:
```

**Why hybrid dev is the default:**
- File watching and hot reload work natively on host (no Docker VM filesystem latency)
- pnpm/node_modules stay on host (no platform binary mismatches)
- IDE autocomplete works without Docker volume indirection
- Expo dev server needs USB/network access to physical devices

**Production overlay:**

```yaml
# docker-compose.prod.yml (extends base)
services:
  api:
    build:
      context: ./apps/api
      target: prod  # Uses production stage of multi-stage Dockerfile
    environment:
      DEBUG: "false"
    restart: unless-stopped

  web:
    build:
      context: ./apps/web
      target: prod
    restart: unless-stopped

  db:
    restart: unless-stopped
    # In production, consider managed Postgres (RDS, Cloud SQL)
    # instead of a self-hosted container
```

### Docker Image Choices

| Image | Why |
|-------|-----|
| `pgvector/pgvector:pg16` | Official PGVector image based on Postgres 16. Extension pre-installed. Do NOT use plain `postgres:16` and install PGVector manually. |
| `python:3.12-slim` | Slim variant reduces image size. Pin Python version to match local dev. |
| `node:20-slim` | LTS version. Matches pnpm compatibility requirements. |
| `redis:7-alpine` | Alpine variant for minimal image size. Redis 7 for Celery and caching. |

### Dockerfile Patterns (Multi-Stage)

**Django API:**

```dockerfile
# apps/api/Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Development target (used by docker-compose)
FROM base AS dev
RUN pip install --no-cache-dir debugpy watchdog
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production target
FROM base AS prod
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Next.js Web App:**

```dockerfile
# apps/web/Dockerfile
FROM node:20-slim AS base
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

FROM base AS dev
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
CMD ["pnpm", "dev"]

FROM base AS prod
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod
COPY . .
RUN pnpm build
CMD ["pnpm", "start"]
```

**Expo Mobile:** NOT containerized. Even in full Docker mode, the Expo dev server runs on the host. Metro bundler requires host network access and USB access to physical devices.

### Optional Docker Profiles

```yaml
# In docker-compose.yml
services:
  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    command: celery -A config worker -l info
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_healthy }
    profiles:
      - with-worker

  mailpit:
    image: axllent/mailpit
    ports: ["8025:8025", "1025:1025"]
    profiles:
      - with-mail
```

- **Celery worker** uses `--profile with-worker` so it only runs when needed.
- **Mailpit** for local email testing -- captures emails from Django Allauth without a real SMTP server.

### CI/CD Pipeline (GitHub Actions)

Three parallel jobs for fast feedback and clear failure isolation:

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Job 1: Python backend
  api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U test_user"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --directory apps/api
      - run: cd apps/api && ruff check .
      - run: cd apps/api && ruff format --check .
      - run: cd apps/api && mypy .
      - run: cd apps/api && pytest --cov
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db

  # Job 2: JS/TS (web + shared packages)
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo lint
      - run: pnpm turbo type-check
      - run: pnpm turbo test
      - run: pnpm turbo build --filter=web

  # Job 3: Mobile (Expo build check)
  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo lint --filter=mobile
      - run: pnpm turbo type-check --filter=mobile
      # Detox E2E tests require macOS runners (expensive)
      # Only run on main branch merges, not every PR
      # EAS Build handles actual native builds
```

**Key CI decisions:**
- Three parallel jobs (api, web, mobile) -- a flake8 failure does not block mobile type-checking
- Postgres service container with PGVector for API tests
- `uv` for Python dependency installation (faster than pip)
- pnpm caching via `actions/setup-node` built-in cache
- Detox E2E tests are expensive (macOS runner); run on merge to main only
- Expo/EAS Build for actual mobile builds (separate from basic CI)

### Environment Variable Strategy

Each service has its own `.env` file, with a `.env.example` checked into git:

```
foundation-template/
  .env.example                  # Docker Compose variables (committed)
  .env                          # Local overrides (gitignored)
  apps/api/.env.example         # Django-specific (committed)
  apps/api/.env                 # Django local (gitignored)
  apps/web/.env.example         # Next.js-specific (committed)
  apps/web/.env.local           # Next.js local (gitignored)
  apps/mobile/.env.example      # Expo-specific (committed)
```

**Docker Compose `.env`:**
```bash
POSTGRES_DB=foundation
POSTGRES_USER=foundation
POSTGRES_PASSWORD=foundation
DATABASE_URL=postgres://foundation:foundation@db:5432/foundation
```

**Django `apps/api/.env`:**
```bash
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=postgres://foundation:foundation@localhost:5432/foundation
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
REDIS_URL=redis://localhost:6379/0
DJANGO_SETTINGS_MODULE=config.settings.development
```

**Next.js `apps/web/.env.local`:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Turborepo cache invalidation:** `globalDependencies` in `turbo.json` includes `**/.env.*local` so that cache is invalidated when environment changes.

### Deployment Targets (Cloud-Agnostic)

The same Docker images deploy to any container platform:

| Target | Method | Notes |
|--------|--------|-------|
| Local dev | Docker Compose (hybrid) | `docker compose up` for infra; apps on host |
| AWS | ECS/Fargate or EC2 + Docker Compose | Fargate for serverless containers; EC2 for more control |
| GCP | Cloud Run or GKE | Cloud Run is simplest for containerized apps |
| Azure | Container Apps or AKS | Container Apps is the PaaS option |
| DigitalOcean | App Platform or Droplet + Docker Compose | App Platform auto-deploys from Dockerfile |
| Railway/Render | Direct Docker deployment | Simplest for solo developer; detects Dockerfile automatically |
| Self-hosted | Docker Compose on VPS | Same compose file with production overrides |

**Recommended starting point for solo developer:** Railway or Render for API, Vercel for Next.js web app, EAS Build for mobile. Move to AWS/GCP when scaling demands it.

### Root Package Scripts

```json
{
  "scripts": {
    "dev": "turbo dev",
    "build": "turbo build",
    "lint": "turbo lint && cd apps/api && ruff check .",
    "test": "turbo test && cd apps/api && pytest",
    "type-check": "turbo type-check",
    "generate:types": "turbo generate:api-types",
    "db:migrate": "docker compose exec api python manage.py migrate",
    "db:makemigrations": "docker compose exec api python manage.py makemigrations"
  }
}
```

### Initial Project Setup

```bash
# Clone template
git clone <template-repo> my-saas
cd my-saas

# Install JS/TS dependencies
corepack enable
pnpm install

# Install Python dependencies
cd apps/api
uv sync
cd ../..

# Start infrastructure
docker compose up -d db    # Start Postgres first

# Run migrations
cd apps/api && uv run python manage.py migrate
cd ../..

# Start all services
docker compose up          # Infrastructure services
turbo dev                  # All JS/TS apps in parallel
# In separate terminal: cd apps/api && uv run python manage.py runserver
```

## Constraints

1. **Docker-first.** All services must be containerizable. No local-only dependencies that cannot run in Docker.
2. **Multi-stage Dockerfiles.** Every Dockerfile must have `dev` and `prod` stages. Dev stage includes debug tools; prod stage is minimal.
3. **No secrets in Docker images.** All sensitive configuration via environment variables. `.env` files are gitignored. `.env.example` files are committed.
4. **Expo never in Docker.** Metro bundler runs on host always.
5. **Infrastructure-as-code in compose files.** No manual setup steps for Postgres, Redis, or any infrastructure service. Everything declarative in docker-compose.yml.
6. **CI mirrors local.** CI pipeline runs the same lint/test/type-check commands as local development. No CI-only test configuration.
7. **Pinned CI action versions.** All GitHub Actions use pinned versions (e.g., `actions/checkout@v4`), not `@latest`.

## References

- `.planning/research/STACK.md` -- Docker Compose configuration, Dockerfile patterns, CI/CD pipeline details
- `.planning/research/ARCHITECTURE.md` -- Docker Compose service architecture, environment variable strategy
- `openspec/specs/foundation/stack.md` -- Technology versions and compatibility matrix
- `openspec/specs/foundation/architecture.md` -- Monorepo structure and service boundaries
