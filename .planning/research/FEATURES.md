# Feature Research: SaaS Starter Kit / Foundation Template

**Domain:** Full-stack SaaS boilerplate / starter template (not a product -- a foundation for building products)
**Researched:** 2026-02-08
**Confidence:** MEDIUM (training data through May 2025; web verification unavailable. SaaS template market is mature and feature expectations are stable, so confidence is reasonable.)

## Competitor Landscape

Before categorizing features, here is what the major SaaS templates in the ecosystem actually ship. This drives the table-stakes vs. differentiator analysis below.

### Competitor Feature Matrix

| Feature | SaaS Pegasus (Django) | ShipFast (Next.js) | Wasp OpenSaaS | create-t3-app | Makerkit (Next.js) | Supastarter (Next.js) | This Template |
|---------|----------------------|-------------------|---------------|---------------|-------------------|----------------------|---------------|
| **Auth (email/password)** | Yes | Yes | Yes | Via NextAuth | Yes | Yes | Yes (Allauth) |
| **Social OAuth** | Yes | Yes | Yes | Via NextAuth | Yes | Yes | No (add per-project) |
| **Billing/Stripe** | Yes | Yes | Yes | No | Yes | Yes | No (intentional) |
| **Teams/Orgs** | Yes | No | No | No | Yes | Yes | No (intentional) |
| **Admin dashboard** | Django Admin | No | Wasp Admin | No | Yes | Yes | Django Admin |
| **Landing page** | Yes | Yes | Yes | No | Yes | Yes | Stub only |
| **Blog/CMS** | Yes | Yes (Markdown) | Yes | No | Yes | Yes | No |
| **Email integration** | Yes (multiple) | Yes (Resend) | Yes | No | Yes | Yes | Stub |
| **SEO optimization** | Yes | Yes | Yes | No | Yes | Yes | Basic meta |
| **API layer** | DRF | Next.js API routes | Wasp operations | tRPC | tRPC/Next API | tRPC | Django Ninja |
| **Auto-generated types** | No | No | Wasp types | tRPC infers | tRPC infers | tRPC infers | Yes (OpenAPI) |
| **Mobile app** | No | No | No | No | No | No | Yes (Expo) |
| **Monorepo** | No | No | No | No | Yes (Turborepo) | Yes (Turborepo) | Yes (Turborepo) |
| **Docker setup** | Yes | Partial | No | No | No | No | Yes (full) |
| **CLI scaffolder** | Yes (cookiecutter) | No | create-wasp | create-t3-app | CLI | CLI | Yes |
| **CI/CD** | GitHub Actions | No | No | No | GitHub Actions | GitHub Actions | Yes |
| **Testing setup** | Yes (pytest) | No | No | No | Partial | Partial | Yes (full stack) |
| **AI module** | No | No | GPT API example | No | No | No | Yes (LangGraph) |
| **Shared packages** | N/A (monolith) | N/A | N/A | N/A | Yes | Yes | Yes |
| **Pre-commit hooks** | Yes | No | No | No | Partial | Partial | Yes |
| **Database migrations** | Yes | Yes (Prisma) | Yes (Prisma) | Prisma optional | Yes | Yes | Yes (Django) |
| **Error tracking** | Sentry | No | Sentry | No | Sentry | Sentry | No (stub) |
| **Analytics** | Plausible/GA | No | Plausible | No | PostHog | PostHog | No (stub) |
| **i18n** | Yes | No | No | No | Yes | Yes | No |
| **Dark mode** | Yes | Yes | Yes | No | Yes | Yes | Yes |
| **RBAC/Permissions** | Yes | No | No | No | Yes | Yes | No (add per-project) |

### Key Observations from Competitor Analysis

1. **Every paid template ships billing.** This template's deliberate exclusion of billing is a bold but defensible choice for a personal-use template -- billing models vary wildly per product. However, it means the template must compensate with excellence elsewhere.

2. **Nobody ships mobile.** Not a single major SaaS template includes a React Native / Expo mobile app. This is the single biggest differentiator available.

3. **Monorepo is emerging but not dominant.** Only Makerkit and Supastarter use Turborepo. Most templates are monoliths or simple single-project setups. Monorepo + shared packages is a genuine differentiator.

4. **Auto-generated types from OpenAPI is rare.** tRPC templates get type safety implicitly, but explicit OpenAPI-to-TypeScript generation across a Django + Next.js boundary is uncommon and valuable.

5. **Testing is consistently weak across templates.** Most templates ship minimal or no test setup. A fully configured test suite across the entire stack is a differentiator.

6. **Docker-first is underserved.** SaaS Pegasus has it, most others do not. Docker-first with hot reload for all services is rare.

---

## Feature Landscape

### Table Stakes (Template Users Expect These)

Features that every SaaS template must have or it feels unfinished. These are the baseline -- users will not choose a template missing these.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Authentication (email/password)** | Universal SaaS requirement. Sign up, log in, log out, password reset. Every template has this. | MEDIUM | Django Allauth handles this. Must work end-to-end across web + mobile + API. Session/token management is the tricky part. |
| **User profile & account settings** | Users need to manage their own data. Every template provides basic profile editing. | LOW | Name, email, password change, avatar. Keep minimal -- products extend this. |
| **Database with migrations** | Every SaaS needs persistent data with schema evolution. | LOW | Postgres 16+ with Django migrations. PGVector extension pre-configured but optional. |
| **API layer with typed endpoints** | Frontend-backend communication is the core of any SaaS. Must be typed and documented. | MEDIUM | Django Ninja Extra generates OpenAPI spec natively. This is the backbone of the auto-generated TypeScript types. |
| **Frontend with component library** | Modern SaaS needs polished UI out of the box. Raw HTML/CSS is not acceptable. | MEDIUM | Next.js 15 + Shadcn/ui + Tailwind CSS. Must include basic layout shell, navigation, auth pages. |
| **Development environment setup** | `git clone && docker compose up` must result in a working app. No manual steps. | MEDIUM | Docker Compose orchestrating Django, Next.js, Postgres, and supporting hot reload for each. |
| **Environment variable management** | Secrets and config must be handled properly from day one. | LOW | `.env.example` files with documentation. Docker Compose reading from `.env`. Validation on startup. |
| **Basic layout / app shell** | A working navigation, sidebar, header/footer. Empty pages feel broken. | LOW | Authenticated layout with sidebar nav, header with user menu. Unauthenticated layout for landing/auth pages. |
| **Database seeding / fixtures** | Template needs demo data for first run. Empty database feels broken. | LOW | Django fixtures or management command that creates a demo user and sample data. |
| **Error handling patterns** | Unhandled errors in a template signal amateur quality. | LOW | Global error boundary (Next.js), Django exception handlers, API error response format standardized. |
| **Code quality tooling** | Linters, formatters, type checking. Non-negotiable for a professional template. | LOW | Ruff (Python), ESLint + Prettier (JS/TS), TypeScript strict mode. Pre-commit hooks to enforce. |
| **README with setup instructions** | Users must understand how to get started. | LOW | Clear getting-started guide, architecture overview, where to find things. |
| **Health check endpoint** | Every deployment needs it. Load balancers, monitoring, Docker HEALTHCHECK. | LOW | Simple `/api/health/` returning 200 with DB connectivity check. |
| **CORS and security headers** | Web apps need proper CORS config and security headers from day one. | LOW | Django CORS headers configured for local dev. CSP, HSTS stubs for production. |
| **Static file serving / asset pipeline** | CSS, JS, images must work in dev and production. | LOW | Next.js handles frontend assets. Django static files configured for API/admin. |
| **Dark mode** | Expected in modern apps. Not having it feels dated. | LOW | Shadcn/ui + Tailwind CSS support dark mode natively. Just wire up the toggle. |

### Differentiators (Competitive Advantage)

Features that set this template apart from competitors. Not expected, but make users choose this template over alternatives.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Mobile app (Expo) in monorepo** | No other SaaS template ships a mobile app. This is the single biggest differentiator. A solo entrepreneur gets web + mobile + API from one codebase. | HIGH | Expo managed workflow with navigation, auth screens, shared API client. Must share auth state with web. React Native Web for shared primitives. |
| **Auto-generated TypeScript from OpenAPI** | Type safety across the Django-to-TypeScript boundary without tRPC. Change a Django Ninja endpoint, TypeScript types update automatically. Zero drift. | MEDIUM | Django Ninja generates OpenAPI spec. Use `openapi-typescript` or similar to generate TS types. Wire into build pipeline or watch mode. |
| **Shared monorepo packages** | API client, Zod schemas, UI primitives, business logic shared between web and mobile. Change once, works everywhere. Eliminates duplication. | HIGH | Turborepo workspaces: `packages/api-client`, `packages/schemas`, `packages/ui`, `packages/shared`. Must handle React Native Web compatibility for UI package. |
| **CLI scaffolder** | Better than GitHub template button. Interactive CLI asks project name, which optional features to include, generates a properly configured project. | MEDIUM | Cookiecutter, degit, or custom Node.js CLI. Must rename packages, update configs, optionally remove AI module. |
| **Full-stack test suite** | Most templates ship zero tests. This ships pytest (backend), vitest (frontend), detox (mobile) with example tests and CI integration. | MEDIUM | Test configuration, example tests for auth flows, CI pipeline running all three. Coverage reporting. |
| **CI/CD pipeline** | GitHub Actions workflows that lint, type-check, test, and build on every push. Most templates do not include this. | LOW | `.github/workflows/` with matrix builds. Separate jobs for backend, frontend, mobile. Cache dependencies. |
| **Optional AI module (LangGraph + PGVector)** | AI is table stakes for many new SaaS products. Having a ready-made agent scaffold, embedding pipeline, and vector search API saves weeks. But making it optional avoids bloat for non-AI products. | HIGH | LangGraph agent skeleton, embedding ingestion pipeline, vector similarity search endpoint. Must be cleanly removable by CLI scaffolder. |
| **Docker-first with full hot reload** | `docker compose up` runs everything with hot reload. Change Django code, see it immediately. Change Next.js code, see it immediately. No local Python/Node install required. | MEDIUM | Docker Compose with volume mounts for hot reload. Watchman or similar for Django. Next.js dev server in Docker. Expo requires some local tooling for simulators. |
| **Pre-commit hooks with full quality gate** | Enforced code quality on every commit. Ruff, ESLint, Prettier, type checking, test running -- all automated. | LOW | Pre-commit framework with hooks for Python and JS/TS. Husky + lint-staged for JS side if needed. |
| **Cross-platform auth flow** | Auth that works identically on web, mobile, and API. Shared auth state, token management, session handling across all three platforms from one auth system. | HIGH | Django Allauth provides the auth backend. Web uses session cookies (or tokens). Mobile uses token-based auth. Shared API client handles auth headers transparently. |
| **OpenAPI documentation UI** | Auto-generated, interactive API docs available at `/api/docs/`. Django Ninja provides this natively. Developers can explore and test API without Postman. | LOW | Django Ninja ships Swagger UI and ReDoc by default. Just ensure it is configured and accessible in development. |

### Anti-Features (Commonly Included, Often Problematic)

Features that many templates include but which cause more problems than they solve, especially in a reusable template context.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Built-in billing / Stripe integration** | "Ship faster" -- most templates sell on having Stripe pre-wired. | Billing is deeply product-specific. Pricing models (per-seat, usage-based, flat, freemium) vary wildly. A template's billing integration constrains product decisions, becomes stale as Stripe APIs evolve, and often needs to be ripped out and redone anyway. For a personal template used across multiple products with different pricing models, embedded billing is a liability. | Provide a `docs/BILLING.md` guide with recommended patterns for adding Stripe/LemonSqueezy. Stub the Django app structure (`apps/billing/`) but leave implementation to each product. |
| **Multi-tenancy baked in** | "Enterprise-ready" -- many templates build teams/orgs/workspaces into the data model from day one. | Multi-tenancy fundamentally shapes the database schema, permissions, and data access patterns. A B2C app, a B2B app, and a marketplace have completely different tenancy models. Baking one in constrains every product to that model. Removing baked-in multi-tenancy is a rewrite. | Document tenancy patterns in `docs/MULTI_TENANCY.md`. Keep the User model clean. Let each product add its own tenant model. |
| **Landing page / marketing site** | Templates like ShipFast sell on "ship in a weekend" including marketing pages. | Landing pages are highly product-specific. A template landing page needs to be completely rewritten for every product. It adds visual noise to the template, creates maintenance burden, and the copy is meaningless placeholder. For a personal template (not selling the template), landing pages are pure waste. | Provide a minimal unauthenticated layout with a single "Welcome" page that redirects to login. Each product builds its own marketing site (or uses a separate marketing site entirely). |
| **Blog / CMS system** | "Content marketing ready" -- looks good on feature lists. | A blog engine adds significant complexity (content models, markdown rendering, image handling, SEO metadata) for a feature that most SaaS products either do not need, handle via a dedicated CMS (Ghost, WordPress, Contentful), or build much later. It is template bloat. | Omit entirely. Products that need a blog can add one or use an external CMS. |
| **Social OAuth providers pre-configured** | "Google login, GitHub login, Apple login" -- impressive feature list. | OAuth providers require external service configuration (client IDs, secrets, callback URLs) that differs per product. Pre-configured providers create a false sense of "it works" but actually need full reconfiguration per deployment. Django Allauth makes adding providers easy -- the template does not need to pre-wire them. | Include Django Allauth with email/password working. Document how to add OAuth providers in `docs/AUTH.md`. The Allauth configuration is minimal per-provider. |
| **Email service integration (Resend, SendGrid, etc.)** | "Transactional email ready" -- every SaaS sends email. | Email providers vary per product (Resend, SendGrid, SES, Postmark). Hardwiring one creates a dependency that may not match the product's needs. Email templates are product-specific (welcome email, invoice email, etc.). | Stub Django's email backend to console output in development. Document email provider setup in `docs/EMAIL.md`. Provide one abstract base email template for consistent styling. |
| **Analytics integration (PostHog, Plausible, GA)** | "Know your users from day one." | Analytics providers are a product decision. PostHog self-hosted is very different from Plausible Cloud which is very different from Google Analytics. Pre-wiring one constrains the choice. | Stub analytics as an empty provider pattern: `analytics.track('event', data)` that logs to console in development. Each product wires a real provider. |
| **Internationalization (i18n)** | "Global-ready" -- looks professional. | i18n transforms every string in the application. It adds complexity to every component, every page, every email. Most SaaS products start in one language and add i18n much later (if ever). Having i18n scaffolding but no actual translations creates false structure. Worse, retrofitting real i18n onto a template with half-implemented i18n is harder than adding it fresh. | Omit entirely. Use plain strings. When a product needs i18n, add `next-intl` or Django's built-in i18n at that point. |
| **RBAC / permissions system** | "Enterprise features from day one." | Role-based access control is deeply product-specific. An HR tool, a project management app, and an e-commerce platform have completely different permission models. A generic RBAC system either constrains the product or gets ripped out. | Keep Django's built-in permissions system available but do not build a custom RBAC layer. Document patterns in `docs/PERMISSIONS.md`. Each product defines its own roles and permissions. |
| **Real-time / WebSocket support** | "Modern apps are real-time." | WebSocket infrastructure (Django Channels, Redis pub/sub) adds significant operational complexity. Most SaaS features work fine with polling or SSE. Real-time is a product-specific decision (chat needs it, dashboards maybe, CRUD apps do not). | Omit. If a product needs real-time, add Django Channels at that point. The Docker setup can easily add Redis. |
| **Error tracking pre-wired (Sentry)** | "Production-ready monitoring." | Sentry DSN is product-specific. Pre-wiring Sentry means the template has a dependency on a specific monitoring vendor. The configuration is trivial (one DSN env var) and better done per-product. | Stub error reporting as middleware that logs to console. Document Sentry setup in `docs/MONITORING.md` (5-minute setup). |
| **Comprehensive admin dashboard** | "Manage your app" -- custom React-based admin panels. | Django Admin exists and is excellent for development and early-stage products. A custom admin dashboard is a product-specific feature that requires product-specific data models, product-specific actions, and product-specific views. Template admin dashboards are either too generic to be useful or too specific to be reusable. | Use Django Admin. It is built-in, powerful, and customizable. Products that outgrow it can add django-unfold or build a custom admin later. |

---

## Feature Dependencies

```
[Postgres + Docker Compose]
    |
    +---> [Django Project + Settings]
    |         |
    |         +---> [Django Ninja Extra API Layer]
    |         |         |
    |         |         +---> [OpenAPI Spec Generation]
    |         |         |         |
    |         |         |         +---> [Auto-generated TypeScript Types]
    |         |         |                    |
    |         |         |                    +---> [Shared API Client Package]
    |         |         |                              |
    |         |         |                              +---> [Next.js Frontend Auth Flow]
    |         |         |                              +---> [Expo Mobile Auth Flow]
    |         |         |
    |         |         +---> [Health Check Endpoint]
    |         |         +---> [OpenAPI Docs UI (Swagger/ReDoc)]
    |         |
    |         +---> [Django Allauth Authentication]
    |         |         |
    |         |         +---> [Auth API Endpoints (login, signup, logout, reset)]
    |         |         |         |
    |         |         |         +---> [Web Auth Pages (Next.js)]
    |         |         |         +---> [Mobile Auth Screens (Expo)]
    |         |         |
    |         |         +---> [User Model + Profile]
    |         |                   |
    |         |                   +---> [Account Settings Pages (web + mobile)]
    |         |
    |         +---> [PGVector Extension] (optional)
    |                   |
    |                   +---> [AI Module: LangGraph + Embeddings + Vector Search]
    |
    +---> [Turborepo Monorepo Structure]
              |
              +---> [Shared Packages]
              |         |
              |         +---> [packages/schemas (Zod)]
              |         +---> [packages/api-client]
              |         +---> [packages/ui (React Native Web)]
              |         +---> [packages/shared (business logic, utils)]
              |
              +---> [Next.js App (apps/web)]
              |         |
              |         +---> [App Shell / Layout]
              |         +---> [Dark Mode Toggle]
              |         +---> [Error Boundaries]
              |
              +---> [Expo App (apps/mobile)]
              |         |
              |         +---> [Navigation Setup]
              |         +---> [Auth Screens]
              |
              +---> [CI/CD Pipeline (GitHub Actions)]
              +---> [Pre-commit Hooks + Quality Gates]
              +---> [Test Suites (pytest, vitest, detox)]

[CLI Scaffolder] --consumes--> [Entire Template]
    (must be built LAST, after template is stable)
```

### Dependency Notes

- **Auto-generated TS types require OpenAPI spec**: Django Ninja Extra must have endpoints defined before types can be generated. The API layer is foundational.
- **Shared API client requires auto-generated types**: The shared `packages/api-client` depends on the generated TypeScript types from OpenAPI. Types must exist first.
- **Auth flow requires both API endpoints AND frontend pages**: Authentication is a vertical slice through the entire stack. The API auth endpoints (Django Allauth), web auth pages (Next.js), and mobile auth screens (Expo) must all exist and connect.
- **Expo mobile requires shared packages**: The mobile app depends on `packages/api-client` and `packages/ui` for code sharing to work. Shared packages must be structured first.
- **AI module requires PGVector**: The optional AI module depends on PGVector extension being configured in Postgres. But since it is optional, it can be developed in parallel and removed by the CLI scaffolder.
- **CLI scaffolder must be built LAST**: The scaffolder operates on the complete template. It cannot be finalized until the template itself is stable. Building it early means constant rework as the template changes.
- **CI/CD depends on test suites existing**: GitHub Actions workflows need tests to run. The test infrastructure must be in place (even with minimal example tests) before CI/CD is meaningful.
- **Pre-commit hooks conflict with rapid iteration**: During early development, strict pre-commit hooks slow down iteration. Configure them but make them easy to bypass during development (use `--no-verify` or a dev flag).

---

## MVP Definition

### Launch With (v1) -- Core Template

The minimum viable template that demonstrates value. A developer can clone it, run it, and see a working full-stack app.

- [ ] **Turborepo monorepo structure** -- The skeleton that everything else lives in
- [ ] **Docker Compose orchestration** -- `docker compose up` runs Postgres, Django, Next.js with hot reload
- [ ] **Django project with Django Ninja Extra** -- API layer with at least auth endpoints and health check
- [ ] **OpenAPI spec generation** -- Django Ninja generates spec, available at `/api/docs/`
- [ ] **Auto-generated TypeScript types** -- Build step that converts OpenAPI spec to TypeScript
- [ ] **Django Allauth authentication** -- Email/password signup, login, logout, password reset
- [ ] **Next.js 15 frontend with Shadcn/ui** -- App shell, auth pages, dashboard placeholder, dark mode
- [ ] **Shared packages (api-client, schemas)** -- At minimum, the API client and Zod schemas shared between apps
- [ ] **Environment variable management** -- `.env.example`, validation, Docker Compose integration
- [ ] **Code quality tooling** -- Ruff, ESLint, Prettier, TypeScript strict mode configured
- [ ] **Basic test setup** -- pytest and vitest configured with at least one example test each
- [ ] **README** -- Getting started, architecture overview, development workflow

### Add After Core Works (v1.x)

Features to add once the core template is solid and tested.

- [ ] **Expo mobile app** -- Add after web + API auth flow is proven. Mobile introduces React Native Web complexity for shared UI.
- [ ] **Shared UI package (React Native Web)** -- Add with mobile. Shared primitives between web and mobile.
- [ ] **Shared business logic package** -- Hooks, utilities, business logic shared between web and mobile.
- [ ] **Full CI/CD pipeline** -- GitHub Actions for lint, type-check, test, build. Add after test suites are meaningful.
- [ ] **Pre-commit hooks** -- Husky + lint-staged + pre-commit framework. Add after quality tooling is configured.
- [ ] **User profile and account settings** -- Profile editing pages on web and mobile.
- [ ] **Database seeding** -- Management command to create demo data.
- [ ] **Error handling patterns** -- Global error boundaries, API error format standardization.

### Future Consideration (v2+)

Features to defer until the template is stable and battle-tested across at least one real product.

- [ ] **Optional AI module (LangGraph + PGVector)** -- Complex, optional, and should be cleanly addable/removable. Build after core is solid.
- [ ] **CLI scaffolder** -- Must be built LAST. The template must be stable first.
- [ ] **Detox mobile tests** -- Mobile E2E testing is complex and flaky. Add after mobile app is stable.
- [ ] **Production deployment guides** -- Docker deployment documentation for common providers (Railway, Fly.io, AWS ECS).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase |
|---------|------------|---------------------|----------|-------|
| Docker Compose + hot reload | HIGH | MEDIUM | P1 | v1 |
| Turborepo monorepo structure | HIGH | MEDIUM | P1 | v1 |
| Django + Django Ninja Extra API | HIGH | MEDIUM | P1 | v1 |
| OpenAPI spec generation | HIGH | LOW | P1 | v1 |
| Auto-generated TS types | HIGH | MEDIUM | P1 | v1 |
| Django Allauth authentication | HIGH | MEDIUM | P1 | v1 |
| Next.js 15 + Shadcn/ui frontend | HIGH | MEDIUM | P1 | v1 |
| Shared API client + schemas | HIGH | MEDIUM | P1 | v1 |
| Code quality tooling (ruff, eslint) | MEDIUM | LOW | P1 | v1 |
| Basic test setup (pytest, vitest) | MEDIUM | LOW | P1 | v1 |
| Environment variable management | MEDIUM | LOW | P1 | v1 |
| Health check endpoint | MEDIUM | LOW | P1 | v1 |
| Expo mobile app | HIGH | HIGH | P2 | v1.x |
| Shared UI package (RNW) | HIGH | HIGH | P2 | v1.x |
| CI/CD pipeline | MEDIUM | LOW | P2 | v1.x |
| Pre-commit hooks | MEDIUM | LOW | P2 | v1.x |
| User profile / account settings | MEDIUM | MEDIUM | P2 | v1.x |
| Database seeding / fixtures | LOW | LOW | P2 | v1.x |
| Error boundaries + handling | MEDIUM | LOW | P2 | v1.x |
| Dark mode toggle | LOW | LOW | P2 | v1.x |
| AI module (LangGraph + PGVector) | MEDIUM | HIGH | P3 | v2+ |
| CLI scaffolder | HIGH | HIGH | P3 | v2+ |
| Detox mobile tests | LOW | HIGH | P3 | v2+ |
| Production deployment docs | MEDIUM | LOW | P3 | v2+ |

**Priority key:**
- P1: Must have for a usable template (core vertical slice)
- P2: Should have -- makes the template production-quality
- P3: Nice to have -- high-value but depends on stable core

---

## Competitor Feature Analysis

| Feature Area | SaaS Pegasus | ShipFast | Wasp OpenSaaS | This Template | Our Advantage |
|-------------|--------------|----------|---------------|---------------|---------------|
| **Auth** | Django Allauth, social auth, 2FA | NextAuth, magic link, social | Wasp auth (email, social, Google) | Django Allauth (email/password) | Same auth library as Pegasus; products add social auth as needed |
| **API** | Django REST Framework | Next.js API routes | Wasp operations (custom DSL) | Django Ninja Extra + OpenAPI | Stronger: auto-generated TypeScript types, Swagger UI, explicit API contracts |
| **Frontend** | Django templates + React (optional) | Next.js + Tailwind + DaisyUI | React + Tailwind | Next.js 15 + Shadcn/ui | Modern: App Router, server components, best-in-class component library |
| **Mobile** | None | None | None | Expo (React Native) | Unique: no competitor offers mobile |
| **Monorepo** | No (monolith) | No (single project) | No (Wasp structure) | Turborepo | Advantage: shared packages, consistent tooling |
| **Type Safety** | No cross-boundary types | None explicit | Wasp-generated types | OpenAPI-to-TypeScript generation | Strong: explicit type generation with single source of truth |
| **Testing** | pytest basics | None | None | pytest + vitest + detox | Strongest: full-stack test coverage |
| **DevOps** | Docker, Render deploy | Minimal | None | Docker Compose, CI/CD, pre-commit | Strongest: complete development + deployment pipeline |
| **Billing** | Stripe built-in | Stripe + LemonSqueezy | Stripe built-in | None (intentional) | Tradeoff: more flexible but requires per-product work |
| **AI** | None | None | OpenAI example | LangGraph + PGVector (optional) | Unique: production-grade AI scaffolding, not just an API call example |

### Positioning Summary

This template's competitive position is: **"The only full-stack SaaS template with web + mobile + API from one codebase, with type safety across the entire boundary, for solo entrepreneurs who want infrastructure quality without vendor lock-in."**

Weaknesses vs. competitors:
- No billing (but intentional -- each product adds its own)
- No landing pages (but intentional -- products build their own)
- Django + Next.js is less common than all-JavaScript stacks (but stronger for complex backends)

Strengths vs. all competitors:
- Only template with mobile app
- Only Django template with auto-generated TypeScript types
- Strongest DevOps story (Docker, CI/CD, pre-commit, full test suite)
- Optional AI module is production-grade, not a toy example

---

## Sources

- SaaS Pegasus feature set and documentation (training data, MEDIUM confidence -- stable product since 2020, features well-known)
- ShipFast feature set (training data, MEDIUM confidence -- well-documented product)
- Wasp OpenSaaS feature set (training data, MEDIUM confidence -- open source, publicly documented)
- create-t3-app feature set (training data, HIGH confidence -- widely used, well-documented open source)
- Makerkit and Supastarter feature sets (training data, LOW confidence -- less thoroughly covered in training data)
- General SaaS boilerplate market analysis (training data, MEDIUM confidence -- mature market with slow feature evolution)

**Note:** WebSearch and WebFetch were unavailable during this research session. All findings are based on training data through May 2025. The SaaS template market is mature and feature sets are stable year-over-year, so confidence in these findings is reasonable. However, specific version numbers and recent feature additions (2025-2026) should be verified when web access is available.

---
*Feature research for: Full-stack SaaS Foundation Template*
*Researched: 2026-02-08*
