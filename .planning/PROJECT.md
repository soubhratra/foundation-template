# Foundation Template

## What This Is

A reusable full-stack SaaS starter kit for a solo technical entrepreneur building multiple products. Clone the repo, run a CLI scaffolder to set project name and features, `docker compose up`, and you have a running web app + mobile app + API + database with authentication already working. Every new SaaS product starts from this template.

## Core Value

A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.

## Requirements

### Validated (v1.0)

- ✓ Turborepo monorepo with Django backend, Next.js frontend, Expo mobile app, and shared packages — v1.0
- ✓ Django Ninja Extra API with auto-generated OpenAPI 3.1 spec — v1.0
- ✓ Next.js 15 App Router frontend with Shadcn/ui and Tailwind CSS — v1.0
- ✓ React Native Expo (managed workflow) mobile app with navigation and auth screens — v1.0
- ✓ Django Allauth authentication with email/password, session management — v1.0
- ✓ Auth flow wired end-to-end: signup, login, logout, password reset across web and mobile — v1.0
- ✓ Postgres 16+ via Docker for local development — v1.0
- ✓ PGVector extension configured (optional AI module) — v1.0
- ✓ Auto-generated TypeScript types from Django Ninja OpenAPI spec — v1.0
- ✓ Shared monorepo packages: API client, Zod validation schemas, UI primitives (React Native Web), business logic/hooks/utils — v1.0
- ✓ One-command local setup: `docker compose up` runs everything — v1.0
- ✓ Hot reload for frontend (Next.js), backend (Django), and mobile (Expo) — v1.0
- ✓ CI/CD with GitHub Actions: lint, test, build on every push — v1.0
- ✓ Code quality gates: pre-commit hooks, ruff (Python), eslint + prettier (JS/TS), type checking — v1.0
- ✓ pytest test suite for backend, vitest for frontend, detox for mobile — v1.0
- ✓ Optional AI module: LangGraph agent scaffold, embedding pipeline, vector search API — removable if not needed — v1.0
- ✓ CLI scaffolder: run a command that asks project name and optional features, generates a new project from the template — v1.0
- ✓ Docker-first deployment: Docker Compose for local, Dockerfiles ready for any cloud provider — v1.0
- ✓ User management: basic user model, profile, account settings pages — v1.0

### Active (v1.1+)

(None defined yet — run `/gsd:new-milestone` to define next milestone requirements)

### Out of Scope

- Billing/payments — too product-specific, each project adds its own
- Multi-tenancy — each project decides its own tenancy model
- Product-specific business logic — template provides infrastructure, not features
- Specific cloud provider lock-in — Docker-first, deploy anywhere
- Admin dashboard — Django admin is sufficient for template
- Real-time features (WebSockets) — product-specific, add per-project
- Email service integration — template stubs email, each project configures provider

## Context

- Solo technical entrepreneur building multiple SaaS products
- Template is the highest-leverage investment — every hour here saves hours across every future project
- Stack decisions are permanent and non-negotiable (Django Ninja Extra, Next.js, Expo, etc.)
- Django Allauth chosen for auth: native Django, full control, no external auth dependency
- AI is optional because not every SaaS product needs it, but when needed it should be ready
- Shared packages across web and mobile reduce duplication: API client, validation, UI primitives, business logic
- Type safety across the stack via auto-generated TypeScript from Django Ninja OpenAPI
- Developer experience is critical — this template will be used repeatedly, friction compounds

## Constraints

- **Package managers**: pnpm for JS/TS, uv/pip for Python — no alternatives
- **Monorepo tool**: Turborepo for JS/TS workspaces
- **Database**: Postgres 16+ with PGVector extension
- **Python framework**: Django Ninja Extra (not DRF, not FastAPI)
- **Frontend framework**: Next.js 15+ with App Router (not Pages Router)
- **Mobile framework**: React Native with Expo managed workflow
- **UI library**: Shadcn/ui + Tailwind CSS (not Material UI, not Chakra)
- **AI orchestration**: LangGraph (not LangChain agents, not custom)
- **Testing**: pytest (backend), vitest (frontend), detox (mobile) — non-negotiable

## Key Decisions

| Decision                        | Rationale                                                                     | Outcome                                                                                    |
| ------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Django Allauth for auth         | Native Django, full control, no external auth service dependency              | ✓ Good — headless mode + dual auth (session+JWT) works cleanly                             |
| AI as optional module           | Not every SaaS needs AI; pluggable avoids bloat                               | ✓ Good — CLI scaffolder removes AI module cleanly via feature flag                         |
| No billing in template          | Too product-specific; each SaaS has different pricing models                  | ✓ Good — confirmed valid; each product adds its own                                        |
| No multi-tenancy in template    | Tenancy model depends on product; template shouldn't constrain                | ✓ Good — confirmed valid                                                                   |
| CLI scaffolder for new projects | Better than GitHub template — can customize features, names, configs          | ✓ Good — `create-foundation-app` with validation + rollback shipped                        |
| Auto-generated TS from OpenAPI  | Single source of truth for API types; Django Ninja generates OpenAPI natively | ✓ Good — but Allauth headless endpoints missing from spec; manual fetch workaround applied |
| Docker-first deployment         | Maximum flexibility across cloud providers; no vendor lock-in                 | ✓ Good — multi-stage Dockerfiles ship in Phase 7                                           |
| React Native Web for shared UI  | Share component primitives across web and mobile in monorepo                  | ✓ Good — packages/ui ships shared primitives consumed by both apps                         |
| Tailwind CSS 3.4 (not 4)        | Tailwind 4 preview crashes Next.js PostCSS pipeline                           | ⚠️ Revisit — upgrade to Tailwind 4 when stable release ships                               |
| HS256 JWT (not RSA)             | Avoids RSA key provisioning complexity in template scaffolding                | ✓ Good — appropriate for template; each product can upgrade                                |

## Current State (v1.0)

- **Version shipped:** v1.0 (2026-03-07)
- **Codebase:** ~162k LOC Python, ~27k LOC TypeScript across 504 files
- **Stack:** Django Ninja Extra + Next.js 15 + Expo SDK 53 + Turborepo + pnpm
- **CLI:** `create-foundation-app` — interactive scaffolder with feature removal, validation, rollback
- **Next milestone:** Undefined — run `/gsd:new-milestone` to define

---

_Last updated: 2026-03-07 after v1.0 milestone_
