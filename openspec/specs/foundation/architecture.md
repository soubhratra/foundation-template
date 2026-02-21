# Architecture Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The Foundation Template is a Turborepo monorepo with a backend-heavy, thin-frontend architecture. Django owns all business logic, auth, and data persistence. Next.js and Expo are rendering layers consuming a type-safe API. The integration layer is the OpenAPI-to-TypeScript type generation pipeline, which ensures compile-time type safety across the Python-TypeScript boundary.

## Specifications

### System Overview Diagram

```
                              CLIENTS
  +--------------------+  +--------------------+  +------------------+
  |   Next.js 15       |  |   Expo Mobile      |  |  Third-Party     |
  |   (App Router)     |  |   (iOS/Android)    |  |  API Consumers   |
  |   SSR + CSR        |  |   Managed Flow     |  |                  |
  +--------+-----------+  +--------+-----------+  +--------+---------+
           |                       |                       |
           |  +--------------------------------------------+
           |  |        SHARED PACKAGES (TypeScript)        |
           |  |  api-client | schemas | ui-primitives      |
           |  |  business-logic | config-eslint | config-ts|
           |  +--------------------------------------------+
           |                       |                       |
           v                       v                       v
  +----------------------------------------------------------------+
  |                    Django Ninja Extra API                        |
  |              (REST + OpenAPI 3.1 spec generation)               |
  |  +----------+  +----------+  +---------+  +-----------------+  |
  |  |  Auth    |  |  Core    |  | Health  |  |  AI Module      |  |
  |  | (Allauth)|  |  CRUD    |  | Check   |  | (LangGraph)     |  |
  |  +----------+  +----------+  +---------+  +-----------------+  |
  +----------------------------------------------------------------+
  |                     Django ORM Layer                             |
  +----------------------------------------------------------------+
  |            PostgreSQL 16+ with PGVector Extension               |
  +----------------------------------------------------------------+
```

### Monorepo Directory Structure

```
foundation-template/
+-- apps/
|   +-- web/                          # Next.js 15 App Router
|   |   +-- app/                      # App Router pages and layouts
|   |   |   +-- (auth)/               # Auth route group (login, signup, etc.)
|   |   |   +-- (dashboard)/          # Authenticated route group
|   |   |   +-- api/                  # Next.js API routes (BFF proxy only)
|   |   |   +-- layout.tsx            # Root layout
|   |   |   +-- page.tsx              # Landing page
|   |   +-- components/               # Web-specific UI components
|   |   +-- lib/                      # Web-specific utilities
|   |   +-- middleware.ts             # Auth middleware (cookie validation)
|   |   +-- next.config.ts            # Next.js config (RNW transpile)
|   |   +-- tailwind.config.ts        # Tailwind configuration
|   |   +-- tsconfig.json             # Extends @repo/config-ts
|   |   +-- package.json              # @repo/web
|   |
|   +-- mobile/                       # Expo React Native app
|   |   +-- app/                      # Expo Router file-based routing
|   |   |   +-- (auth)/               # Auth screens
|   |   |   +-- (tabs)/               # Tab navigation
|   |   |   +-- _layout.tsx           # Root layout
|   |   +-- components/               # Mobile-specific components
|   |   +-- lib/                      # Mobile-specific utilities
|   |   +-- metro.config.js           # Metro bundler (monorepo resolution)
|   |   +-- app.json                  # Expo config
|   |   +-- tsconfig.json
|   |   +-- package.json              # @repo/mobile
|   |
|   +-- api/                          # Django Ninja Extra project
|       +-- manage.py
|       +-- pyproject.toml            # Python dependencies (uv)
|       +-- uv.lock                   # Python lockfile
|       +-- config/                   # Django project settings
|       |   +-- __init__.py
|       |   +-- settings/
|       |   |   +-- __init__.py
|       |   |   +-- base.py           # Shared settings
|       |   |   +-- development.py    # Dev overrides
|       |   |   +-- production.py     # Production overrides
|       |   +-- urls.py
|       |   +-- wsgi.py
|       |   +-- asgi.py
|       +-- apps/                     # Django applications
|       |   +-- accounts/             # Custom user model + auth
|       |   |   +-- models.py
|       |   |   +-- schemas.py        # Pydantic schemas
|       |   |   +-- controllers.py    # Ninja Extra controllers
|       |   |   +-- services.py       # Business logic
|       |   |   +-- admin.py
|       |   |   +-- tests/
|       |   +-- core/                 # Shared Django utilities
|       |   |   +-- models.py         # Base model mixins
|       |   |   +-- schemas.py        # Common Pydantic schemas
|       |   |   +-- exceptions.py     # Custom exceptions
|       |   +-- ai/                   # LangGraph module (removable)
|       |       +-- graphs/           # LangGraph graph definitions
|       |       +-- models.py         # Embedding models
|       |       +-- controllers.py
|       |       +-- schemas.py
|       |       +-- services.py
|       |       +-- tasks.py          # Celery tasks for embeddings
|       +-- tests/                    # Project-level test config
|       +-- Dockerfile
|       +-- package.json              # Minimal (turbo task registration only)
|
+-- packages/
|   +-- api-client/                   # Auto-generated typed API client
|   |   +-- src/
|   |   |   +-- types.d.ts           # Generated by openapi-typescript (DO NOT EDIT)
|   |   |   +-- client.ts            # openapi-fetch client instance
|   |   |   +-- index.ts             # Re-exports
|   |   +-- openapi.json             # Cached OpenAPI spec (committed)
|   |   +-- package.json             # @repo/api-client
|   |
|   +-- schemas/                      # Shared Zod validation schemas
|   |   +-- src/
|   |   |   +-- auth.ts              # Login, signup, password reset
|   |   |   +-- user.ts              # User profile
|   |   |   +-- common.ts            # Shared primitives (email, password)
|   |   |   +-- index.ts
|   |   +-- package.json             # @repo/schemas
|   |
|   +-- ui-primitives/               # React Native Web shared components
|   |   +-- src/
|   |   |   +-- button.tsx
|   |   |   +-- text-input.tsx
|   |   |   +-- card.tsx
|   |   |   +-- typography.tsx
|   |   |   +-- loading.tsx
|   |   |   +-- index.ts
|   |   +-- package.json             # @repo/ui-primitives
|   |
|   +-- config-eslint/               # Shared ESLint flat config
|   |   +-- index.js                 # Base config
|   |   +-- next.js                  # Next.js-specific
|   |   +-- react-native.js          # React Native-specific
|   |   +-- package.json             # @repo/config-eslint
|   |
|   +-- config-ts/                   # Shared TypeScript configs
|       +-- base.json                # Shared strict settings
|       +-- nextjs.json              # Next.js extends base
|       +-- react-native.json        # React Native extends base
|       +-- library.json             # Shared packages extends base
|       +-- package.json             # @repo/config-ts
|
+-- tooling/                        # Build tools, scripts (NOT a turbo workspace)
|   +-- scripts/
|   |   +-- generate-api-client.sh  # Fetch OpenAPI spec + generate client
|   |   +-- setup.sh                # First-time project setup
|   +-- docker/
|       +-- nginx.conf              # Reverse proxy config (optional)
|
+-- docker-compose.yml               # Local dev (infra services only)
+-- docker-compose.full.yml          # Full Docker dev (all services)
+-- docker-compose.prod.yml          # Production overrides (multi-stage targets)
+-- turbo.json                       # Turborepo pipeline config
+-- package.json                     # Root workspace config
+-- pnpm-workspace.yaml              # pnpm workspace definition
+-- ruff.toml                        # Python linting config (repo root)
+-- .pre-commit-config.yaml          # Pre-commit hooks
+-- .env.example                     # Root env template
+-- .github/
|   +-- workflows/
|       +-- ci.yml                   # CI pipeline (3 parallel jobs)
+-- .gitignore
```

### Structure Rationale

| Directory                   | Rationale                                                                                                                                          |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/`                     | Deployable applications. Turborepo convention. Each app has its own build process and server.                                                      |
| `apps/api/`                 | Django project. NOT a pnpm workspace. Python dependencies managed by uv. Participates in Turborepo via minimal package.json for task registration. |
| `packages/`                 | Shared libraries consumed by apps. Not independently deployable.                                                                                   |
| `packages/api-client/`      | Auto-generated types live in committed file. Custom wrappers and re-exports are stable across regeneration.                                        |
| `packages/config-*`         | Shared configurations prevent drift between apps. Each app extends rather than duplicates.                                                         |
| `apps/api/config/settings/` | Split settings pattern (base/development/production) selected via DJANGO_SETTINGS_MODULE env var.                                                  |
| `apps/api/apps/`            | Django applications follow controllers/services/models layered pattern.                                                                            |
| `apps/api/apps/ai/`         | AI module is fully isolated. All AI code lives here. Removable without affecting other apps.                                                       |
| `tooling/`                  | Not a Turborepo workspace. Scripts and Dockerfiles supporting development. Keeps the root clean.                                                   |

### Component Responsibilities

| Component              | Responsibility                                                                     | Does NOT Do                                              |
| ---------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| Django Ninja Extra API | All business logic, auth, data persistence, OpenAPI spec generation                | Serve HTML, manage JS/TS dependencies                    |
| Next.js Web App        | Web UI rendering, SSR/SSG, SEO, auth middleware (cookie validation)                | Business logic, direct database access                   |
| Expo Mobile App        | iOS/Android native experience, push notifications, device APIs                     | Business logic, session cookie auth                      |
| @repo/api-client       | Type-safe HTTP client, auto-generated types                                        | Business logic, validation                               |
| @repo/schemas          | Cross-platform input validation (Zod)                                              | API communication, UI rendering                          |
| @repo/ui-primitives    | Foundational cross-platform UI components (Button, Text, Input)                    | Navigation, complex layouts, animations                  |
| @repo/business-logic   | Platform-agnostic React hooks (useAuth, useUser), utilities, constants, formatters | UI rendering, direct API calls (delegates to api-client) |
| @repo/config-eslint    | Shared ESLint configurations                                                       | Runtime code                                             |
| @repo/config-ts        | Shared TypeScript configurations                                                   | Runtime code                                             |
| PostgreSQL + PGVector  | Relational data storage, vector embeddings                                         | Application logic                                        |
| Redis                  | Celery task broker, django-redis caching, optional session storage                 | Business logic, data persistence                         |

### Package Dependency Graph

```
                    +---------------+
                    | config-eslint |   (no monorepo deps)
                    | config-ts     |
                    +---------------+
                          ^
        +-----------------+-----------------+
        |                 |                 |
  +----------+     +-----------+     +------------+
  | schemas  |     |    ui-    |     | api-client |
  | (zod)    |     | primitives|     | (generated)|
  +----+-----+     +-----------+     +-----+------+
       |                                    |
       +------------------------------------+
                         |
                  +------+-------+
                  | business-    |
                  | logic        |
                  | (hooks, etc) |
                  +------+-------+
                         |
              +----------+----------+
              |                     |
        +-----+-----+       +------+-----+
        |    web    |       |   mobile   |
        | (Next.js) |       |   (Expo)   |
        +-----------+       +------------+
```

**Dependency rules:**

- config-eslint, config-ts: No monorepo dependencies. Foundation layer.
- schemas: No monorepo dependencies. Pure Zod schemas.
- ui-primitives: No monorepo dependencies. Pure React Native Web primitives.
- api-client: Depends on schemas (imports Zod schemas for request validation).
- business-logic: Depends on api-client (uses typed client) and schemas (uses validation). Contains React hooks, utility functions. This is the primary code-sharing layer.
- web and mobile: Depend on all packages they need directly. Composition layer.
- No package-to-package chains longer than one hop.

### Workspace Configuration Patterns

#### Config Packages in Root devDependencies

**Pattern:** Link `@repo/config-*` packages in root `package.json` devDependencies.

**Rationale:**

- Allows Node.js and TypeScript module resolution to find config packages
- Enables config verification commands at root level
- Required for ESLint and TypeScript to resolve shared configurations

**Implementation:**

```json
// Root package.json
{
  "devDependencies": {
    "@repo/config-eslint": "workspace:*",
    "@repo/config-ts": "workspace:*",
    "typescript": "^5.6.0",
    "eslint": "^9.0.0"
  }
}
```

**Decision:** Phase 01

#### Root ESLint Configuration

**Location:** `eslint.config.js` at repository root
**Rationale:** lint-staged runs from root and needs config for package-level discovery.

**Pattern:**

```javascript
// eslint.config.js (root)
import baseConfig from "@repo/config-eslint";

export default [...baseConfig];
```

**Note:** Individual packages can extend this with package-specific rules.

**Decision:** Phase 08-cli-scaffolder

#### Expo Type Environment Alignment

**Issue:** TypeScript ReactNode mismatch between Expo (React Native) and web packages.
**Impact:** Metro type-check fails with incompatible React type definitions.

**Solution:** Align `@types/react` versions across all packages to React 19 definitions.

**Configuration:**

```json
// apps/mobile/package.json
{
  "devDependencies": {
    "@types/react": "~19.0.0", // Match web packages
    "react": "19.0.0",
    "react-native": "0.76.x"
  }
}
```

**Decision:** Phase 03

#### pnpm node-linker=hoisted

**What:** `.npmrc` at repo root must contain:

```
node-linker=hoisted
```

**Why:** pnpm's default symlink strategy creates a virtual store layout where packages are symlinked rather than physically present in `node_modules/`. Metro bundler (Expo) cannot follow these symlinks during bundle resolution — it silently fails to find `@repo/*` workspace packages, producing confusing "cannot find module" errors at bundle time that don't appear in Next.js (which uses webpack and handles symlinks correctly).

The hoisted layout physically copies all packages into `node_modules/` at the workspace root, which Metro can resolve without special configuration.

**Rejected alternative:** pnpm default symlink strategy — works for Next.js and Node.js tools but silently breaks Metro. The failure is non-obvious because Next.js builds succeed while only the Expo bundler is affected.

**Decision:** Phase 01 (Monorepo Foundation)

#### Metro Workspace Package Resolution

**Issue:** Expo bundler needs explicit alias to resolve `@repo/*` workspace packages.
**Impact:** Without alias, Metro cannot find `@repo/api-client` and other shared packages.

**Solution:** Add Metro alias for workspace packages.

**Configuration:**

```javascript
// apps/mobile/metro.config.js
const { getDefaultConfig } = require("expo/metro-config");
const path = require("path");

const config = getDefaultConfig(__dirname);

config.watchFolders = [path.resolve(__dirname, "../..")];

config.resolver.nodeModulesPaths = [
  path.resolve(__dirname, "node_modules"),
  path.resolve(__dirname, "../../node_modules"),
];

// Workspace package aliases
config.resolver.extraNodeModules = {
  "@repo/api-client": path.resolve(__dirname, "../../packages/api-client"),
  "@repo/validation": path.resolve(__dirname, "../../packages/validation"),
  "@repo/ui": path.resolve(__dirname, "../../packages/ui"),
  "@repo/business-logic": path.resolve(__dirname, "../../packages/business-logic"),
};

module.exports = config;
```

**Decision:** Phase 05-mobile-application

### Centralization Patterns

#### API Base URL Helper

**Location:** `apps/web/app/base-url.ts` (or similar)
**Purpose:** Centralize API base URL construction for server and client components.

**Pattern:**

```typescript
// apps/web/app/base-url.ts
export function buildApiBaseUrl(request?: Request): string {
  // Server-side: use internal URL
  if (typeof window === "undefined") {
    return process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  }
  // Client-side: use public URL
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}
```

**Benefit:** Layouts and routes reuse without duplicating logic.
**Decision:** Phase 04-web-application

#### CSRF-Aware API Helper

**Location:** `apps/web/lib/postJson.ts` (or similar)
**Purpose:** Centralize CSRF token handling for Django headless API mutations.

**Pattern:**

```typescript
// apps/web/lib/postJson.ts
function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : null;
}

export async function postJson(url: string, body: any) {
  return fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken() ?? "",
    },
    credentials: "include",
    body: JSON.stringify(body),
  });
}
```

**Benefit:** Every auth mutation shares the same Django headless request wiring.
**Decision:** Phase 04-web-application

### Build Order (Phase Dependency Chain)

```
Phase 1: Monorepo Foundation
  +-- 1a. Root scaffolding (turbo.json, pnpm-workspace.yaml, package.json)
  +-- 1b. packages/config-eslint, packages/config-ts
  +-- 1c. Docker Compose (db, redis -- infrastructure only)
  +-- 1d. apps/api scaffolding (Django project, settings, CUSTOM USER MODEL)
          CRITICAL: Custom user model MUST exist before first migration.

Phase 2: API Core + Auth
  +-- 2a. Django Ninja Extra setup (api.py, router registration)
  +-- 2b. Django Allauth headless mode (auth endpoints)
  +-- 2c. OpenAPI schema export (management command)
  +-- 2d. Health check endpoint
  Requires: Phase 1 complete

Phase 3: Shared Packages + Type Generation
  +-- 3a. packages/api-client (type generation pipeline)
  +-- 3b. packages/schemas (Zod schemas matching Pydantic models)
  +-- 3c. packages/ui-primitives (React Native Web components)
  Requires: Phase 2 (API running with endpoints)

Phase 4: Web Application
  +-- 4a. apps/web scaffolding (Next.js 15 App Router)
  +-- 4b. React Native Web integration in next.config.ts
  +-- 4c. Auth flow (middleware, login/signup pages)
  +-- 4d. Dashboard shell with Shadcn/ui
  Requires: Phase 3 (shared packages exist)

Phase 5: Mobile Application
  +-- 5a. apps/mobile scaffolding (Expo managed workflow)
  +-- 5b. Metro config for monorepo package resolution
  +-- 5c. Auth flow (expo-secure-store, JWT management)
  +-- 5d. Screens consuming shared packages
  Requires: Phase 3 (shared packages exist)
  Can run in parallel with Phase 4

Phase 6: AI Module (Optional)
  +-- 6a. PGVector setup (extension, model mixin, HNSW index)
  +-- 6b. LangGraph graph definitions
  +-- 6c. Embedding pipeline (Celery tasks)
  +-- 6d. AI API endpoints + frontend UI
  Requires: Phase 2 (API exists)
  Orthogonal to Phases 4/5

Phase 7: DevEx + CI/CD
  +-- 7a. GitHub Actions (3 parallel jobs: api, web, mobile)
  +-- 7b. Pre-commit hooks (ruff, lint-staged)
  +-- 7c. Production Dockerfiles (multi-stage)
  Incremental -- can build alongside other phases

Phase 8: CLI Scaffolder
  +-- MUST be built LAST after template is stable
```

**Critical path:** Phase 1 -> Phase 2 -> Phase 3 -> Phase 4/5 (parallel) -> Phase 7

### Turborepo Pipeline Configuration

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true,
      "dependsOn": ["^build"]
    },
    "lint": {
      "dependsOn": ["^build"]
    },
    "test": {
      "dependsOn": ["^build"]
    },
    "type-check": {
      "dependsOn": ["^build"]
    },
    "generate:api-types": {
      "cache": false,
      "inputs": ["../../apps/api/**/*.py"],
      "outputs": ["src/types.d.ts"]
    },
    "clean": {
      "cache": false
    }
  }
}
```

**Python task integration:** Django tasks are registered via a minimal package.json in apps/api/ that delegates to Python tooling:

```json
{
  "name": "@repo/api",
  "private": true,
  "scripts": {
    "lint": "ruff check .",
    "test": "pytest",
    "type-check": "mypy .",
    "export-schema": "python manage.py export_openapi_schema > ../../packages/api-client/openapi.json"
  }
}
```

### pnpm Workspace Configuration

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
  # NOTE: apps/api is a pnpm workspace for Turborepo task orchestration only.
  # It has NO JS/TS dependencies. Python dependencies managed by uv/pyproject.toml.
  # The package.json in apps/api/ exists solely to register scripts (dev, lint, test)
  # so that `turbo dev` can start Django alongside Next.js and Expo.
```

### Docker Compose Service Architecture (Hybrid Dev)

The default development model is **hybrid**: infrastructure services run in Docker, application code runs on the host.

```yaml
# docker-compose.yml -- Infrastructure only (default dev)
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

**Why hybrid:**

- File watching and hot reload work natively on host (no Docker VM filesystem latency)
- pnpm/node_modules stay on host (no platform binary mismatches)
- IDE autocomplete works without Docker volume indirection
- Expo dev server needs USB/network access to physical devices

**Expo stays on host always.** Even in full Docker mode, Expo cannot be containerized (Metro bundler needs host network and device access).

### Scaling Considerations

| Concern         | 100 users                         | 10K users                                          | 100K+ users                                                   |
| --------------- | --------------------------------- | -------------------------------------------------- | ------------------------------------------------------------- |
| API             | Single Django process (runserver) | Gunicorn 4-8 workers behind nginx                  | Horizontal scaling: multiple Django pods behind load balancer |
| Database        | Single Postgres instance          | Connection pooling (PgBouncer), query optimization | Read replicas, partitioning, HNSW index tuning                |
| Background jobs | No worker needed                  | Celery with Redis broker, 2-4 workers              | Dedicated Celery queues, autoscaling workers                  |
| Frontend        | Vercel free tier or single VPS    | Vercel Pro or self-hosted with CDN                 | Edge functions, ISR, regional deployment                      |
| AI/Embeddings   | Synchronous generation            | Async via Celery, batch processing                 | Dedicated embedding worker, pre-computed results              |

**What breaks first:**

1. Database connections (Django default: new connection per request; Postgres default limit: 100)
2. Long-running AI requests (LLM calls take 5-30s, block Django workers)
3. OpenAPI spec size (grows with API surface; split modules if needed)

### Authentication Architecture

**Strategy: Session-based for web, JWT for mobile.**

| Platform      | Auth Mechanism              | Token Storage                  | Refresh Strategy                                                  |
| ------------- | --------------------------- | ------------------------------ | ----------------------------------------------------------------- |
| Web (Next.js) | Session cookies (httpOnly)  | Browser cookie (set by Django) | Django session middleware handles refresh                         |
| Mobile (Expo) | JWT access + refresh tokens | expo-secure-store              | api-client interceptor detects 401, POST /api/auth/refresh, retry |

**Why dual-mode auth:**

- **Web (Session/Cookie):** Django Allauth naturally provides session-based auth. httpOnly cookies are more secure than storing JWTs in browser localStorage. Next.js middleware can read the session cookie for server-side auth checks without exposing tokens to client JavaScript.
- **Mobile (JWT):** Mobile apps cannot use cookies effectively. JWT access + refresh token pair stored in expo-secure-store (hardware-backed secure storage). The api-client package includes an interceptor for transparent token refresh.
- **Django Allauth** supports both flows. The headless mode provides token-based endpoints alongside session-based auth. `django-ninja-jwt` can be added for JWT-specific support with Django Ninja.

**Auth flow:**

```
Web: Browser -> httpOnly cookie -> Next.js middleware validates -> proxies to Django with cookie
Mobile: App -> expo-secure-store token -> Authorization: Bearer header -> Django validates JWT
```

## Constraints

1. **Backend owns all business logic.** Next.js API routes are BFF thin proxies only: auth cookie translation, webhook receivers, server-side data fetching. Never business logic.
2. **Django is a pnpm workspace for task orchestration only.** Python dependencies managed by uv. `apps/api/package.json` has no JS/TS dependencies — it exists solely to register scripts (`dev`, `lint`, `test`, `type-check`) so Turborepo can orchestrate them alongside JS/TS tasks.

   **What breaks if you treat it as a real JS workspace:** Turborepo hashes package.json dependency graphs for cache invalidation. A Django app with no JS dependencies appears to Turborepo as a package whose inputs never change. Result: CI caches never hit (Turborepo reports MISS every run), or the inverse — Turborepo incorrectly caches Python tasks and skips re-running tests after code changes. The fix is explicit `inputs` globs in `turbo.json` covering `**/*.py` files, which bypasses Turborepo's dependency graph for Python tasks.

3. **Custom user model before first migration.** apps/api/apps/accounts/models.py must define a custom AbstractUser subclass. AUTH_USER_MODEL must be set before `python manage.py migrate` is ever run. Recovery cost for missing this is HIGH.
4. **Package dependency depth limit: 1 hop.** No package depends on another package that depends on another package. Apps depend on packages directly. Prevents circular dependencies and build cascade.
5. **Expo never in Docker.** Even in docker-compose.full.yml, Expo is excluded. Metro bundler runs on host.
6. **AI module must be cleanly removable.** All AI code in apps/api/apps/ai/. No AI imports in non-AI Django apps. No AI dependencies in root requirements unless conditional.

## References

- `.planning/research/ARCHITECTURE.md` -- Full architecture research with data flow diagrams
- `.planning/research/PITFALLS.md` -- Turborepo/Docker/Metro pitfalls and mitigations
- `.planning/research/STACK.md` -- Technology choices and configuration patterns
