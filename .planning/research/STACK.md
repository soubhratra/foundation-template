# Stack Research: Foundation Template Supporting Stack

**Domain:** Full-stack SaaS starter template (monorepo)
**Researched:** 2026-02-08
**Confidence:** MEDIUM (versions based on training data through May 2025; all version numbers flagged for verification before implementation)

> **IMPORTANT:** This document does NOT question or research the core stack decisions (Django Ninja Extra, Next.js 15+, Expo, LangGraph, etc.). Those are decided and non-negotiable. This research covers the **supporting libraries, tooling, configuration patterns, and integration techniques** that make the decided stack work together cohesively.

---

## Core Stack (DECIDED -- Not Researched)

Listed for reference only. These are non-negotiable.

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Django Ninja Extra (Python) | API framework |
| Frontend | Next.js 15+ (App Router) + Shadcn/ui + Tailwind CSS | Web UI |
| Mobile | React Native + Expo (managed workflow) | Mobile apps |
| AI | LangGraph + PGVector | Agent orchestration + embeddings |
| Auth | Django Allauth | Native Django auth |
| ORM | Django ORM | With django-ninja-extra schemas |
| Database | Postgres 16+ with PGVector | Primary data store |
| JS Package Manager | pnpm | JS/TS workspace management |
| Python Package Manager | uv / pip | Python dependency management |
| Monorepo | Turborepo | Build orchestration |
| Testing | pytest, vitest, detox | Backend, frontend, mobile |

---

## Recommended Supporting Stack

### 1. OpenAPI-to-TypeScript Type Generation

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| openapi-typescript | ^7.x | Generate TypeScript types from Django Ninja OpenAPI spec | The de facto standard for OpenAPI 3.x to TypeScript type generation. Produces pure types (no runtime code), which is exactly what we want -- a lightweight type layer, not a heavy SDK. Works with OpenAPI 3.0 and 3.1. Django Ninja natively exports OpenAPI 3.0 spec. | MEDIUM |
| openapi-fetch | ^0.12.x | Type-safe HTTP client built on generated types | Companion to openapi-typescript. Uses the generated types to provide a type-safe `fetch` wrapper with zero runtime overhead. No code generation for the client itself -- just wraps native `fetch` with type inference. This replaces hand-written API client code entirely. | MEDIUM |

**How it works:**
1. Django Ninja Extra auto-generates `openapi.json` at runtime (e.g., `/api/openapi.json`)
2. `openapi-typescript` CLI reads that spec and generates TypeScript types (e.g., `api-types.d.ts`)
3. `openapi-fetch` uses those types for type-safe API calls in Next.js and React Native
4. A turborepo script regenerates types on demand or in CI

**Pattern:**
```bash
# In packages/api-client/package.json scripts:
"generate:types": "openapi-typescript http://localhost:8000/api/openapi.json -o ./src/types.d.ts"
```

**Alternative considered and rejected:**

| Alternative | Why Not |
|-------------|---------|
| openapi-generator (Java-based) | Generates bloated SDK code, requires Java runtime, over-engineered for our needs |
| orval | More opinionated, generates React Query hooks -- couples your API client to a specific data-fetching library |
| swagger-typescript-api | Less maintained, generates runtime code we don't need |
| Manual type definitions | Defeats the purpose; types drift from API, no single source of truth |

---

### 2. Shared Validation: Zod

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| zod | ^3.x | Runtime validation schemas shared across web + mobile | Standard TypeScript-first validation library. Used by Shadcn/ui form patterns, works identically in Next.js and React Native. Schemas double as TypeScript types via `z.infer<>`. | MEDIUM |

**Pattern:** Zod schemas live in a shared monorepo package (`packages/schemas/`) and are imported by both Next.js and Expo apps. Backend validation stays in Django (Pydantic via ninja schemas), but Zod handles client-side form validation and response parsing.

**Why not share Pydantic schemas directly:**
- Pydantic is Python-only; cannot run in browser/mobile
- The OpenAPI spec is the bridge: Django Pydantic/ninja schemas -> OpenAPI -> TypeScript types
- Zod adds client-side validation on top of those types

---

### 3. React Native Web (Shared UI Primitives)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| react-native-web | ^0.19.x | Run React Native components in web browser | Enables shared UI primitive components (Text, View, Pressable, etc.) across Next.js and Expo in the monorepo. This is how `packages/ui-primitives/` works -- write once with RN primitives, render on both platforms. | MEDIUM |

**Scope of sharing:** Share primitive components (buttons, inputs, text, layout) and hooks. Do NOT try to share complex UI -- Shadcn/ui handles web-specific design, Expo handles mobile-specific patterns. The shared layer is intentionally thin.

**What to share via RN Web:**
- Basic UI atoms: Button, TextInput, Card wrappers, Loading states
- Layout primitives: Stack, Row, Spacer
- Typography: Heading, Body, Caption

**What NOT to share:**
- Navigation (Next.js router vs React Navigation are fundamentally different)
- Complex forms (web uses Shadcn/ui form components, mobile uses native inputs)
- Responsive layouts (approaches differ significantly between web and mobile)

**Integration with Next.js:**
Next.js needs webpack/turbopack alias configuration to resolve `react-native` imports to `react-native-web`. This is a well-documented pattern but requires explicit configuration in `next.config.js`:

```javascript
// next.config.js
const { withExpo } = require("@expo/next-adapter");
module.exports = withExpo({
  transpilePackages: ["react-native-web", "@project/ui-primitives"],
  // ... other config
});
```

**Alternative considered:** Tamagui, NativeWind, or Solito for cross-platform UI. These add more abstraction but also more complexity. For a template, raw `react-native-web` with thin primitives is simpler and more transparent. Each project can add Tamagui later if desired.

---

### 4. Docker Compose Configuration

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Docker Compose | v2.x (Docker Desktop bundled) | Multi-service local development | Single `docker compose up` runs all services. Docker Compose v2 is the standard (v1 standalone binary is deprecated). | HIGH |

**Service architecture:**

```yaml
# docker-compose.yml
services:
  db:
    image: pgvector/pgvector:pg16
    # Provides Postgres 16 with PGVector extension pre-installed
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

  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    ports: ["8000:8000"]
    volumes:
      - ./apps/api:/app  # Hot reload via volume mount
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://foundation:foundation@db:5432/foundation
    command: python manage.py runserver 0.0.0.0:8000

  web:
    build:
      context: .
      dockerfile: apps/web/Dockerfile
    ports: ["3000:3000"]
    volumes:
      - ./apps/web:/app
      - ./packages:/packages  # Shared packages accessible
    depends_on: [api]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000

  # NOTE: Expo dev server runs on host, not in Docker
  # Reason: Expo needs USB/network access to physical devices
  # and the Metro bundler works best on the host machine

volumes:
  postgres_data:
```

**Critical pattern -- Expo stays on host:**
Do NOT containerize the Expo dev server. Mobile development requires direct USB access to devices, network access for Expo Go, and the Metro bundler performs significantly better on the host. The Expo app connects to the containerized API via `http://localhost:8000` (or host IP on physical devices).

**Docker image choices:**

| Image | Why |
|-------|-----|
| `pgvector/pgvector:pg16` | Official PGVector image based on Postgres 16. Includes the extension pre-installed. Do NOT use plain `postgres:16` and install PGVector manually -- it adds build complexity for no benefit. |
| Python base: `python:3.12-slim` | Slim variant reduces image size. Pin Python version to match local dev. |
| Node base: `node:20-slim` | LTS version. Matches pnpm compatibility. |

**Dockerfile patterns:**

For the Django API, use a multi-stage build:
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

For the Next.js web app:
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

---

### 5. Turborepo Configuration

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| turbo | ^2.x | Monorepo build orchestration and caching | Handles task dependencies, parallel builds, and remote caching. The Python backend is managed alongside but NOT as a turbo workspace (Python has its own dependency management). | MEDIUM |

**Workspace structure:**

```
foundation-template/
  turbo.json
  pnpm-workspace.yaml
  package.json
  apps/
    web/          # Next.js 15+ (pnpm workspace)
    mobile/       # Expo React Native (pnpm workspace)
    api/          # Django Ninja Extra (NOT a pnpm workspace)
  packages/
    api-client/   # openapi-typescript types + openapi-fetch client
    schemas/      # Zod validation schemas
    ui-primitives/# React Native Web shared components
    config-eslint/# Shared ESLint configuration
    config-ts/    # Shared TypeScript configuration
```

**pnpm-workspace.yaml:**
```yaml
packages:
  - "apps/web"
  - "apps/mobile"
  - "packages/*"
  # NOTE: apps/api is NOT listed -- Python, managed by uv/pip
```

**turbo.json:**
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
      "persistent": true
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
    }
  }
}
```

**Critical pattern -- Python backend is NOT a turbo workspace:**
Turborepo manages JS/TS workspaces via pnpm. The Django API lives in `apps/api/` but is not a pnpm workspace. Python tasks (lint, test, migrations) are orchestrated via:
1. Docker Compose for the runtime
2. A root-level `Makefile` or scripts for Python-specific tasks
3. Optionally, turbo can invoke Python tasks via root `package.json` scripts that shell out

**Root package.json scripts pattern:**
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

---

### 6. Code Quality Tooling

#### Python (Backend)

| Tool | Version | Purpose | Why Recommended | Confidence |
|------|---------|---------|-----------------|------------|
| ruff | ^0.8.x | Python linter AND formatter (replaces flake8 + black + isort) | Single tool for all Python code quality. 10-100x faster than alternatives (written in Rust). Handles linting, formatting, and import sorting. No reason to use flake8, black, or isort separately anymore. | MEDIUM |
| mypy | ^1.x | Python static type checking | Django Ninja Extra uses type annotations for schema generation; mypy catches type errors. Use `django-stubs` for Django-specific type checking. | MEDIUM |
| pre-commit | ^4.x | Git pre-commit hook framework | Runs ruff, mypy, eslint, prettier on staged files before commit. The standard for multi-language repos. | MEDIUM |

**ruff.toml (at repo root):**
```toml
[lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "SIM", "TCH"]
ignore = ["E501"]  # Line length handled by formatter

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

**Why NOT black + flake8 + isort:**
Ruff replaces all three with a single, dramatically faster tool. Black and flake8 are mature but slow. In a pre-commit hook that runs on every commit, speed matters. Ruff is the industry standard for new Python projects as of 2025.

#### JavaScript/TypeScript (Frontend + Mobile + Shared Packages)

| Tool | Version | Purpose | Why Recommended | Confidence |
|------|---------|---------|-----------------|------------|
| eslint | ^9.x | JS/TS linting | ESLint 9 uses flat config (`eslint.config.js`). The new config system is now stable and recommended. | MEDIUM |
| prettier | ^3.x | Code formatting | Opinionated formatter. Separate from ESLint (do NOT use eslint-plugin-prettier -- it's slow). Run independently. | MEDIUM |
| typescript | ^5.x | Type checking | Use `tsc --noEmit` for type-checking. Next.js and Expo both use TypeScript natively. | MEDIUM |

**ESLint 9 flat config pattern (shared package):**
```javascript
// packages/config-eslint/index.js
import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import nextPlugin from "@next/eslint-plugin-next";

export const baseConfig = tseslint.config(
  ...tseslint.configs.recommended,
  { ignores: ["**/dist/**", "**/.next/**", "**/node_modules/**"] }
);

export const nextConfig = tseslint.config(
  ...baseConfig,
  { plugins: { react: reactPlugin, "@next/next": nextPlugin } }
);

export const reactNativeConfig = tseslint.config(
  ...baseConfig,
  { plugins: { react: reactPlugin } }
);
```

**Why ESLint 9 flat config, not legacy .eslintrc:**
ESLint deprecated the old config system. New projects should use flat config exclusively. It's simpler (just JS exports) and composes better in monorepos.

#### Pre-commit Configuration

**.pre-commit-config.yaml:**
```yaml
repos:
  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0  # VERIFY: pin to latest
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # JS/TS (via lint-staged, not pre-commit directly)
  - repo: local
    hooks:
      - id: lint-staged
        name: lint-staged
        entry: pnpm lint-staged
        language: system
        pass_filenames: false

  # General
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0  # VERIFY: pin to latest
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
```

**lint-staged config (in root package.json):**
```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,yml,yaml}": ["prettier --write"]
  }
}
```

**Why pre-commit for Python + lint-staged for JS:**
`pre-commit` is the Python ecosystem's standard hook manager. `lint-staged` is the JS ecosystem's standard. Using both respects each ecosystem's conventions. `pre-commit` orchestrates everything and calls `lint-staged` for JS files.

---

### 7. CI/CD Pipeline (GitHub Actions)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| GitHub Actions | N/A | CI/CD pipeline | Standard for GitHub-hosted repos. Free for public repos, generous free tier for private. | HIGH |

**Workflow pattern -- three jobs, parallel where possible:**

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
      # NOTE: Detox E2E tests require macOS runners (expensive)
      # Only run on main branch merges, not every PR
      # EAS Build handles actual native builds
```

**Key decisions:**
- Three parallel jobs (api, web, mobile) for fast CI
- Postgres service container with PGVector for API tests
- `uv` for Python dependency installation (much faster than pip)
- pnpm caching via `actions/setup-node` built-in cache
- Detox E2E tests are expensive (macOS runner required); run on merge to main only
- Expo/EAS Build for actual mobile builds (not in basic CI)

**Why NOT a single monolithic job:**
Running Python, Next.js, and mobile checks in one job means a flake8 failure blocks mobile type-checking feedback. Parallel jobs give faster feedback and clearer failure isolation.

---

### 8. Additional Supporting Libraries

| Library | Version | Purpose | Why Recommended | Confidence |
|---------|---------|---------|-----------------|------------|
| @tanstack/react-query | ^5.x | Data fetching and caching for Next.js + React Native | Standard for server state management. Works identically on web and mobile. Pairs perfectly with openapi-fetch for type-safe queries. | MEDIUM |
| react-hook-form | ^7.x | Form state management | Lightweight, performant form library. Integrates with Zod via `@hookform/resolvers`. Used by Shadcn/ui form components. | MEDIUM |
| @hookform/resolvers | ^3.x | Connects react-hook-form to Zod | Enables `zodResolver(schema)` in form hooks for automatic validation. | MEDIUM |
| @expo/next-adapter | ^6.x | Next.js + Expo compatibility | Configures Next.js to handle React Native Web imports properly. Required for shared `packages/ui-primitives/`. | LOW |
| @react-navigation/native | ^7.x | Mobile navigation | Standard navigation for React Native/Expo apps. Do NOT try to share navigation with Next.js -- they are fundamentally different paradigms. | MEDIUM |
| gunicorn | ^22.x | Production WSGI server | Standard production server for Django. Do NOT use `manage.py runserver` in production. | MEDIUM |
| django-cors-headers | ^4.x | CORS handling for API | Required because Next.js frontend runs on a different port/domain than Django API. | MEDIUM |
| django-environ | ^0.11.x | Environment variable management | Reads `.env` files for Django settings. Standard for 12-factor app configuration. | MEDIUM |
| psycopg | ^3.x | PostgreSQL adapter for Django | psycopg3 (the package named `psycopg`) is the modern PostgreSQL adapter. Use instead of `psycopg2-binary` for new projects -- it's pure Python with optional C acceleration, and actively maintained. | MEDIUM |
| whitenoise | ^6.x | Static file serving | Serves Django static files in production without requiring nginx/S3. Simplifies deployment for a template. | MEDIUM |
| huey or celery | ^2.x | Background task queue (optional) | For async jobs (email sending, AI processing). Huey is simpler (uses Redis or SQLite); Celery is more powerful but complex. Recommend Huey for template simplicity, let projects upgrade to Celery if needed. | LOW |

---

### 9. Python Dependency Management (uv)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| uv | latest | Python package installer and resolver | 10-100x faster than pip. Drop-in replacement. Handles venvs, dependency resolution, and lockfiles. Created by the same team as ruff (Astral). Becoming the standard Python package manager. | MEDIUM |

**Pattern:**
```bash
# In apps/api/
uv init  # Creates pyproject.toml
uv add django django-ninja-extra django-allauth  # Add dependencies
uv sync  # Install from lockfile (uv.lock)
```

**Why uv over pip:**
- Dramatically faster installs (important in CI and Docker builds)
- Built-in lockfile (`uv.lock`) for reproducible builds
- Built-in virtual environment management
- Same team as ruff -- consistent tooling philosophy

**Why NOT poetry:**
- Poetry is slower than uv
- Poetry has a custom resolver that can be slow on complex dependency trees
- uv is gaining rapid adoption and is simpler
- For a new template in 2025/2026, uv is the forward-looking choice

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `psycopg2-binary` | Legacy adapter, wheels can cause issues in Docker, not actively developed | `psycopg[binary]` (psycopg3) |
| `black` + `flake8` + `isort` | Three tools where one (ruff) does everything faster | `ruff` |
| `eslint-plugin-prettier` | Slow -- runs prettier inside ESLint. Use them as separate tools | ESLint + Prettier separately |
| `.eslintrc` / `.eslintrc.json` | Legacy ESLint config format, deprecated in ESLint 9 | `eslint.config.js` (flat config) |
| `swagger-codegen` / `openapi-generator` | Java-based, generates bloated SDKs, over-engineered | `openapi-typescript` + `openapi-fetch` |
| `axios` | Adds unnecessary dependency; `openapi-fetch` wraps native `fetch` | `openapi-fetch` (uses native fetch) |
| `dotenv` (npm package) | Next.js has built-in `.env` handling; Django uses `django-environ` | Built-in env handling per framework |
| `docker-compose` v1 (standalone) | Deprecated. Docker Desktop includes Compose v2 as `docker compose` | `docker compose` (v2, built into Docker) |
| `pip` directly in CI/Docker | Slow, no lockfile | `uv` |
| `create-react-app` | Dead project, not relevant here | Next.js (already decided) |
| Poetry | Slower than uv, heavier, less momentum in 2025+ | `uv` |
| Yarn | pnpm is decided and non-negotiable | `pnpm` |
| `jest` (for frontend) | vitest is faster, ESM-native, Vite-compatible | `vitest` (already decided) |
| Tamagui / NativeWind (in template) | Adds cross-platform UI abstraction complexity to the template; let each project add if needed | Raw `react-native-web` with thin primitives |
| Solito | Navigation abstraction layer between Next.js and React Navigation; adds coupling and complexity | Keep navigation separate per platform |

---

## Version Compatibility Matrix

> **WARNING:** All versions below are based on training data (May 2025). Verify with `npm view <package> version` and `pip index versions <package>` before implementation.

| Package | Estimated Version | Compatible With | Notes |
|---------|-------------------|-----------------|-------|
| Next.js | 15.x | React 19.x, React DOM 19.x | App Router is the default and recommended |
| React | 19.x | React Native 0.76+ (New Architecture) | React 19 brings Server Components (web only) |
| React Native | 0.76.x+ | Expo SDK 52+ | New Architecture enabled by default |
| Expo SDK | 52.x | React Native 0.76.x | Managed workflow, EAS Build for native |
| TypeScript | 5.6+ | All JS/TS packages | Strict mode recommended |
| Node.js | 20.x LTS | pnpm 9.x, turbo 2.x | LTS for stability in CI |
| Python | 3.12.x | Django 5.x, ruff, mypy | 3.12 for performance improvements |
| Django | 5.1.x | django-ninja-extra, django-allauth | LTS-adjacent, stable |
| Postgres | 16.x | PGVector 0.7.x+ | PGVector HNSW indexing available in 0.5+ |
| pnpm | 9.x | Node 20+, turbo 2.x | Corepack-managed |
| turbo | 2.x | pnpm workspaces | Major rewrite from v1, better performance |

---

## Monorepo Package Structure (Detailed)

### packages/api-client/
**Purpose:** Auto-generated TypeScript types + type-safe fetch client
```
packages/api-client/
  package.json
  tsconfig.json
  src/
    types.d.ts          # Generated by openapi-typescript (DO NOT EDIT)
    client.ts           # openapi-fetch client instance
    index.ts            # Re-exports
```

### packages/schemas/
**Purpose:** Zod validation schemas shared between web and mobile
```
packages/schemas/
  package.json
  tsconfig.json
  src/
    auth.ts             # Login, signup, password reset schemas
    user.ts             # User profile schemas
    common.ts           # Shared primitives (email, password, etc.)
    index.ts
```

### packages/ui-primitives/
**Purpose:** React Native Web components usable on both platforms
```
packages/ui-primitives/
  package.json
  tsconfig.json
  src/
    Button.tsx
    TextInput.tsx
    Card.tsx
    Typography.tsx
    Layout.tsx
    Loading.tsx
    index.ts
```

### packages/config-eslint/
**Purpose:** Shared ESLint flat config
```
packages/config-eslint/
  package.json
  index.js              # Base config
  next.js               # Next.js-specific config
  react-native.js       # React Native-specific config
```

### packages/config-ts/
**Purpose:** Shared TypeScript configs
```
packages/config-ts/
  package.json
  base.json             # Shared strict settings
  nextjs.json           # Next.js-specific (extends base)
  react-native.json     # React Native-specific (extends base)
  library.json          # For shared packages (extends base)
```

---

## Environment Variables Pattern

**Strategy:** Each service has its own `.env` file, with a `.env.example` checked into git.

```
foundation-template/
  .env.example                  # Docker Compose variables
  apps/api/.env.example         # Django-specific
  apps/web/.env.example         # Next.js-specific (NEXT_PUBLIC_ prefix)
  apps/mobile/.env.example      # Expo-specific
```

**Docker Compose `.env`:**
```bash
POSTGRES_DB=foundation
POSTGRES_USER=foundation
POSTGRES_PASSWORD=foundation
DATABASE_URL=postgres://foundation:foundation@db:5432/foundation
```

**Django `.env` (apps/api/.env):**
```bash
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=postgres://foundation:foundation@localhost:5432/foundation
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**Next.js `.env.local` (apps/web/.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Deployment Patterns (Docker-First)

**Local development:** `docker compose up` (Postgres + Django + Next.js)
**Production (any cloud):** Docker images built from the same Dockerfiles

| Deployment Target | Method | Notes |
|-------------------|--------|-------|
| Local dev | Docker Compose | `docker compose up` runs everything |
| AWS | ECS/Fargate or EC2 + Docker Compose | Fargate for serverless containers; EC2 for more control |
| GCP | Cloud Run or GKE | Cloud Run is simplest for containerized apps |
| Azure | Container Apps or AKS | Container Apps is the PaaS option |
| DigitalOcean | App Platform or Droplet + Docker Compose | App Platform auto-deploys from Dockerfile |
| Railway/Render | Direct Docker deployment | Simplest option for solo developer; detects Dockerfile |
| Self-hosted | Docker Compose on VPS | Same compose file works with minor production tweaks |

**Production Docker Compose overlay:**
```yaml
# docker-compose.prod.yml (extends base)
services:
  api:
    build:
      target: prod  # Uses production stage of multi-stage Dockerfile
    environment:
      DEBUG: "false"
    restart: unless-stopped

  web:
    build:
      target: prod
    restart: unless-stopped

  db:
    restart: unless-stopped
    # In production, consider managed Postgres (RDS, Cloud SQL)
    # instead of self-hosted container
```

---

## Installation Commands

### Initial project setup
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

# Start everything
docker compose up -d db    # Start Postgres first
cd apps/api && uv run python manage.py migrate  # Run migrations
docker compose up          # Start all services
```

### Development dependencies (all managed via respective package managers)
```bash
# JS/TS (via pnpm, in respective workspaces)
pnpm add -D -w turbo                          # Root: build orchestration
pnpm add -D -w prettier                       # Root: formatting
pnpm add -D -w lint-staged                    # Root: pre-commit JS linting
pnpm add -D -w @types/node                    # Root: Node types

# In packages/api-client:
pnpm add openapi-typescript openapi-fetch

# In apps/web:
pnpm add @tanstack/react-query react-hook-form @hookform/resolvers zod

# In apps/mobile:
pnpm add @tanstack/react-query react-hook-form @hookform/resolvers zod
pnpm add @react-navigation/native @react-navigation/native-stack

# Python (via uv, in apps/api/)
uv add django django-ninja-extra django-allauth
uv add django-cors-headers django-environ psycopg[binary] whitenoise gunicorn
uv add --dev ruff mypy django-stubs pytest pytest-django pytest-cov
```

---

## Sources and Confidence Notes

| Source Type | What Was Verified | Confidence Impact |
|-------------|-------------------|-------------------|
| Training data (May 2025) | All library recommendations, version numbers, configuration patterns | MEDIUM -- versions may have incremented since training cutoff |
| npm/PyPI registries | Unable to verify (tool access denied) | Versions flagged for manual verification |
| Official documentation patterns | Based on training data knowledge of official docs | MEDIUM -- patterns are stable but details may have changed |

**Action required before implementation:**
1. Run `npm view <package> version` for all JS/TS packages to get current versions
2. Run `pip index versions <package>` for all Python packages to get current versions
3. Verify ESLint 9 flat config API is stable (it was in v9.0+ as of training data)
4. Verify `@expo/next-adapter` still exists and is the recommended approach for Expo + Next.js
5. Check if openapi-typescript v7+ has any breaking changes vs v6
6. Verify Expo SDK version compatibility with React Native version

---
*Stack research for: Foundation Template (Full-Stack SaaS Starter)*
*Researched: 2026-02-08*
*Confidence: MEDIUM -- all versions require verification against current npm/PyPI registries*
