# Architecture Research

**Domain:** Full-stack SaaS foundation template (Turborepo monorepo)
**Researched:** 2026-02-08
**Confidence:** MEDIUM (WebSearch/WebFetch unavailable; findings based on training data through May 2025 plus established patterns for all named technologies. All claims should be verified against current docs during implementation.)

---

## System Overview

```
                            CLIENTS
  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │   Next.js 15     │  │   Expo Mobile    │  │  Third-Party     │
  │   (App Router)   │  │   (iOS/Android)  │  │  API Consumers   │
  │   SSR + CSR      │  │   Managed Flow   │  │                  │
  └───────┬──────────┘  └───────┬──────────┘  └───────┬──────────┘
          │                     │                     │
          │  ┌─────────────────────────────────┐      │
          │  │      SHARED PACKAGES (TS)       │      │
          │  │  api-client | validation | ui   │      │
          │  │  business-logic | config        │      │
          │  └─────────────────────────────────┘      │
          │                     │                     │
          ▼                     ▼                     ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                    Django Ninja Extra API                      │
  │              (REST + OpenAPI spec generation)                  │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
  │  │  Auth    │  │  Core    │  │  Billing │  │  AI Module   │  │
  │  │ (Allauth)│  │  CRUD    │  │  (Stripe)│  │ (LangGraph)  │  │
  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
  ├───────────────────────────────────────────────────────────────┤
  │                     Django ORM Layer                           │
  ├───────────────────────────────────────────────────────────────┤
  │              PostgreSQL 16+ with PGVector                     │
  └───────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Django Ninja Extra API** | All business logic, auth, data persistence, OpenAPI spec generation | Django apps with Ninja Extra controllers, Pydantic schemas |
| **Next.js 15 Frontend** | Web UI, SSR/SSG pages, SEO, Next.js middleware for auth guards | App Router, Server Components, Shadcn/ui + Tailwind |
| **Expo Mobile App** | iOS/Android native experience, push notifications, device APIs | Expo managed workflow, Expo Router |
| **Shared API Client** | Type-safe HTTP client auto-generated from OpenAPI | Generated via openapi-typescript + openapi-fetch or orval |
| **Shared Validation** | Cross-platform input validation schemas | Zod schemas consumed by web, mobile, and optionally synced to Python Pydantic |
| **Shared UI** | Reusable UI primitives working on both web and mobile | React Native Web components, or Tamagui/NativeWind |
| **Shared Business Logic** | Platform-agnostic hooks, utilities, constants, formatters | Plain TypeScript, React hooks |
| **PostgreSQL + PGVector** | Relational data, vector embeddings for AI features | PostgreSQL 16 with pgvector extension |
| **AI Module (LangGraph)** | RAG pipeline, agent workflows, embedding generation | LangGraph Python package within Django, or separate worker |

---

## Recommended Monorepo Structure

```
foundation-template/
├── apps/
│   ├── web/                        # Next.js 15 App Router
│   │   ├── app/                    # App Router pages/layouts
│   │   │   ├── (auth)/             # Auth route group
│   │   │   ├── (dashboard)/        # Dashboard route group
│   │   │   ├── api/                # Next.js API routes (BFF proxy, webhooks)
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/             # Web-specific components
│   │   ├── lib/                    # Web-specific utilities
│   │   ├── middleware.ts           # Auth middleware
│   │   ├── next.config.ts          # Next.js config (with RNW transpile)
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── mobile/                     # Expo React Native app
│   │   ├── app/                    # Expo Router file-based routing
│   │   │   ├── (auth)/
│   │   │   ├── (tabs)/
│   │   │   └── _layout.tsx
│   │   ├── components/             # Mobile-specific components
│   │   ├── lib/                    # Mobile-specific utilities
│   │   ├── app.json                # Expo config
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── api/                        # Django project root
│       ├── manage.py
│       ├── pyproject.toml          # Python dependencies (uv/poetry)
│       ├── config/                 # Django project settings
│       │   ├── __init__.py
│       │   ├── settings/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── development.py
│       │   │   └── production.py
│       │   ├── urls.py
│       │   ├── wsgi.py
│       │   └── asgi.py
│       ├── apps/                   # Django apps
│       │   ├── accounts/           # User model, Django Allauth config
│       │   │   ├── models.py
│       │   │   ├── schemas.py      # Pydantic schemas (Ninja)
│       │   │   ├── controllers.py  # Ninja Extra controllers
│       │   │   ├── services.py     # Business logic
│       │   │   └── tests/
│       │   ├── core/               # Shared Django utilities
│       │   ├── billing/            # Stripe integration
│       │   └── ai/                 # LangGraph module (removable)
│       │       ├── graphs/         # LangGraph graph definitions
│       │       ├── embeddings.py   # PGVector embedding pipeline
│       │       ├── controllers.py
│       │       └── schemas.py
│       ├── tests/
│       └── Dockerfile
│
├── packages/
│   ├── api-client/                 # Auto-generated typed API client
│   │   ├── src/
│   │   │   ├── generated/          # Auto-generated types + client
│   │   │   │   ├── types.ts        # From OpenAPI spec
│   │   │   │   └── client.ts       # Typed fetch client
│   │   │   ├── index.ts            # Re-exports + custom wrappers
│   │   │   └── hooks.ts            # React Query hooks wrapping client
│   │   ├── scripts/
│   │   │   └── generate.ts         # OpenAPI generation script
│   │   ├── openapi.json            # Cached OpenAPI spec from Django
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── validation/                 # Shared Zod schemas
│   │   ├── src/
│   │   │   ├── auth.ts             # Auth validation schemas
│   │   │   ├── user.ts             # User schemas
│   │   │   ├── billing.ts          # Billing schemas
│   │   │   └── index.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── ui/                         # Shared UI primitives
│   │   ├── src/
│   │   │   ├── button.tsx          # Cross-platform Button
│   │   │   ├── input.tsx           # Cross-platform Input
│   │   │   ├── text.tsx            # Cross-platform Text
│   │   │   ├── primitives/         # Low-level primitives
│   │   │   └── index.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── business-logic/             # Shared hooks, utils, constants
│   │   ├── src/
│   │   │   ├── hooks/              # React hooks (useAuth, useUser)
│   │   │   ├── utils/              # Formatters, helpers
│   │   │   ├── constants/          # App-wide constants
│   │   │   └── index.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── config/                     # Shared eslint config
│   │   ├── eslint-preset.js
│   │   └── package.json
│   │
│   └── typescript-config/          # Shared TypeScript configs
│       ├── base.json
│       ├── nextjs.json
│       ├── react-native.json
│       └── package.json
│
├── tooling/                        # Build tools, scripts, CI helpers
│   ├── scripts/
│   │   ├── generate-api-client.sh  # Fetch OpenAPI spec + generate client
│   │   └── setup.sh                # First-time project setup
│   └── docker/
│       ├── Dockerfile.api          # Django production Dockerfile
│       ├── Dockerfile.web          # Next.js production Dockerfile
│       └── nginx.conf              # Reverse proxy config (optional)
│
├── docker-compose.yml              # Local development orchestration
├── docker-compose.prod.yml         # Production overrides
├── turbo.json                      # Turborepo pipeline config
├── package.json                    # Root workspace config
├── pnpm-workspace.yaml             # pnpm workspace definition
├── .env.example                    # Environment variable template
├── .gitignore
└── README.md
```

### Structure Rationale

- **`apps/` vs `packages/`:** Turborepo convention. `apps/` contains deployable applications (things with their own server/build process). `packages/` contains shared libraries consumed by apps. This is the standard Turborepo pattern and should not be deviated from.

- **Django in `apps/api/`:** Even though Django is Python, it lives in `apps/` because it is a deployable application. Turborepo does not natively manage Python dependencies, but it can still orchestrate tasks (lint, test, build) for the Django project via custom scripts defined in `turbo.json`. The Python dependency management happens via `pyproject.toml` with uv or poetry, independent of the pnpm workspace.

- **`packages/api-client/` with `generated/` subfolder:** The generated code is isolated in a subdirectory so it can be gitignored or committed (team preference). The outer `src/` adds custom wrappers, React Query hooks, and re-exports that remain stable even when the generated code changes.

- **`packages/ui/` for cross-platform components:** This package uses React Native Web primitives (View, Text, Pressable) that render natively on mobile and as divs/spans on web. This is the simplest path to genuine code sharing -- not every component needs to be cross-platform, only foundational primitives.

- **`packages/config/` and `packages/typescript-config/`:** Following Turborepo's recommended pattern for sharing configurations. Each app extends these base configs, reducing drift.

- **`tooling/`:** Not a Turborepo workspace -- just scripts and Dockerfiles that support development. Keeps the root clean.

---

## Architectural Patterns

### Pattern 1: Backend-for-Frontend (BFF) Thin Proxy via Next.js API Routes

**What:** Next.js API routes act as a thin proxy layer between the browser and Django API for specific concerns: CSRF token handling, cookie-to-header auth token translation, webhook endpoints (e.g., Stripe), and server-side data fetching in Server Components.

**When to use:** When the web client needs server-side session management, when you need to aggregate multiple Django API calls into one response, or when third-party webhooks need a stable URL that differs from the Django endpoint.

**Trade-offs:**
- PRO: Simplifies auth (httpOnly cookies managed by Next.js, token forwarded to Django)
- PRO: Server Components can call Django directly (server-to-server, no CORS)
- CON: Adds a network hop for proxied requests
- CON: Must not become a second API -- keep it thin

**Example:**
```typescript
// apps/web/app/api/proxy/[...path]/route.ts
import { cookies } from 'next/headers';

export async function GET(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  const apiPath = params.path.join('/');

  const response = await fetch(
    `${process.env.DJANGO_API_URL}/api/v1/${apiPath}`,
    {
      headers: {
        Authorization: token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    }
  );

  const data = await response.json();
  return Response.json(data, { status: response.status });
}
```

**Recommended approach:** Direct client-to-Django calls for most data fetching (the API client package handles this). Use Next.js API routes ONLY for: (1) Server Component data loading, (2) auth token exchange, (3) webhook receivers, (4) server-side operations that need secrets not exposed to the browser.

### Pattern 2: OpenAPI-First Type Generation Pipeline

**What:** Django Ninja Extra generates an OpenAPI 3.1 schema from Pydantic models and controller decorators. This schema is consumed by a code generation tool that produces TypeScript types and a typed fetch client, which lives in `packages/api-client/`.

**When to use:** Always. This is the core integration pattern that keeps the Python backend and TypeScript frontends in sync.

**Trade-offs:**
- PRO: Single source of truth for API contracts (Python Pydantic models)
- PRO: TypeScript consumers get compile-time type safety
- PRO: No manual type maintenance
- CON: Generation step must be run after API changes
- CON: Complex response types (unions, discriminated unions) may need manual refinement

**Pipeline:**
```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Django Ninja    │     │  OpenAPI JSON     │     │  TypeScript      │
│  Pydantic Models │────>│  Schema           │────>│  Types + Client  │
│  + Controllers   │     │  (apps/api/)      │     │  (packages/      │
│                  │     │                   │     │   api-client/)   │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        |                       |                        |
   python manage.py          curl or                openapi-ts or
   export_openapi_schema     script                 orval generate
```

**Recommended tools:**
- **openapi-typescript** (v7+) for type generation -- produces TypeScript types from OpenAPI 3.x schemas. Lightweight, well-maintained.
- **openapi-fetch** for the runtime client -- tiny (~6kb), uses native fetch, fully typed from openapi-typescript output. No code generation needed for the client itself, just types.
- Alternative: **orval** if you want auto-generated React Query hooks. More opinionated but reduces boilerplate significantly.

**Example Turborepo pipeline (`turbo.json` excerpt):**
```json
{
  "tasks": {
    "generate": {
      "dependsOn": ["^build"],
      "outputs": ["src/generated/**"]
    },
    "api#export-schema": {
      "cache": false
    }
  }
}
```

### Pattern 3: Layered Django App Structure (Controllers / Services / Repositories)

**What:** Each Django app follows a strict layered architecture: Controllers (Ninja Extra) handle HTTP concerns, Services contain business logic, and the ORM models/managers serve as the repository layer.

**When to use:** Always. This prevents the common Django anti-pattern of fat views/controllers.

**Trade-offs:**
- PRO: Testable business logic (services can be tested without HTTP)
- PRO: Controllers stay thin -- just validation, auth, and delegation
- CON: More files per app
- CON: Can feel over-engineered for simple CRUD

**Example:**
```python
# apps/api/apps/accounts/controllers.py
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated

from .schemas import UserOut, UserUpdateIn
from .services import UserService

@api_controller('/users', tags=['Users'])
class UserController:
    def __init__(self):
        self.service = UserService()

    @route.get('/me', response=UserOut, permissions=[IsAuthenticated])
    def get_current_user(self, request):
        return self.service.get_user(request.user.id)

    @route.patch('/me', response=UserOut, permissions=[IsAuthenticated])
    def update_current_user(self, request, payload: UserUpdateIn):
        return self.service.update_user(request.user.id, payload)
```

```python
# apps/api/apps/accounts/services.py
from django.contrib.auth import get_user_model
from .schemas import UserUpdateIn

User = get_user_model()

class UserService:
    def get_user(self, user_id: int) -> User:
        return User.objects.get(id=user_id)

    def update_user(self, user_id: int, data: UserUpdateIn) -> User:
        user = User.objects.get(id=user_id)
        for field, value in data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        user.save()
        return user
```

### Pattern 4: Cross-Platform UI via React Native Web (Selective Sharing)

**What:** Share foundational UI primitives (Button, Text, Input, Card) between Next.js web and Expo mobile using React Native Web. NOT all components -- only low-level primitives where visual parity matters.

**When to use:** For design-system-level primitives. Platform-specific components (navigation, native features) remain in their respective `apps/` directories.

**Trade-offs:**
- PRO: True code reuse for core UI elements
- PRO: Consistent design language across platforms
- CON: React Native Web adds complexity to Next.js config (module resolution, transpilation)
- CON: Not all React Native components have web equivalents
- CON: Styling approaches may diverge (Tailwind on web, StyleSheet on native)

**Recommended approach -- NativeWind over raw React Native Web:**
Use NativeWind (Tailwind CSS for React Native) in `packages/ui/`. NativeWind v4 supports both React Native and React Native Web, allowing the same className-based styling to work on both platforms. This eliminates the StyleSheet vs Tailwind divergence.

**Next.js configuration for React Native Web:**
```javascript
// apps/web/next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: [
    'react-native',
    'react-native-web',
    'nativewind',
    '@repo/ui',
    '@repo/business-logic',
  ],
  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      'react-native$': 'react-native-web',
    };
    return config;
  },
};

export default nextConfig;
```

**Expo configuration (must resolve monorepo packages):**
```javascript
// apps/mobile/metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);
config.watchFolders = [monorepoRoot];
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

module.exports = config;
```

---

## Data Flow

### Primary Request Flow (Client to Database)

```
[Browser/Mobile App]
    |
    |  HTTP request (fetch via api-client package)
    |  Authorization: Bearer <token>
    |
    v
[Django Ninja Extra API]
    |
    |-- Middleware: Auth token validation (Django Allauth / JWT)
    |-- Controller: Request validation (Pydantic schema)
    |-- Service: Business logic
    |-- ORM: Database query
    |
    v
[PostgreSQL 16 + PGVector]
    |
    v
[Response: Pydantic schema -> JSON]
    |
    v
[Client: openapi-fetch typed response -> React state]
```

### Server Component Data Flow (Next.js SSR)

```
[Browser requests page]
    |
    v
[Next.js Server (Server Component)]
    |
    |  Server-to-server fetch (no CORS, internal network)
    |  Uses service account token or forwarded user cookie
    |
    v
[Django Ninja Extra API]
    |
    v
[Server Component renders HTML with data]
    |
    v
[HTML streamed to browser]
    |
    v
[Client Components hydrate with server-fetched data]
```

### Authentication Flow

```
                    SIGN UP / SIGN IN

[Web Client]                              [Mobile Client]
    |                                         |
    |  POST /api/auth/login                   |  POST /api/auth/login
    |  {email, password}                      |  {email, password}
    |                                         |
    v                                         v
[Django Allauth + Ninja Extra Auth Controller]
    |
    |-- Validates credentials
    |-- Creates session OR issues JWT tokens
    |
    v                                         v
[Web: Set httpOnly cookie]            [Mobile: Return access + refresh tokens]
    |                                         |
    |  Cookie sent automatically              |  Stored in expo-secure-store
    |  on subsequent requests                 |  Sent via Authorization header
    |                                         |
    v                                         v
[Next.js Middleware]                  [Expo app-level auth check]
    |                                         |
    |-- Reads auth cookie                     |-- Reads token from secure store
    |-- Validates (or proxies to Django)      |-- Attaches to api-client
    |-- Redirects if unauthenticated          |-- Navigates to login if expired
    |                                         |
    v                                         v
[Authenticated page renders]          [Authenticated screen renders]


                    TOKEN REFRESH

[Web: Cookie refresh handled by Django session middleware]
[Mobile: api-client interceptor detects 401 -> POST /api/auth/refresh -> retry]
```

**Auth architecture decision: Session-based for web, JWT for mobile.**

Rationale:
- **Web (Session/Cookie):** Django Allauth naturally provides session-based auth. httpOnly cookies are more secure than storing JWTs in browser storage. Next.js middleware can read the session cookie for server-side auth checks. No token refresh logic needed on the client.
- **Mobile (JWT):** Mobile apps cannot use cookies effectively. JWT access + refresh token pair stored in `expo-secure-store`. The API client package includes an interceptor that handles transparent token refresh.
- **Django Allauth** supports both flows. The `dj-rest-auth` package (built on top of Allauth) provides token-based endpoints alongside session-based auth. Alternatively, `django-ninja-jwt` provides JWT support specifically for Django Ninja.

### OpenAPI Type Sync Flow

```
[Developer changes Django Pydantic schema or controller]
    |
    v
[Run: turbo run generate --filter=api-client]
    |
    |-- Step 1: Django management command exports openapi.json
    |-- Step 2: openapi-typescript generates TypeScript types
    |-- Step 3: Types are consumed by api-client package
    |
    v
[TypeScript compilation catches type mismatches in web/mobile]
    |
    v
[CI pipeline also runs generation + type-check to catch drift]
```

### AI Module Data Flow (LangGraph + PGVector)

```
[User submits query (web or mobile)]
    |
    v
[Django AI Controller]
    |
    |-- Validates input
    |-- Delegates to LangGraph graph
    |
    v
[LangGraph Agent/Chain]
    |
    |-- Retrieval: Query PGVector for relevant embeddings
    |-- Generation: Call LLM with context
    |-- (Optional) Tool use: Call other Django services
    |
    v
[Response streamed back via SSE or returned as JSON]
    |
    v
[Client renders response]


                EMBEDDING PIPELINE

[New content created/updated in Django]
    |
    v
[Django signal or Celery task]
    |
    |-- Generate embedding via OpenAI/local model
    |-- Store in PGVector column
    |
    v
[PGVector index updated, available for similarity search]
```

---

## Docker Compose Service Architecture

```yaml
# docker-compose.yml - Local Development
services:
  # Database
  db:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: foundation
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Cache + Task Broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  # Backend API
  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
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
    command: python manage.py runserver 0.0.0.0:8000

  # Background Workers (optional profile)
  worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
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
    command: celery -A config worker -l info
    profiles:
      - with-worker

  # Dev Email Capture (optional profile)
  mailpit:
    image: axllent/mailpit
    ports:
      - "8025:8025"
      - "1025:1025"
    profiles:
      - with-mail

volumes:
  postgres_data:
```

**Key Docker decisions:**

- **`pgvector/pgvector:pg16`** instead of plain `postgres:16` -- PGVector is pre-installed, no extension setup needed.
- **Next.js and Expo are NOT in Docker for local development.** They run natively via `turbo run dev`. Reason: Hot module replacement, fast refresh, and file watching work much better natively. Docker adds latency to the frontend dev loop for no benefit. Only Django and infrastructure services (Postgres, Redis) run in Docker.
- **Celery worker uses Docker profiles** (`--profile with-worker`) so it only runs when needed. Not every developer needs the async worker running.
- **Mailpit** for local email testing -- captures emails sent by Django Allauth without needing a real SMTP server. Also uses profiles.
- **Redis** is included for Celery broker, Django caching, and potential session storage. Even if not needed immediately, it is cheap to include and avoids adding it later.

---

## Turborepo Pipeline Configuration

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": [".env"],
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
    "typecheck": {
      "dependsOn": ["^build"]
    },
    "generate": {
      "cache": false,
      "outputs": ["src/generated/**"]
    },
    "clean": {
      "cache": false
    }
  }
}
```

**Turborepo + Python nuance:** Turborepo orchestrates tasks defined in `package.json` scripts. For the Django project (`apps/api/`), create a minimal `package.json` that delegates to Python tooling:

```json
{
  "name": "@repo/api",
  "private": true,
  "scripts": {
    "dev": "python manage.py runserver 0.0.0.0:8000",
    "test": "pytest",
    "lint": "ruff check .",
    "typecheck": "mypy .",
    "export-schema": "python manage.py export_openapi_schema > ../../packages/api-client/openapi.json"
  }
}
```

This lets `turbo run lint` or `turbo run test` include the Django project alongside TypeScript packages. The Python package manager (uv/poetry) handles dependency installation separately -- it is not managed by pnpm.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Fat Next.js API Routes (Accidental Second Backend)

**What people do:** Move business logic into Next.js API routes, creating a shadow backend alongside Django. Routes start querying the database directly, handling auth, performing complex operations.

**Why it is wrong:** Two sources of truth for business logic. Mobile app cannot access Next.js API routes, so features are duplicated. Django's ORM, migrations, and Allauth auth are bypassed.

**Do this instead:** Keep ALL business logic in Django. Next.js API routes should only: (1) proxy requests to Django when cookie-to-token translation is needed, (2) receive webhooks, (3) handle Next.js-specific concerns like revalidation triggers. The vast majority of data fetching should go directly from the client to Django via the API client package.

### Anti-Pattern 2: Sharing ALL Components via React Native Web

**What people do:** Try to make every UI component cross-platform, including complex layouts, navigation, forms with web-specific behavior.

**Why it is wrong:** React Native Web has gaps. Complex web-specific patterns (CSS Grid layouts, hover states with complex popovers, web form APIs) do not translate well. You end up with `Platform.OS` checks everywhere, defeating the purpose of sharing.

**Do this instead:** Share only foundational primitives in `packages/ui/`: Button, Text, Input, Card, Avatar, Badge, Icon. Keep platform-specific components (navigation bars, web-specific data tables, mobile-specific gesture handlers) in their respective `apps/` directories. The shared `packages/business-logic/` and `packages/api-client/` provide the real code reuse value.

### Anti-Pattern 3: Coupling Type Generation to Dev Server Startup

**What people do:** Auto-generate the API client on every dev server start, requiring Django to be running before Next.js or Expo can start.

**Why it is wrong:** Creates a hard dependency that slows down development. Frontend developers cannot work unless the backend is running. CI pipelines become fragile.

**Do this instead:** Commit the generated `openapi.json` and generated types to version control. Run type generation as an explicit step (`turbo run generate`) after API changes, not as part of the dev startup flow. CI verifies that committed types match the current Django schema. This allows frontend developers to work with stale-but-present types when the backend is unavailable.

### Anti-Pattern 4: Monolithic Django Settings

**What people do:** Use a single `settings.py` with `if DEBUG:` conditionals scattered throughout.

**Why it is wrong:** Hard to reason about which settings apply in which environment. Easy to accidentally ship debug settings to production.

**Do this instead:** Use the split settings pattern: `settings/base.py` (shared), `settings/development.py` (imports base + dev overrides), `settings/production.py` (imports base + prod overrides). Select via `DJANGO_SETTINGS_MODULE` environment variable.

### Anti-Pattern 5: Deeply Nested Shared Package Dependencies

**What people do:** Create packages that depend on other packages that depend on other packages: `ui` imports from `business-logic` which imports from `validation` which imports from `api-client`.

**Why it is wrong:** Creates circular dependency risks, increases build times, and makes it impossible to use one package without pulling in the entire dependency tree.

**Do this instead:** Keep packages at a flat dependency level. `api-client` depends on `validation` (for request body types). `ui` depends on nothing else in the monorepo. `business-logic` depends on `api-client` and `validation`. Apps (`web`, `mobile`) depend on all packages they need directly. No package-to-package chains longer than one hop.

---

## Package Dependency Graph

```
                        ┌─────────────┐
                        │   config    │   (no deps -- base tsconfigs, eslint)
                        └─────────────┘
                              ^
        ┌─────────────────────┼─────────────────────┐
        |                     |                     |
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ validation  │     │     ui      │     │ api-client  │
  │ (zod)       │     │ (RNW)      │     │ (generated) │
  └──────┬──────┘     └─────────────┘     └──────┬──────┘
         |                                       |
         |            ┌─────────────┐            |
         └───────────>│  business-  │<───────────┘
                      │  logic      │
                      │ (hooks,etc) │
                      └──────┬──────┘
                             |
              ┌──────────────┼──────────────┐
              v              v              v
        ┌──────────┐  ┌──────────┐  ┌──────────────┐
        │   web    │  │  mobile  │  │  (future      │
        │ (Next.js)│  │  (Expo)  │  │   apps)       │
        └──────────┘  └──────────┘  └──────────────┘
```

**Dependency rules:**
- `config` / `typescript-config`: No monorepo dependencies. Foundation layer.
- `validation`: No monorepo dependencies. Pure Zod schemas.
- `ui`: No monorepo dependencies. Pure React Native Web primitives. Styled with NativeWind.
- `api-client`: Depends on `validation` (imports Zod schemas for request validation).
- `business-logic`: Depends on `api-client` (uses typed client) and `validation` (uses schemas). Contains React hooks, utility functions.
- `web` and `mobile`: Depend on all packages they need. This is the composition layer.

---

## Scaling Considerations

| Concern | At 100 users | At 10K users | At 100K+ users |
|---------|--------------|--------------|----------------|
| **API** | Single Django process (runserver) | Gunicorn with 4-8 workers behind nginx | Horizontal scaling: multiple Django pods behind load balancer |
| **Database** | Single Postgres instance, no read replicas | Connection pooling (PgBouncer), query optimization, indexes | Read replicas, partitioning for large tables, PGVector HNSW indexes |
| **Background jobs** | No worker needed (or single Celery worker) | Celery with Redis broker, 2-4 workers | Dedicated Celery queues, autoscaling workers, task prioritization |
| **Frontend** | Vercel free tier or single VPS | Vercel Pro or self-hosted with CDN | Edge functions, ISR, regional deployment |
| **Mobile** | Direct API calls | Same as web -- API is the bottleneck | Same scaling story as API |
| **AI/Embeddings** | Sync embedding generation | Async via Celery, batch processing | Dedicated embedding worker, HNSW index tuning, pre-computed results |

### Scaling Priorities (What Breaks First)

1. **Database connections:** Django's default is to open a new connection per request. At 1K+ concurrent users, PostgreSQL's connection limit (default 100) becomes a bottleneck. **Fix:** Add PgBouncer or django-db-connection-pool early.
2. **Long-running AI requests:** LLM calls can take 5-30 seconds. Synchronous handling blocks Django workers. **Fix:** Use Celery for AI tasks from day one, return results via polling or SSE.
3. **OpenAPI spec size:** As the API grows, the generated TypeScript types file can become very large. **Fix:** Split API into versioned modules, generate per-module clients if needed.

---

## Build Order (Dependencies Between Components)

The following build order reflects the dependency graph and should inform the roadmap phase structure:

```
Phase 1: Foundation
  |-- 1a. Monorepo scaffolding (turbo.json, pnpm-workspace.yaml, package.json)
  |-- 1b. packages/config (tsconfig bases, eslint config)
  |-- 1c. Docker Compose (db, redis)
  |-- 1d. apps/api scaffolding (Django project, settings, custom user model)
           MUST be done before any API work.
           Custom user model MUST be created before first migration.

Phase 2: API Core
  |-- 2a. Django Ninja Extra setup (api.py, router registration)
  |-- 2b. Django Allauth setup (auth endpoints)
  |-- 2c. OpenAPI schema export (management command)
  |-- 2d. packages/api-client (type generation pipeline)
           Requires: Phase 1 complete, Django running with at least one endpoint

Phase 3: Shared Packages
  |-- 3a. packages/validation (Zod schemas matching Pydantic models)
  |-- 3b. packages/business-logic (auth hooks, API hooks using api-client)
  |-- 3c. packages/ui (React Native Web primitives)
           Requires: packages/config for tsconfig
           Can be developed in parallel with Phase 2

Phase 4: Web Application
  |-- 4a. apps/web scaffolding (Next.js 15 App Router)
  |-- 4b. React Native Web integration in Next.js config
  |-- 4c. Auth flow (middleware, login/signup pages)
  |-- 4d. Dashboard pages consuming api-client
  |-- 4e. Shadcn/ui setup + web-specific components
           Requires: Phase 2 (api-client), Phase 3 (shared packages)

Phase 5: Mobile Application
  |-- 5a. apps/mobile scaffolding (Expo managed workflow)
  |-- 5b. Metro config for monorepo package resolution
  |-- 5c. Auth flow (secure storage, JWT management)
  |-- 5d. Screens consuming shared packages
  |-- 5e. Mobile-specific features (push notifications, etc.)
           Requires: Phase 2 (api-client), Phase 3 (shared packages)
           Can be done in parallel with Phase 4

Phase 6: AI Module (Optional)
  |-- 6a. PGVector setup (model mixin, embedding field)
  |-- 6b. LangGraph graph definitions
  |-- 6c. Embedding pipeline (Celery tasks)
  |-- 6d. AI API endpoints
  |-- 6e. Frontend AI UI (chat interface, etc.)
           Requires: Phase 2 (API), Phase 1d (database)
           Designed to be removable: all code in apps/api/apps/ai/

Phase 7: DevEx and CI/CD
  |-- 7a. GitHub Actions (lint, test, typecheck, type generation verification)
  |-- 7b. Pre-commit hooks
  |-- 7c. Production Dockerfiles
  |-- 7d. Deployment configuration
           Can be incrementally built alongside other phases
```

**Critical path:** Phase 1 -> Phase 2 -> Phase 3 -> Phase 4/5 (parallel). The AI module is entirely orthogonal and can be built at any time after Phase 2.

**Why this order:**
1. Custom user model in Django MUST be created before the first migration. Changing it later requires database recreation. This is why Django scaffolding is Phase 1.
2. The API client package is the bridge between Python and TypeScript. It must exist before any frontend can meaningfully integrate.
3. Shared packages (validation, business-logic, ui) can be developed in parallel with the API because they have independent test harnesses, but they become useful only when consumed by apps.
4. Web and mobile can be developed in parallel once the shared packages exist.

---

## Key Technology Integration Details

### pnpm Workspace Configuration

```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'tooling/*'
```

Note: `apps/api` is listed as a workspace even though it is a Python project. It has a minimal `package.json` to participate in Turborepo task orchestration. Its Python dependencies are managed separately by `pyproject.toml`.

### Workspace Package Naming Convention

Use `@repo/` scope for all internal packages:
- `@repo/api-client`
- `@repo/validation`
- `@repo/ui`
- `@repo/business-logic`
- `@repo/config`
- `@repo/typescript-config`
- `@repo/api` (Django -- minimal package.json)

This convention is recommended by Turborepo documentation and avoids naming collisions with npm packages.

### Environment Variable Strategy

```
.env.example              # Template with all required vars (committed)
.env                      # Local overrides (gitignored)
apps/api/.env             # Django-specific vars (gitignored)
apps/web/.env.local       # Next.js local vars (gitignored)
```

Turborepo's `globalDependencies` in `turbo.json` should include `.env` so that cache is invalidated when environment changes. Next.js automatically loads `.env.local`. Django loads via `django-environ` or `python-dotenv`.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Stripe** | Webhooks to Next.js API route or Django endpoint; Stripe SDK in Django services | Webhook signature verification is critical. Use Stripe CLI for local testing. |
| **Email (Resend/SES)** | Django email backend; Allauth uses it for verification | Mailpit for local dev. Switch to production provider via Django EMAIL_BACKEND setting. |
| **LLM Provider (OpenAI/Anthropic)** | Python SDK in Django AI module | API keys in environment, never committed. Rate limiting in service layer. |
| **Object Storage (S3/R2)** | django-storages with S3 backend | For user uploads, AI document storage. Use presigned URLs for direct uploads. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Web <-> Django API** | HTTP REST via api-client (direct) or Next.js API route (proxy) | Direct for most calls. Proxy only for auth cookie handling. |
| **Mobile <-> Django API** | HTTP REST via api-client (always direct) | JWT auth. Never proxied. |
| **Django <-> PostgreSQL** | Django ORM | Migrations managed by Django. PGVector accessed via pgvector-python. |
| **Django <-> Redis** | django-redis for caching; Celery for task broker | Redis is infrastructure, not a data store. |
| **Django <-> LangGraph** | In-process Python call (same Django process) | LangGraph graphs are imported and invoked directly. For long-running graphs, dispatch via Celery. |
| **Web <-> Expo (shared code)** | packages/* (build-time sharing, not runtime) | No runtime communication. Code sharing is via the monorepo build system. |

---

## Sources

- Turborepo documentation: structuring repositories with apps/ and packages/ convention (turbo.build/repo/docs) -- MEDIUM confidence (training data, not live-verified)
- Django Ninja documentation: router organization, Pydantic schema integration (django-ninja.dev) -- MEDIUM confidence
- Django Ninja Extra: controller-based API organization pattern (django-ninja-extra) -- MEDIUM confidence
- React Native Web: aliasing react-native to react-native-web in Next.js webpack config (necolas.github.io/react-native-web) -- MEDIUM confidence
- Expo monorepo documentation: Metro config for monorepo workspace resolution (docs.expo.dev) -- MEDIUM confidence
- NativeWind v4: Tailwind CSS support for React Native and React Native Web -- LOW confidence (rapidly evolving, verify current docs)
- openapi-typescript + openapi-fetch: TypeScript type generation from OpenAPI specs (openapi-ts.dev) -- MEDIUM confidence
- Django Allauth: session and token-based authentication (docs.allauth.org) -- MEDIUM confidence
- pgvector: PostgreSQL vector similarity search extension (github.com/pgvector/pgvector) -- HIGH confidence (well-established, stable API)
- LangGraph: Python agent framework with graph-based workflows (langchain-ai/langgraph) -- LOW confidence (rapidly evolving API, verify current docs)
- Docker official images: pgvector/pgvector, redis:7-alpine -- HIGH confidence

---

*Architecture research for: Foundation Template (Full-Stack SaaS Monorepo)*
*Researched: 2026-02-08*
*Overall confidence: MEDIUM -- All findings based on training data (cutoff May 2025). WebSearch and WebFetch were unavailable for live verification. Core patterns (Turborepo structure, Django project layout, Docker Compose) are well-established and unlikely to have changed. React Native Web + NativeWind integration and LangGraph API should be verified against current documentation during implementation.*
