# Project Research Summary

**Project:** Foundation Template - Full-Stack SaaS Starter
**Domain:** Monorepo SaaS boilerplate (Django Ninja Extra + Next.js 15 + Expo + Turborepo)
**Researched:** 2026-02-08
**Confidence:** MEDIUM

## Executive Summary

This is a full-stack SaaS foundation template built as a Turborepo monorepo with Django Ninja Extra (Python) backend, Next.js 15 (App Router) web frontend, and Expo React Native mobile app. Research reveals this template occupies a unique competitive position: it's the **only template offering web + mobile + API from a single codebase with type-safe OpenAPI-generated bindings**. Most SaaS templates ship web-only; none ship mobile. This is the core differentiator.

The recommended approach centers on **type safety as the integration layer**. Django Ninja Extra auto-generates OpenAPI specs from Pydantic schemas. TypeScript types generate from that spec via openapi-typescript. Shared monorepo packages (api-client, validation, ui-primitives, business-logic) enable genuine cross-platform code sharing. The architecture is backend-heavy (Django owns all business logic) with thin frontends consuming a type-safe API. Docker Compose orchestrates local development, but frontends run natively (not in Docker) for hot-reload performance.

The biggest risks are **auth complexity across three platforms** (Next.js SSR, Next.js client, Expo mobile) and **React Native Web overreach** (trying to share too many components leads to platform-conditional hell). Mitigation: dual auth strategy (session cookies for web, JWT for mobile) implemented in Phase 2, and strict sharing boundaries (primitives only) enforced in Phase 3.

## Key Findings

### Recommended Stack

Research confirms the decided core stack (Django Ninja Extra, Next.js 15, Expo, Turborepo) is sound. The critical supporting stack decisions are:

**Type generation and API client:**
- **openapi-typescript** + **openapi-fetch** — generates TypeScript types from Django's OpenAPI spec; lightweight fetch wrapper with zero runtime overhead. This is the bridge between Python and TypeScript.
- **Zod** — shared validation schemas across web and mobile. Works identically on both platforms.

**Monorepo orchestration:**
- **Turborepo 2.x** — manages JS/TS workspaces. Django is NOT a Turborepo workspace (Python dependencies managed separately by uv) but participates via explicit `inputs`/`outputs` in turbo.json.
- **pnpm 9.x** — workspace package manager. Fast, strict dependency resolution.
- **uv** — Python package manager (10-100x faster than pip). Modern alternative to poetry.

**Cross-platform UI:**
- **React Native Web** — enables sharing foundational UI primitives (Button, Text, Input) between Next.js and Expo. Scope limited to primitives only; complex components stay platform-specific.
- **Shadcn/ui** + **Tailwind CSS** — web-specific component library built on Radix UI primitives.

**Code quality:**
- **ruff** — replaces black + flake8 + isort; single tool for Python linting and formatting.
- **ESLint 9 flat config** + **Prettier** — JS/TS linting and formatting.
- **pre-commit** — orchestrates hooks across Python and JS codebases.

**Infrastructure:**
- **Docker Compose** — Postgres 16 (pgvector/pgvector image), Redis, Django API in containers. Next.js and Expo run natively on host for dev performance.
- **GitHub Actions** — three parallel jobs (api, web, mobile) for fast CI.

**Critical decisions:**
- psycopg3 (package name: `psycopg[binary]`) over psycopg2 — modern, actively maintained
- HNSW indexes over IVFFlat for PGVector — no training needed, better for incremental inserts
- Session auth for web (cookies), JWT for mobile (tokens) — dual strategy, not either/or

**Versions require verification** (training data cutoff May 2025) — all package versions should be checked before implementation.

### Expected Features

Research compared this template against 6 major competitors (SaaS Pegasus, ShipFast, Wasp OpenSaaS, create-t3-app, Makerkit, Supastarter). Key findings:

**Must have (table stakes):**
- Email/password authentication with password reset
- User profile and account settings
- Database with migrations (Postgres + Django ORM)
- API layer with typed endpoints (Django Ninja + OpenAPI spec)
- Frontend with component library (Next.js 15 + Shadcn/ui)
- Development environment (docker compose up works)
- Environment variable management (.env.example, validation)
- Basic layout/app shell (authenticated + unauthenticated layouts)
- Health check endpoint for deployment
- Code quality tooling (ruff, eslint, prettier, pre-commit hooks)
- Dark mode

**Should have (competitive differentiation):**
- **Mobile app (Expo)** — NO competitor ships this. Unique differentiator.
- **Auto-generated TypeScript from OpenAPI** — Django-to-TypeScript type sync without tRPC. Rare in Django templates.
- **Shared monorepo packages** — api-client, schemas, ui-primitives, business-logic shared between web and mobile. Eliminates duplication.
- **Full-stack test suite** — pytest (backend), vitest (web), detox (mobile) with CI integration. Most templates ship zero tests.
- **CI/CD pipeline** — GitHub Actions with lint/test/build for all three platforms.
- **Docker-first with hot reload** — complete local dev environment in one command.
- **Optional AI module** — LangGraph + PGVector scaffolding that can be removed by CLI scaffolder.

**Defer to v2+ (explicitly excluded as anti-features):**
- Built-in billing/Stripe — too product-specific; constrains pricing models
- Multi-tenancy baked in — different products have wildly different tenant models
- Landing page/marketing site — every product rewrites this anyway; pure bloat
- Blog/CMS — adds complexity for a feature most SaaS products don't need
- Social OAuth providers pre-configured — requires per-product setup anyway; false sense of "it works"
- Email service integration — provider choice is product-specific
- Analytics integration — same rationale
- i18n — most products start in one language; retrofitting is easier than maintaining half-implemented i18n
- RBAC/permissions system — deeply product-specific
- Real-time/WebSocket — operational complexity; most SaaS doesn't need it

**Competitive positioning:** "The only full-stack SaaS template with web + mobile + API from one codebase, with type safety across the entire boundary, for solo entrepreneurs who want infrastructure quality without vendor lock-in."

### Architecture Approach

The architecture is **backend-heavy, thin frontends, type-safe integration**. Django owns all business logic, auth, and data persistence. Next.js and Expo are primarily rendering layers that consume the Django API via a shared, type-safe client.

**Major components:**

1. **Django Ninja Extra API** — All business logic, auth (Django Allauth), CRUD operations, OpenAPI spec generation. Layered structure: Controllers (HTTP handling) → Services (business logic) → ORM (data access).

2. **Shared TypeScript packages** — The integration layer:
   - `packages/api-client` — auto-generated types + openapi-fetch client
   - `packages/validation` — Zod schemas shared across web and mobile
   - `packages/ui` — React Native Web primitives (Button, Text, Input only)
   - `packages/business-logic` — React hooks, utilities, constants

3. **Next.js 15 web app** — App Router with Server Components. Uses Shadcn/ui for web-specific UI. Auth via session cookies (httpOnly, same-origin via proxy or subdomain). Middleware handles auth guards.

4. **Expo mobile app** — Managed workflow with Expo Router. Auth via JWT tokens stored in expo-secure-store. Connects directly to Django API (never proxied).

5. **PostgreSQL 16 + PGVector** — Relational data + vector embeddings. PGVector extension pre-installed (pgvector/pgvector Docker image). HNSW indexes for similarity search.

6. **Optional AI module** — LangGraph graphs for agent workflows, embedding pipeline via Celery, vector search endpoints. Entirely in `apps/api/apps/ai/` for clean removal.

**Key patterns:**

- **Backend-for-Frontend (BFF) thin proxy** — Next.js API routes proxy auth requests only (for cookie-to-token translation). Most data fetching is direct client-to-Django.
- **OpenAPI-first type generation** — Django Pydantic schemas → OpenAPI JSON → TypeScript types. Pipeline enforced in CI (fail if generated types are stale).
- **Layered Django apps** — Controllers (Ninja Extra) / Services (business logic) / ORM (data). Never fat controllers.
- **Selective React Native Web sharing** — Only primitives (Text, View, Pressable, Image, TextInput). Platform-specific components stay in their respective apps.

**Critical dependencies:**

- OpenAPI spec generation MUST be implemented before frontend work (types are the contract)
- Shared packages MUST exist before web/mobile apps consume them
- Custom Django user model MUST be created before first migration (cannot change later without painful migration)
- Mobile app depends on web auth being proven first (auth is a vertical slice through the entire stack)

### Critical Pitfalls

Research identified 7 critical pitfalls that cause multi-day debugging or rewrites:

1. **Turborepo cannot orchestrate Python** — treating Django as a JS workspace breaks caching. **Solution:** Django stays outside pnpm workspace; uses explicit `inputs`/`outputs` globs in turbo.json for cache invalidation.

2. **Django Allauth cross-platform auth misconfiguration** — mixing session and token auth without strategy breaks one platform or the other. **Solution:** Dual auth (session cookies for web, JWT for mobile); Next.js proxy for same-origin auth; separate WebAuthProvider and MobileAuthProvider in shared API client.

3. **React Native Web component overreach** — trying to share complex components leads to Platform.OS conditionals everywhere. **Solution:** Share ONLY primitives (Text, View, Pressable, Image, TextInput); use .web.tsx/.native.tsx splits for platform-specific code.

4. **OpenAPI-to-TypeScript pipeline fragility** — schema drift, breaking changes in codegen, nullable/optional inconsistencies. **Solution:** Pin codegen version; commit generated openapi.json; CI gate that fails if types are stale; snapshot comparison in tests.

5. **PGVector wrong index type** — IVFFlat trained on empty data gives terrible recall; wrong operator class (L2 vs cosine) means index isn't used. **Solution:** Use HNSW exclusively; match operator class to distance function; add migration for index creation.

6. **Expo Metro bundler monorepo misconfiguration** — "Unable to resolve module" errors, duplicate React instances, .web.tsx not resolving. **Solution:** Explicit metro.config.js with watchFolders and nodeModulesPaths; verify single React instance.

7. **Docker Compose hot reload silently failing** — file watching doesn't propagate; volume mount performance; platform binary mismatches. **Solution:** Hybrid dev (infra in Docker, apps on host) OR use Docker Compose Watch with polling-based file watchers.

**Top 3 by recovery cost (HIGH):**
- Auth misconfiguration (touches every endpoint, every page, every screen)
- React Native Web overreach (rewriting 50+ components)
- Custom user model not created initially (painful migration if data exists)

## Implications for Roadmap

Based on research, the roadmap must follow the dependency graph discovered in ARCHITECTURE.md. The critical path is: **Monorepo → API Core → Shared Packages → Web/Mobile (parallel)**.

### Suggested Phase Structure

**Phase 1: Monorepo Foundation**
- **Rationale:** Everything else depends on this. Turborepo + pnpm + Docker must work before any app development. Custom Django user model MUST be created before first migration.
- **Delivers:** Turborepo scaffolding, Docker Compose (Postgres, Redis), Django project with custom user model, empty Next.js and Expo apps, shared config packages (tsconfig, eslint).
- **Addresses:** Pitfalls #1 (Turborepo Python integration), #6 (Expo Metro config), #7 (Docker hot reload).
- **Research flag:** Standard patterns; skip research-phase. Well-documented setup.

**Phase 2: API Core + Auth**
- **Rationale:** The API is the integration layer. Without working auth, no frontend can make authenticated requests. Auth is the hardest integration in the entire template (three platforms, CSRF, cookies vs tokens).
- **Delivers:** Django Ninja Extra API with auth endpoints (signup, login, logout, password reset), Django Allauth configured for headless mode, OpenAPI spec export, health check endpoint.
- **Addresses:** Pitfall #2 (auth cross-platform complexity). Must implement dual auth strategy here.
- **Research flag:** NEEDS DEEPER RESEARCH. Auth integration across Django Allauth headless + Next.js + Expo is complex and poorly documented. Plan for 2-3 day research spike during phase planning.

**Phase 3: Shared Packages + Type Generation**
- **Rationale:** Frontends cannot be built without the API client. The type generation pipeline is the backbone of cross-platform type safety.
- **Delivers:** packages/api-client (OpenAPI → TS types + openapi-fetch client), packages/validation (Zod schemas), packages/ui (React Native Web primitives only), packages/business-logic (auth hooks, utilities).
- **Addresses:** Pitfall #4 (OpenAPI pipeline fragility). CI gate added here to enforce type sync.
- **Research flag:** Standard patterns for openapi-typescript. Minor unknowns around Zod schema generation from OpenAPI.

**Phase 4: Web Application**
- **Rationale:** Web first, mobile second. Web proves the auth flow and API integration. Mobile builds on proven patterns.
- **Delivers:** Next.js 15 App Router with auth pages (login, signup, password reset, email verification), dashboard shell, authenticated layout, Shadcn/ui components, middleware for auth guards.
- **Addresses:** Features (table stakes frontend). Validates API client works end-to-end.
- **Research flag:** Standard Next.js 15 patterns. No deep research needed.

**Phase 5: Mobile Application**
- **Rationale:** After web auth is proven, mobile follows the same API integration patterns. Metro bundler config was handled in Phase 1.
- **Delivers:** Expo app with Expo Router, auth screens (login, signup), JWT token management (expo-secure-store), navigation setup, mobile-specific features (push notifications if included).
- **Addresses:** Features (mobile app — unique differentiator). Validates shared packages work cross-platform.
- **Research flag:** Standard Expo patterns. Known risk: React Native Web boundaries must be enforced (Pitfall #3).

**Phase 6: AI Module (Optional)**
- **Rationale:** Optional, removable, high-value differentiation. All code isolated in apps/api/apps/ai/ so CLI scaffolder can exclude it cleanly.
- **Delivers:** PGVector setup (model mixin, embedding field, HNSW index), LangGraph graph skeleton, embedding pipeline (Celery task), AI API endpoints, chat UI (web + mobile).
- **Addresses:** Features (AI module differentiator). Pitfall #5 (PGVector index configuration) must be addressed here.
- **Research flag:** NEEDS DEEPER RESEARCH. LangGraph API evolves rapidly (training data cutoff May 2025). Plan for research spike on LangGraph checkpoint-postgres integration and graph patterns.

**Phase 7: DevEx + CI/CD**
- **Rationale:** Incrementally built alongside phases 1-6, but finalized here. Pre-commit hooks slow down early iteration; enable them once patterns stabilize.
- **Delivers:** GitHub Actions (three parallel jobs: api, web, mobile), pre-commit hooks (ruff, eslint, prettier), production Dockerfiles, deployment guides (Railway, Fly.io, AWS ECS).
- **Addresses:** Features (CI/CD, full test suite). Pitfall #4 enforcement (CI fails on stale types).
- **Research flag:** Standard GitHub Actions patterns.

**Phase 8: CLI Scaffolder**
- **Rationale:** MUST be built LAST. The scaffolder operates on the complete template. Building it early means constant rework as the template evolves.
- **Delivers:** Interactive CLI (cookiecutter or custom Node.js) that asks project name, optional features (include AI?), generates configured project with unique SECRET_KEY, renamed packages, updated configs.
- **Addresses:** UX (template hard to customize). Makes the template actually usable.
- **Research flag:** Standard CLI patterns (inquirer.js, commander.js).

### Phase Ordering Rationale

- **Phase 1 MUST be first:** Custom user model and monorepo structure are foundational. Cannot change later without rewrites.
- **Phase 2 (Auth) MUST be second:** Auth is a vertical slice. Frontends cannot be built without working auth endpoints.
- **Phase 3 MUST precede 4/5:** Shared packages are the integration layer. Frontends depend on them.
- **Phases 4 and 5 can parallelize** after Phase 3 completes. However, web first is recommended to prove the API integration before adding mobile complexity.
- **Phase 6 (AI) is orthogonal:** Can be built anytime after Phase 2 (API exists). But placing it after mobile ensures the core template is solid before adding optional complexity.
- **Phase 7 (CI/CD) is incremental:** Can start in Phase 1 (basic linting) and expand through Phase 6. Finalized after all phases complete.
- **Phase 8 (CLI) MUST be last:** The scaffolder depends on a stable template.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 2 (Auth)** — Django Allauth headless mode + Next.js + Expo integration is complex. Sparse documentation. CSRF/cookie/token handling across three platforms has many edge cases. Plan for 2-3 day research spike.
- **Phase 6 (AI)** — LangGraph API evolves rapidly. Training data cutoff May 2025; verify current API. Research LangGraph checkpoint-postgres integration patterns, graph composition best practices, streaming response handling.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Monorepo)** — Turborepo + pnpm + Docker Compose are well-documented. Metro config for Expo monorepo has established patterns.
- **Phase 3 (Shared Packages)** — openapi-typescript + openapi-fetch are stable. Zod is mature. React Native Web primitives are well-understood.
- **Phase 4 (Web)** — Next.js 15 App Router is heavily documented. Shadcn/ui has extensive examples.
- **Phase 5 (Mobile)** — Expo managed workflow is straightforward. Expo Router follows Next.js conventions.
- **Phase 7 (CI/CD)** — GitHub Actions has abundant examples for monorepo CI.
- **Phase 8 (CLI)** — CLI scaffolding is a solved problem (cookiecutter, degit, plop).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Core stack decisions are sound. Supporting libraries (openapi-typescript, ruff, uv) are stable. Version numbers require verification (training cutoff May 2025). |
| Features | MEDIUM | Competitor analysis is based on training data (stable market, slow feature evolution). Table stakes vs differentiators are well-established. Anti-features rationale is opinionated but defensible. |
| Architecture | MEDIUM | Django Ninja + Next.js + Expo patterns are well-documented. React Native Web boundaries are well-understood. Turborepo + Python integration requires explicit config but is proven. |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls are based on established pain points (auth complexity, RN Web overreach, PGVector indexing). Specific config details (Django Allauth headless, Metro bundler) should be validated against current docs. |

**Overall confidence:** MEDIUM

Research is based on training data through May 2025. WebSearch and WebFetch were unavailable. Core patterns (monorepo structure, Django layered architecture, OpenAPI type generation) are stable and unlikely to have changed significantly. Rapidly evolving areas (LangGraph API, Expo SDK, Django Allauth headless mode) require validation during implementation.

### Gaps to Address

**Gaps identified during research:**

1. **Django Allauth headless mode API** — Configuration keys (HEADLESS_FRONTEND_URLS, HEADLESS_ONLY) should be verified against current Django Allauth docs. The headless mode is relatively new (added ~2023-2024) and may have evolved.

2. **LangGraph checkpoint-postgres integration** — Package name, API, and connection pooling patterns should be researched during Phase 6 planning. Training data may not reflect current API.

3. **Expo SDK version compatibility** — Research assumes Expo SDK 52+. Verify React Native 0.76+ compatibility and New Architecture defaults with current Expo SDK (likely 53+ by implementation time).

4. **openapi-typescript v7+ breaking changes** — Verify generated output format is stable. Pin version in package.json to avoid surprise breakage.

5. **ESLint 9 flat config stability** — Verify flat config is the recommended approach (it was in training data, but ESLint 9 was relatively new in May 2025).

6. **Docker Compose Watch syntax** — Feature introduced in Docker Compose v2.22+. Verify current syntax for develop.watch configuration if using full-Docker dev approach.

**How to handle during planning:**
- Phase 2 (Auth) planning: 2-3 day research spike on Django Allauth headless + Next.js + Expo integration. Prototype auth flow before committing to implementation.
- Phase 6 (AI) planning: Research spike on LangGraph current API, checkpoint patterns, streaming responses.
- Phase 1-8: Verify all package versions at phase start (npm view, pip index). Update versions in implementation, not research docs.

## Sources

### Primary (HIGH confidence)
- Django documentation — custom user model requirements, layered app structure
- PGVector README — HNSW vs IVFFlat, operator classes, index parameters
- React Native Web documentation — component compatibility matrix, limitations
- Docker official images — pgvector/pgvector, redis, postgres, python, node

### Secondary (MEDIUM confidence)
- Turborepo documentation (turbo.build) — monorepo structure, task orchestration, caching
- Django Ninja Extra documentation — controller-based API, Pydantic schema integration
- Next.js 15 documentation — App Router, Server Components, middleware
- Expo documentation — monorepo Metro config, managed workflow, Expo Router
- openapi-typescript documentation — type generation from OpenAPI 3.x
- SaaS template competitor analysis (Pegasus, ShipFast, Wasp, T3, Makerkit, Supastarter) — feature matrix, positioning

### Tertiary (LOW confidence, needs validation)
- Django Allauth headless mode — configuration keys, token-based auth endpoints
- LangGraph documentation — checkpoint-postgres package, graph composition, streaming
- NativeWind v4 — Tailwind CSS for React Native Web cross-platform styling
- Expo SDK 52+ — React Native 0.76 compatibility, New Architecture defaults
- Docker Compose Watch — develop.watch syntax for hot reload
- ESLint 9 flat config — stability of new config format

---
*Research completed: 2026-02-08*
*Ready for roadmap: YES*

**Next step:** Orchestrator proceeds to requirements definition (REQUIREMENTS.md) using this synthesis as context.
