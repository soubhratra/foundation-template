# Stack Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template uses a carefully curated technology stack organized into three tiers: core (non-negotiable), supporting (recommended), and excluded (explicitly rejected). Every technology choice has a documented rationale. No technology is included without a reason; no technology is excluded without a reason.

## Specifications

### Core Stack (Non-Negotiable)

These technologies define the template's identity. They are decided and must not be substituted.

| Layer                  | Technology                  | Version                     | Why Chosen                                                                                                                                                                                                                                             |
| ---------------------- | --------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Backend Framework      | Django Ninja Extra          | Latest stable               | Class-based API controllers with automatic OpenAPI 3.1 spec generation from Pydantic schemas. Provides the type bridge between Python and TypeScript. Django's maturity for auth, ORM, admin, and migrations is unmatched.                             |
| Web Frontend           | Next.js 15+ (App Router)    | 15.x                        | Server Components, streaming SSR, file-based routing, middleware for auth guards. App Router is the recommended default.                                                                                                                               |
| Web UI Library         | Shadcn/ui                   | Latest                      | Copy-paste component library built on Radix UI primitives. Fully customizable, no vendor lock-in. Works with Tailwind CSS.                                                                                                                             |
| CSS Framework          | Tailwind CSS                | 3.4.x                       | Utility-first CSS. Co-located styling eliminates style drift. Native dark mode support. Integrates with Shadcn/ui. **Implementation Note:** Version 3.4 used instead of 4.x beta because Tailwind 4 preview plugin crashes Next.js PostCSS (Phase 04). |
| Mobile                 | React Native Expo (managed) | Expo SDK 52+                | Managed workflow eliminates native build complexity. Expo Router provides file-based routing. EAS Build for native binaries.                                                                                                                           |
| AI Orchestration       | LangGraph                   | Latest stable               | Graph-based agent workflows with state management, tool use, and checkpoint persistence. More structured than raw LangChain.                                                                                                                           |
| Vector Database        | PGVector                    | 0.7.x+                      | PostgreSQL extension for vector similarity search. HNSW indexing for approximate nearest neighbor. Avoids a separate vector database service.                                                                                                          |
| Authentication         | Django Allauth              | Latest stable               | Native Django auth with headless mode for SPA/API usage. Supports session cookies (web) and token-based auth (mobile). Extensible for social OAuth per-project.                                                                                        |
| ORM                    | Django ORM                  | (bundled with Django 5.1.x) | Mature, battle-tested. Migrations, querysets, select_related/prefetch_related. No reason to add SQLAlchemy or Prisma alongside Django.                                                                                                                 |
| Database               | PostgreSQL 16+              | 16.x                        | PGVector support, JSONB, excellent Django integration. The pgvector/pgvector Docker image includes the extension pre-installed.                                                                                                                        |
| JS Package Manager     | pnpm                        | 9.x                         | Strict dependency resolution, workspace support, faster than npm/yarn. Corepack-managed.                                                                                                                                                               |
| Python Package Manager | uv                          | Latest                      | 10-100x faster than pip. Built-in lockfile (uv.lock), virtual environment management. Same team as ruff (Astral).                                                                                                                                      |
| Monorepo Orchestrator  | Turborepo                   | 2.x                         | Task dependency graph, parallel execution, build caching. Manages JS/TS workspaces. Python participates via explicit inputs/outputs.                                                                                                                   |
| Backend Testing        | pytest                      | Latest stable               | Django test integration via pytest-django. Fixtures, parametrize, coverage via pytest-cov.                                                                                                                                                             |
| Frontend Testing       | vitest                      | Latest stable               | ESM-native, Vite-compatible, fast. Drop-in replacement for Jest with better DX. **Implementation Note:** Chosen for Next.js 15 compatibility over Jest (Phase 07).                                                                                     |
| Mobile E2E Testing     | Detox                       | Latest stable               | Gray-box E2E testing for React Native. Requires macOS runner. Run on merge to main only due to cost. **Implementation Note:** Template includes iOS-only configuration; Android can be added by users (Phase 07).                                      |

### Supporting Stack (Recommended)

These technologies fill specific gaps in the core stack. They are recommended but may be swapped with documented justification.

| Technology             | Version      | Purpose                                                  | Why This Over Alternatives                                                                                                                             |
| ---------------------- | ------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| openapi-typescript     | ^7.x         | Generate TypeScript types from Django Ninja OpenAPI spec | Pure type generation, no runtime code. Lightweight. Works with OpenAPI 3.0 and 3.1.                                                                    |
| openapi-fetch          | ^0.12.x      | Type-safe HTTP client using generated types              | Zero runtime overhead. Wraps native fetch with type inference. No code generation for the client.                                                      |
| Zod                    | ^3.x         | Runtime validation schemas shared across web and mobile  | TypeScript-first. z.infer<> for type extraction. Works identically in Next.js and Expo. Used by Shadcn/ui form patterns.                               |
| React Native Web       | ^0.19.x      | Run RN primitives in web browser                         | Enables shared UI primitive components (Text, View, Pressable) across platforms. Thin sharing layer only.                                              |
| ruff                   | ^0.8.x       | Python linter AND formatter                              | **Replaces black + flake8 + isort.** Single unified tool, 10-100x faster (written in Rust). Standard for Python projects in 2025+ (Phase 07).          |
| ESLint 9 (flat config) | ^9.x         | JS/TS linting                                            | Flat config (eslint.config.js) is the current standard. Composes well in monorepos.                                                                    |
| Prettier               | ^3.x         | Code formatting (JS/TS/JSON/MD)                          | Opinionated formatter. Run separately from ESLint (not via eslint-plugin-prettier).                                                                    |
| pre-commit             | ^4.x         | Git pre-commit hook framework                            | Orchestrates ruff (Python) and lint-staged (JS/TS) hooks. Standard for multi-language repos.                                                           |
| Docker Compose         | v2.x         | Multi-service local development                          | Infrastructure services (Postgres, Redis) in containers. Bundled with Docker Desktop.                                                                  |
| GitHub Actions         | N/A          | CI/CD pipeline                                           | Three parallel jobs (api, web, mobile). Free for public repos, generous free tier for private.                                                         |
| @tanstack/react-query  | ^5.x         | Data fetching and caching                                | Server state management. Works identically on web and mobile. Pairs with openapi-fetch for type-safe queries.                                          |
| react-hook-form        | ^7.x         | Form state management                                    | Lightweight, performant. Integrates with Zod via @hookform/resolvers. Used by Shadcn/ui form components.                                               |
| gunicorn               | ^22.x        | Production WSGI server                                   | Standard production server for Django. Never use manage.py runserver in production.                                                                    |
| django-cors-headers    | ^4.x         | CORS handling                                            | Required because Next.js runs on a different port/domain than Django API.                                                                              |
| django-environ         | ^0.11.x      | Environment variable management                          | Reads .env files for Django settings. Standard 12-factor app configuration.                                                                            |
| psycopg (psycopg3)     | ^3.x         | PostgreSQL adapter                                       | Modern adapter. Pure Python with optional C acceleration. Actively maintained. Replaces psycopg2.                                                      |
| whitenoise             | ^6.x         | Static file serving                                      | Serves Django static files in production without nginx/S3. Simplifies deployment.                                                                      |
| Celery                 | ^5.x         | Background task queue                                    | For async jobs (embedding generation, email sending, AI processing). Uses Redis as broker.                                                             |
| lint-staged            | Latest       | JS/TS pre-commit file processing                         | Runs ESLint + Prettier on staged JS/TS files. Called by pre-commit via local hook.                                                                     |
| TypeScript             | ^5.6+        | Type checking across JS/TS packages                      | Strict mode. tsc --noEmit for type-checking. Next.js and Expo use natively.                                                                            |
| mypy                   | ^1.x         | Python static type checking                              | Catches type errors in Django Ninja schemas. Use with django-stubs.                                                                                    |
| @hookform/resolvers    | ^3.x         | Connects react-hook-form to Zod                          | Enables zodResolver(schema) in form hooks. Bridges react-hook-form and Zod validation. Required by Shadcn/ui form patterns.                            |
| django-stubs           | ^5.x         | Django type stubs for mypy                               | Type annotations for Django models, querysets, settings. Required for effective mypy with Django projects.                                             |
| pytest-django          | ^4.x         | pytest plugin for Django                                 | Django test fixtures, database access, settings override. Standard backend testing integration.                                                        |
| pytest-cov             | ^5.x         | Test coverage reporting                                  | Generates coverage metrics for CI and local development. Used with `pytest --cov`.                                                                     |
| Redis                  | 7.x (Alpine) | Cache and task broker                                    | Celery broker, django-redis caching, optional session storage. Included in Docker Compose infrastructure. Cheap to include, avoids retrofitting later. |

### What NOT to Use (Explicitly Rejected)

| Technology                          | Why Rejected                                                                                         | Use Instead                                    |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| psycopg2-binary                     | Legacy adapter. Wheels cause issues in Docker. Not actively developed.                               | psycopg[binary] (psycopg3)                     |
| black + flake8 + isort              | Three tools where one (ruff) does everything faster. Unnecessary complexity.                         | ruff                                           |
| eslint-plugin-prettier              | Slow -- runs Prettier inside ESLint process. Defeats purpose of separate tools.                      | ESLint + Prettier as separate commands         |
| .eslintrc / .eslintrc.json          | Legacy ESLint config format, deprecated in ESLint 9.                                                 | eslint.config.js (flat config)                 |
| swagger-codegen / openapi-generator | Java-based, generates bloated SDKs, requires Java runtime. Over-engineered.                          | openapi-typescript + openapi-fetch             |
| axios                               | Adds unnecessary dependency. openapi-fetch wraps native fetch with type safety.                      | openapi-fetch (uses native fetch)              |
| dotenv (npm)                        | Next.js has built-in .env handling. Django uses django-environ. Redundant.                           | Built-in env handling per framework            |
| docker-compose v1 (standalone)      | Deprecated. Docker Desktop includes Compose v2 as docker compose.                                    | docker compose (v2)                            |
| pip (directly in CI/Docker)         | Slow, no lockfile, no built-in virtual environment management.                                       | uv                                             |
| Poetry                              | Slower than uv, heavier, less momentum in 2025+.                                                     | uv                                             |
| Yarn                                | pnpm is decided and non-negotiable. Yarn adds nothing pnpm does not provide.                         | pnpm                                           |
| Jest                                | vitest is faster, ESM-native, Vite-compatible. Jest's CJS-first model is outdated.                   | vitest                                         |
| Tamagui / NativeWind (in template)  | Adds cross-platform UI abstraction complexity. Let projects add if needed.                           | Raw react-native-web with thin primitives      |
| Solito                              | Navigation abstraction between Next.js and React Navigation. Adds coupling.                          | Keep navigation separate per platform          |
| orval                               | Generates React Query hooks -- couples API client to a specific data-fetching library.               | openapi-typescript + openapi-fetch (decoupled) |
| tRPC                                | Requires Node.js backend. Django is Python. tRPC is not compatible with this stack.                  | OpenAPI type generation pipeline               |
| Django REST Framework (DRF)         | Django Ninja Extra is faster, uses Pydantic for schemas, generates OpenAPI natively. DRF is heavier. | Django Ninja Extra                             |

### Version Compatibility Matrix

| Package        | Version  | Compatible With                    | Notes                                        |
| -------------- | -------- | ---------------------------------- | -------------------------------------------- |
| Next.js        | 15.x     | React 19.x, React DOM 19.x         | App Router is default and recommended        |
| React          | 19.x     | React Native 0.76+                 | React 19 brings Server Components (web only) |
| React Native   | 0.76.x+  | Expo SDK 52+                       | New Architecture enabled by default          |
| Expo SDK       | 52.x+    | React Native 0.76.x+               | Managed workflow, EAS Build for native       |
| TypeScript     | 5.6+     | All JS/TS packages                 | Strict mode recommended                      |
| Node.js        | 20.x LTS | pnpm 9.x, turbo 2.x                | LTS for stability in CI                      |
| Python         | 3.12.x   | Django 5.x, ruff, mypy             | 3.12 for performance improvements            |
| Django         | 5.1.x    | django-ninja-extra, django-allauth | Stable, well-supported                       |
| PostgreSQL     | 16.x     | PGVector 0.7.x+                    | HNSW indexing available in 0.5+              |
| pnpm           | 9.x      | Node 20+, turbo 2.x                | Corepack-managed                             |
| Turborepo      | 2.x      | pnpm workspaces                    | Major rewrite from v1, better performance    |
| Docker Compose | v2.x     | Docker Desktop                     | Bundled with Docker Desktop                  |
| Redis          | 7.x      | Celery 5.x, django-redis           | Alpine variant for smaller images            |

## Constraints

1. **Core stack is non-negotiable.** Changing any core technology requires a new template, not a modification to this one.
2. **All versions must be pinned.** No `latest` tags in package.json or pyproject.toml. Pin to specific minor versions.
3. **Version verification required.** All versions listed are based on research data through May 2025. Run `npm view <package> version` and `pip index versions <package>` before implementation to get current versions.
4. **No dual-purpose tools.** Each tool serves one purpose. If two tools overlap (e.g., black and ruff for formatting), keep only one.
5. **Rejected technologies must not appear in any dependency file.** If psycopg2-binary, axios, or any rejected technology appears in requirements.txt, pyproject.toml, or package.json, the build should fail.

## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
