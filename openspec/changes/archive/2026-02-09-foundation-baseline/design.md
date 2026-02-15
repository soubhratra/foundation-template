## Context

This is a greenfield foundation template for building SaaS products. There is no existing codebase — everything is scaffolded from scratch. The template targets a solo technical entrepreneur who will use it to spin up multiple SaaS products, each inheriting the same stack: Django Ninja Extra (API), Next.js 15 (web), Expo (mobile), Turborepo (monorepo), Postgres+PGVector (database), Redis (cache/broker).

The template must work as both a reference implementation and a CLI-scaffoldable starting point. All architectural decisions must favor convention over configuration while remaining removable/replaceable by downstream projects.

## Goals / Non-Goals

**Goals:**
- Provide a working full-stack app (web + mobile + API + auth) from a single `docker compose up` + `turbo dev`
- Type-safe integration between Django API and TypeScript frontends via OpenAPI spec generation
- Dual auth strategy (session cookies for web, JWT for mobile) sharing one Django Allauth backend
- Shared packages consumed by both web and mobile (api-client, validation, ui primitives, business logic)
- Optional AI module (PGVector + LangGraph) that can be cleanly removed
- CLI scaffolder that generates new projects with unique secrets and renamed packages
- CI/CD pipeline that catches type staleness, lint violations, and test failures

**Non-Goals:**
- Billing/Stripe integration (too product-specific)
- Multi-tenancy (depends on product's tenancy model)
- Social OAuth pre-configured (requires per-product API keys)
- Landing page / marketing site
- i18n / localization
- RBAC / permissions system
- Real-time / WebSockets
- Custom admin dashboard (Django admin suffices)

## Decisions

### D1: Monorepo structure — Turborepo + pnpm for JS/TS, Django outside pnpm workspaces
**Rationale**: Turborepo excels at JS/TS task orchestration but has no Python support. Django is managed by `uv` as a standalone project at `apps/api/`. Root `package.json` scripts bridge the two worlds with `turbo dev` starting all services.
**Alternatives**: Nx (heavier, unnecessary for this scope), Bazel (enterprise-grade overkill), separate repos (loses type sharing benefits).

### D2: OpenAPI-first type generation pipeline
**Rationale**: Django Ninja Extra auto-generates OpenAPI 3.1 from Python type hints. `openapi-typescript` converts this to TypeScript types. `openapi-fetch` consumes those types for a fully typed API client. This is a one-directional pipeline (Python → TypeScript) that avoids manual type synchronization.
**Alternatives**: tRPC (requires Node.js backend), GraphQL (overengineered for most SaaS), manual TypeScript types (drift risk).

### D3: Django Allauth headless mode for auth
**Rationale**: Allauth handles email verification, password reset, session management, and has a headless API mode purpose-built for SPA/mobile clients. Avoids reimplementing auth flows.
**Alternatives**: django-rest-auth (less maintained), custom JWT auth (reinventing the wheel), Auth0/Clerk (external dependency, vendor lock-in).

### D4: Dual auth — session cookies (web) + JWT (mobile)
**Rationale**: Next.js works best with HttpOnly session cookies (CSRF protection, no client-side token storage). Expo needs JWT because mobile apps can't rely on cookies. Both strategies authenticate against the same Django Allauth backend.
**Alternatives**: JWT-only (loses cookie security benefits for web), session-only (doesn't work for mobile).

### D5: Selective React Native Web for UI primitives only
**Rationale**: Share only low-level primitives (Button, Text, Input, Card) via React Native Web. Web app uses Shadcn/ui for its full component library; mobile uses RN components. This avoids the "lowest common denominator" problem where shared components can't leverage platform strengths.
**Alternatives**: Full RNW sharing (degrades both platforms), no sharing (duplication), Tamagui (adds complexity without clear benefit at this scale).

### D6: Hybrid Docker development — infra in Docker, apps on host
**Rationale**: Postgres and Redis run in Docker (consistent, no local install). Django, Next.js, and Expo run on host for fast hot reload and native tooling (Expo requires host execution). `turbo dev` orchestrates all host processes.
**Alternatives**: Everything in Docker (slow HMR, Expo incompatible), everything on host (Postgres/Redis install burden).

### D7: Layered Django architecture — Controllers / Services / ORM
**Rationale**: Ninja Extra controllers handle HTTP concerns. Service layer contains business logic (testable without HTTP). ORM layer handles data access. This prevents fat views and makes logic reusable across API endpoints, Celery tasks, and management commands.
**Alternatives**: Fat views (common but unmaintainable), DDD (overengineered for template scope).

### D8: PGVector with HNSW indexes for AI module
**Rationale**: PGVector lives inside the same Postgres instance (no separate vector DB). HNSW indexes provide fast approximate nearest neighbor search suitable for most SaaS use cases. The AI module is isolated in `apps/api/apps/ai/` for clean removal.
**Alternatives**: Pinecone/Weaviate (external dependency), IVFFlat indexes (slower for common query patterns).

### D9: Build order follows dependency graph
**Rationale**: Phase 1 (monorepo) → Phase 2 (API/auth) → Phase 3 (shared packages) → Phase 4 (web) → Phase 5 (mobile) → Phase 6 (AI, parallel with 4-5) → Phase 7 (CI/CD) → Phase 8 (CLI). Each phase depends on the previous one being verifiable.

## Risks / Trade-offs

- **[Django Ninja Extra maturity]** → Smaller ecosystem than DRF. Mitigation: Ninja Extra is actively maintained, has growing adoption, and the OpenAPI-first approach is its key advantage.
- **[Expo SDK version churn]** → Expo releases frequently with breaking changes. Mitigation: Pin to a specific SDK version, document upgrade path.
- **[React Native Web limitations]** → Not all RN components work on web. Mitigation: Only share primitives (D5), use platform-specific UI libraries for complex components.
- **[OpenAPI pipeline fragility]** → Generated types can go stale if pipeline isn't enforced. Mitigation: CI gate checks type freshness (DX-03).
- **[Custom User model timing]** → Must be created before first migration or requires DB reset. Mitigation: Phase 2 creates custom User model as first action.
- **[AI module coupling risk]** → Optional module could leak dependencies into core. Mitigation: Strict isolation in `apps/api/apps/ai/`, removal verification test.
- **[Monorepo complexity]** → Turborepo + Docker + multiple runtimes = steep learning curve. Mitigation: Comprehensive `.env.example` files, clear error messages, `turbo dev` as single entry point.
