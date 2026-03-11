# Roadmap: Foundation Template

## Milestones

- ✅ **v1.0 Foundation Template** — Phases 1–8 (shipped 2026-03-07)
- ✅ **v1.1 Billing & Payments Module** — Phases 9–12 (shipped 2026-03-11)

## Phases

<details>
<summary>✅ v1.0 Foundation Template (Phases 1–8) — SHIPPED 2026-03-07</summary>

- [x] Phase 1: Monorepo Foundation (4/4 plans) — Turborepo + pnpm workspaces, Docker Compose (Postgres 16 + PGVector + Redis), shared ESLint/TS config packages, hybrid `turbo dev` orchestration
- [x] Phase 2: API Core + Auth Backend (5/5 plans) — Django Ninja Extra API, dual auth strategy (session + JWT), Django Allauth headless, auto-generated OpenAPI 3.1 spec
- [x] Phase 3: Shared Packages + Type Generation (6/6 plans) — Auto-generated TypeScript types from OpenAPI, shared API client, Zod validation schemas, UI primitives (React Native Web)
- [x] Phase 4: Web Application (5/5 plans) — Next.js 15 App Router, complete auth flow (signup/login/logout/password reset), dashboard shell, user management
- [x] Phase 5: Mobile Application (4/4 plans) — React Native Expo managed workflow, auth screens, JWT token management, Expo Router navigation, shared package consumption
- [x] Phase 6: AI Module (5/5 plans) — Optional PGVector + LangGraph module, embedding pipeline, vector search API, tool agent scaffold
- [x] Phase 7: DevEx + CI/CD (4/4 plans) — GitHub Actions CI, pre-commit hooks (ruff + eslint), pytest/vitest/Detox test suites, production multi-stage Dockerfiles
- [x] Phase 8: CLI Scaffolder (3/3 plans) — Interactive `create-foundation-app` CLI, template generation engine, feature removal, post-generation validation, rollback

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v1.1 Billing & Payments Module (Phases 9–12) — SHIPPED 2026-03-11</summary>

- [x] Phase 9: Billing Scaffold (3/3 plans) — `PaymentAdapter` ABC, `StripeAdapter` v14, Customer/Subscription/Payment models, post_save signal, `BILLING_PLANS` settings, migration 0001 (completed 2026-03-07)
- [x] Phase 10: Webhook Infrastructure + Service Layer (3/3 plans) — Plain Django webhook view, Celery async dispatch, idempotent `ProcessedWebhookEvent`, 6 Tier-1 event handlers, `BillingService` full lifecycle, `@require_active_subscription` decorator (completed 2026-03-08)
- [x] Phase 11: API Endpoints + Billing Frontend (8/8 plans) — Ninja Extra billing controller, 8 REST endpoints, Next.js `/billing` page, plan cards, payment history, upgrade/downgrade modals, cancel flow, past-due banner (completed 2026-03-10)
- [x] Phase 12: Invoice PDF + CLI Scaffolder Integration (3/3 plans) — WeasyPrint + Jinja2 A4 PDF template, `generate_invoice_pdf` Celery task, PDF polling endpoint, `removeBillingModule()` CLI, `--without billing` flag, SCAFF-04 pytest test (completed 2026-03-11)

Full archive: `.planning/milestones/v1.1-ROADMAP.md`

</details>

## Progress

| Phase                        | Milestone | Plans Complete | Status   | Completed  |
| ---------------------------- | --------- | -------------- | -------- | ---------- |
| 1. Monorepo Foundation       | v1.0      | 4/4            | Complete | 2026-02-17 |
| 2. API Core + Auth Backend   | v1.0      | 5/5            | Complete | 2026-02-17 |
| 3. Shared Packages + Types   | v1.0      | 6/6            | Complete | 2026-02-17 |
| 4. Web Application           | v1.0      | 5/5            | Complete | 2026-02-17 |
| 5. Mobile Application        | v1.0      | 4/4            | Complete | 2026-02-17 |
| 6. AI Module                 | v1.0      | 5/5            | Complete | 2026-02-17 |
| 7. DevEx + CI/CD             | v1.0      | 4/4            | Complete | 2026-02-17 |
| 8. CLI Scaffolder            | v1.0      | 3/3            | Complete | 2026-02-17 |
| 9. Billing Scaffold          | v1.1      | 3/3            | Complete | 2026-03-07 |
| 10. Webhook Infra + Service  | v1.1      | 3/3            | Complete | 2026-03-08 |
| 11. API Endpoints + Frontend | v1.1      | 8/8            | Complete | 2026-03-10 |
| 12. Invoice PDF + CLI        | v1.1      | 3/3            | Complete | 2026-03-11 |
