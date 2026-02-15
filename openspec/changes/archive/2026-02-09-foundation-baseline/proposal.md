## Why

Every new SaaS project starts from scratch — wiring up auth, configuring monorepo tooling, setting up type-safe API clients, building the same login/signup flows. This foundation template eliminates that repeated work by providing a production-ready full-stack starter kit (Django Ninja Extra + Next.js 15 + Expo + Turborepo) that takes a new project from zero to running app in under 5 minutes.

## What Changes

This is the initial baseline — everything is new:

- Turborepo monorepo with pnpm workspaces for JS/TS and uv for Python
- Docker Compose local development (Postgres 16 + PGVector + Redis)
- Django Ninja Extra API with layered architecture and auto-generated OpenAPI 3.1 spec
- Dual auth strategy via Django Allauth headless (session cookies for web, JWT for mobile)
- Type generation pipeline: OpenAPI spec → openapi-typescript → openapi-fetch typed client
- Shared packages: api-client, validation (Zod), ui (React Native Web primitives), business-logic
- Next.js 15 App Router web app with Shadcn/ui, auth flows, dashboard shell
- Expo managed workflow mobile app with tab navigation, JWT persistence, shared package consumption
- Optional AI module: PGVector embeddings, LangGraph agent scaffold, Celery pipeline
- GitHub Actions CI/CD with parallel jobs, pre-commit hooks, production Dockerfiles
- Interactive CLI scaffolder for generating new projects from the template

## Capabilities

### New Capabilities

- `monorepo`: Turborepo + pnpm workspace scaffolding, shared configs (tsconfig, eslint), root orchestration
- `docker-infra`: Docker Compose for Postgres 16 + PGVector + Redis, hybrid dev model (infra in Docker, apps on host)
- `django-api`: Django Ninja Extra REST API with layered architecture, settings split, custom user model, health check
- `api-contracts`: OpenAPI 3.1 spec export, type generation pipeline, CORS configuration, error response format
- `auth`: Django Allauth headless mode, dual auth strategy (session + JWT), all auth flows (signup/login/logout/reset/verify)
- `data-models`: Custom AbstractUser, BaseModel mixin (timestamps, soft delete), PGVector EmbeddingMixin, migration strategy
- `shared-packages`: 6 shared packages (api-client, validation, ui, business-logic, config-eslint, config-ts)
- `nextjs-app`: Next.js 15 App Router, Shadcn/ui, auth pages, dashboard shell, middleware guards, dark mode
- `expo-app`: Expo Router, auth screens, tab navigation, JWT management with expo-secure-store, Metro config
- `ai-module`: PGVector HNSW indexes, LangGraph agent scaffold, Celery embedding pipeline, module isolation
- `background-tasks`: Celery configuration, task patterns, embedding pipeline, email tasks, periodic tasks
- `error-handling`: Error strategy across Django/Next.js/Expo, error code taxonomy, logging
- `testing`: pytest/vitest/detox patterns, CI integration, coverage thresholds
- `security`: Auth security, CSRF, CORS, secrets management, input validation, dependency scanning
- `conventions`: Naming conventions, file structure, git conventions, env var strategy, code quality tooling
- `devex-ci`: Pre-commit hooks, GitHub Actions, type staleness gate, production Dockerfiles
- `cli-scaffolder`: Interactive CLI for project generation, name/config replacement, AI module exclusion

### Modified Capabilities

_None — this is the initial baseline._

## Impact

- **Code**: Entire repository is scaffolded from scratch across all apps and packages
- **APIs**: All REST endpoints defined (auth, health, user, AI/vector search)
- **Dependencies**: Full dependency tree for Python (Django, Ninja Extra, Allauth, Celery, pgvector) and JS/TS (Next.js, Expo, openapi-typescript, openapi-fetch, Zod, React Native Web)
- **Systems**: Local Docker infrastructure (Postgres, Redis), CI/CD pipeline (GitHub Actions), pre-commit hooks
