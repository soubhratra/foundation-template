# Roadmap: Foundation Template

## Overview

This roadmap delivers a full-stack SaaS starter kit (Django Ninja Extra + Next.js 15 + Expo + Turborepo) that takes a new project from zero to running app in under 5 minutes. The 8 phases follow the dependency graph: monorepo scaffolding first, then API/auth backend, then shared packages as the type-safe integration layer, then web and mobile frontends (sequential -- web proves auth before mobile adds JWT complexity), then the optional AI module, then DevEx/CI hardening, and finally the CLI scaffolder that operates on the finished template. Every phase delivers a coherent, verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Monorepo Foundation** - Turborepo monorepo with Docker Compose, Django project, empty frontend apps, and shared configs
- [ ] **Phase 2: API Core + Auth Backend** - Django Ninja Extra API with auth endpoints, OpenAPI spec, and dual auth strategy
- [ ] **Phase 3: Shared Packages + Type Generation** - Type-safe integration layer: API client, validation schemas, UI primitives, business logic
- [ ] **Phase 4: Web Application** - Next.js 15 App Router with complete auth flow, dashboard shell, and user management
- [ ] **Phase 5: Mobile Application** - Expo app with auth screens, JWT token management, and shared package consumption
- [ ] **Phase 6: AI Module** - Optional PGVector + LangGraph module with embedding pipeline and vector search
- [ ] **Phase 7: DevEx + CI/CD** - GitHub Actions, pre-commit hooks, test suites, production Dockerfiles, type checking
- [ ] **Phase 8: CLI Scaffolder** - Interactive CLI that generates new projects from the finished template

## Phase Details

### Phase 1: Monorepo Foundation
**Goal**: Developer can clone the repo, run `docker compose up`, and have Postgres + Redis running with an empty Django project, Next.js app, and Expo app all hot-reloading in the monorepo
**Depends on**: Nothing (first phase)
**Requirements**: MONO-01, MONO-02, MONO-03, MONO-04, MONO-05, MONO-06, MONO-07, MONO-08
**Success Criteria** (what must be TRUE):
  1. `pnpm install` at repo root installs all JS/TS dependencies and Turborepo orchestrates workspace tasks
  2. `docker compose up` starts Postgres 16 with PGVector and Redis; Django can connect and run migrations
  3. `turbo dev` starts Django (with hot reload), Next.js (with hot reload), and Expo (with hot reload) simultaneously
  4. Shared config packages (tsconfig, eslint) are consumed by all JS/TS apps without errors
  5. `.env.example` files exist for all apps; missing required env vars produce clear error messages
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md -- Turborepo + pnpm workspace scaffolding with shared config packages (Wave 1)
- [ ] 01-02-PLAN.md -- Docker Compose (Postgres + PGVector + Redis) and Django project with custom user model (Wave 2)
- [x] 01-03-PLAN.md -- Next.js and Expo app scaffolds with Metro monorepo config (Wave 2)
- [ ] 01-04-PLAN.md -- Hybrid dev orchestration (turbo dev) and environment variable management (Wave 3)

### Phase 2: API Core + Auth Backend
**Goal**: Django API serves authenticated endpoints with auto-generated OpenAPI spec; dual auth strategy (session cookies for web, JWT for mobile) is configured and testable via API client
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, API-09, AUTH-08, AUTH-09
**Success Criteria** (what must be TRUE):
  1. Django Ninja Extra API serves endpoints at /api/ with auto-generated OpenAPI 3.1 spec viewable at /api/docs
  2. Health check endpoint returns service status including database connectivity
  3. OpenAPI JSON spec is exported to a file that downstream type generation can consume
  4. Django Allauth headless mode accepts signup, login, logout, and password reset requests via API (no server-rendered forms)
  5. Session cookie auth and JWT token auth both work against the same endpoints (dual strategy verified via manual API testing)
**Plans**: TBD

Plans:
- [ ] 02-01: Django Ninja Extra API scaffold with layered architecture and settings split
- [ ] 02-02: Custom user model, migrations, health check, and admin configuration
- [ ] 02-03: Django Allauth headless configuration with dual auth strategy
- [ ] 02-04: OpenAPI spec export and CORS configuration

### Phase 3: Shared Packages + Type Generation
**Goal**: Shared monorepo packages provide type-safe API client, validation schemas, UI primitives, and business logic hooks that both web and mobile apps can import and use
**Depends on**: Phase 2
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, PKG-06, PKG-07, PKG-08
**Success Criteria** (what must be TRUE):
  1. Running the type generation pipeline produces TypeScript types from the Django OpenAPI spec; types reflect actual API endpoints and schemas
  2. `packages/api-client` exports a typed openapi-fetch client that provides autocomplete for API paths and request/response types
  3. `packages/validation` exports Zod schemas for auth forms (signup, login, profile) usable in both web and mobile
  4. `packages/ui` exports React Native Web primitives (Button, Text, Input, Card) that render on both web and mobile without platform conditionals
  5. `packages/business-logic` exports shared auth hooks (useAuth, useUser) and utility functions importable by both apps
**Plans**: TBD

Plans:
- [ ] 03-01: Type generation pipeline (OpenAPI spec to TypeScript types via openapi-typescript)
- [ ] 03-02: API client package with openapi-fetch typed wrapper
- [ ] 03-03: Validation package with Zod schemas for auth and profile forms
- [ ] 03-04: UI primitives package with React Native Web components
- [ ] 03-05: Business logic package with auth hooks and shared utilities

### Phase 4: Web Application
**Goal**: Users can sign up, log in, manage their account, and navigate an authenticated dashboard in the Next.js web app -- the complete auth flow works end-to-end from browser to Django API
**Depends on**: Phase 3
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05, WEB-06, WEB-07, WEB-08, WEB-09, AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06
**Success Criteria** (what must be TRUE):
  1. User can sign up with email/password and receives email verification; can log in after verification and stays logged in across browser refreshes (session cookies)
  2. User can log out from any authenticated page; can reset a forgotten password via email link
  3. Unauthenticated users are redirected to login; authenticated users see the dashboard shell with navigation
  4. User can view and update their profile/account settings from the settings page
  5. Dark mode toggle works with system preference detection; all pages render correctly in both themes
**Plans**: TBD

Plans:
- [ ] 04-01: Next.js 15 App Router setup with Shadcn/ui, Tailwind CSS, and layouts (auth + unauth)
- [ ] 04-02: Auth pages (login, signup, password reset, email verification) with form validation
- [ ] 04-03: Auth middleware, session management, and protected route guards
- [ ] 04-04: Dashboard shell, user profile/settings page, and dark mode
- [ ] 04-05: Server Components with typed API calls via shared api-client

### Phase 5: Mobile Application
**Goal**: Users can sign up, log in, and navigate an authenticated tab-based mobile app in Expo -- consuming the same shared packages as web, with JWT token persistence across app restarts
**Depends on**: Phase 4
**Requirements**: MOB-01, MOB-02, MOB-03, MOB-04, MOB-05, MOB-06, MOB-07, MOB-08, AUTH-07
**Success Criteria** (what must be TRUE):
  1. User can sign up and log in on mobile; JWT token is stored in expo-secure-store and persists across app restarts
  2. Authenticated users see tab-based navigation; unauthenticated users see auth screens
  3. Mobile app uses the same shared API client, validation schemas, and UI primitives as web (packages/api-client, packages/validation, packages/ui)
  4. User can view and update profile/account settings on mobile
**Plans**: TBD

Plans:
- [ ] 05-01: Expo Router navigation setup with auth and tab-based layouts
- [ ] 05-02: Auth screens (login, signup) with shared validation and API client
- [ ] 05-03: JWT token management with expo-secure-store
- [ ] 05-04: Profile/settings screen and shared UI primitives integration

### Phase 6: AI Module
**Goal**: An optional, fully isolated AI module provides vector search and LangGraph agent scaffolding that can be cleanly removed from the template
**Depends on**: Phase 2
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05, AI-06
**Success Criteria** (what must be TRUE):
  1. PGVector extension is enabled; Django models can declare embedding fields with the provided mixin; HNSW index is created via migration
  2. LangGraph agent scaffold exists with at least one working example graph that can be invoked via API endpoint
  3. Embedding pipeline runs as a Celery background task that generates and stores vector embeddings
  4. Vector search API endpoint accepts a query and returns results ranked by similarity
  5. Entire AI module lives in apps/api/apps/ai/ and can be deleted without breaking any other part of the template
**Plans**: TBD

Plans:
- [ ] 06-01: PGVector model mixin, embedding fields, and HNSW index migration
- [ ] 06-02: LangGraph agent scaffold with example graph
- [ ] 06-03: Celery embedding pipeline and vector search API endpoint
- [ ] 06-04: Module isolation verification (clean removal test)

### Phase 7: DevEx + CI/CD
**Goal**: Every push triggers automated linting, type checking, and testing across all three platforms; production Dockerfiles are ready for deployment; developer workflow is enforced by pre-commit hooks
**Depends on**: Phase 5, Phase 6
**Requirements**: DX-01, DX-02, DX-03, DX-04, DX-05, DX-06, DX-07, DX-08
**Success Criteria** (what must be TRUE):
  1. Pre-commit hooks run ruff (Python), eslint + prettier (JS/TS) on every commit; violations block the commit
  2. GitHub Actions runs three parallel jobs (api, web, mobile) on every push; each job lints, type-checks, and runs tests
  3. CI fails if generated TypeScript types are stale relative to the current OpenAPI spec
  4. pytest, vitest, and detox test suites each contain example tests that pass; `turbo test` runs all three
  5. Production Dockerfiles for Django API and Next.js app build successfully and produce runnable images
**Plans**: TBD

Plans:
- [ ] 07-01: Pre-commit hooks (ruff, eslint, prettier) and type checking enforcement (mypy, tsc)
- [ ] 07-02: pytest, vitest, and detox test suites with example tests
- [ ] 07-03: GitHub Actions workflow with parallel jobs and type staleness gate
- [ ] 07-04: Production Dockerfiles for Django API and Next.js app

### Phase 8: CLI Scaffolder
**Goal**: A developer can run a single CLI command that asks for project name and feature selections, then generates a fully configured new project that passes all linting and type checks out of the box
**Depends on**: Phase 7
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, AI-07
**Success Criteria** (what must be TRUE):
  1. Interactive CLI prompts for project name and optional features (include AI module? yes/no)
  2. Generated project directory has all package names, Django settings, and config files updated to the new project name
  3. Generated project has a unique Django SECRET_KEY and other secrets (not the template defaults)
  4. Generated project passes all linting (ruff, eslint, prettier) and type checks (mypy, tsc) without modifications
  5. When AI module is excluded, all AI-related code, dependencies, and configuration are cleanly removed from the generated project
**Plans**: TBD

Plans:
- [ ] 08-01: CLI framework with interactive prompts for project name and feature selection
- [ ] 08-02: Template generation engine (file copying, renaming, secret generation)
- [ ] 08-03: AI module exclusion logic and generated project validation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8
Note: Phase 6 (AI) depends only on Phase 2; it could execute in parallel with Phases 4-5 if desired.

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Monorepo Foundation | 2/4 | In progress | - |
| 2. API Core + Auth Backend | 0/4 | Not started | - |
| 3. Shared Packages + Type Generation | 0/5 | Not started | - |
| 4. Web Application | 0/5 | Not started | - |
| 5. Mobile Application | 0/4 | Not started | - |
| 6. AI Module | 0/4 | Not started | - |
| 7. DevEx + CI/CD | 0/4 | Not started | - |
| 8. CLI Scaffolder | 0/3 | Not started | - |

---
*Roadmap created: 2026-02-08*
*Total requirements: 71 | Mapped: 71/71 | Coverage: 100%*
