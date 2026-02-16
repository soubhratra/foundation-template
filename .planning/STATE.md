# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-08)

**Core value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.
**Current focus:** Phase 2 - API Core + Auth Backend

## Current Position

**Current Phase:** 02
**Current Phase Name:** API Core + Auth Backend
**Current Plan:** 4
**Total Plans in Phase:** 4
**Status:** Phase complete — ready for verification
**Last Activity:** 2026-02-16
**Last Activity Description:** Completed 02-01-PLAN.md

**Progress:** [█████████░] 90%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01 P01 | 6 min | 3 tasks | 18 files |
| Phase 01 P03 | 5 min | 2 tasks | 16 files |
| Phase 01 P02 | 6 min | 2 tasks | 27 files |
| Phase 01 P04 | 1h 22m | 2 tasks | 11 files |
| Phase 02 P01 | 1 min | 3 tasks | 5 files |
| Phase 02 P02 | 0 min | 2 tasks | 7 files |
| Phase 02 P03 | 26 min | 3 tasks | 11 files |
| Phase 02 P04 | 1 min | 2 tasks | 4 files |
| Phase 02-api-core-auth-backend P05 | 6min | 3 tasks | 4 files |
| Phase 03-shared-packages-type-generation P03 | 7 min | 2 tasks | 7 files |
| Phase 03 P04 | 14 min | 2 tasks | 13 files |
| Phase 03 P01 | 15 min | 2 tasks | 7 files |
| Phase 03-shared-packages-type-generation P03-02 | 7 min | 2 tasks | 9 files |
| Phase 03-shared-packages-type-generation P05 | 1h 2m | 3 tasks | 10 files |
| Phase 04-web-application P01 | 23 min | 3 tasks | 37 files |
| Phase 04-web-application P02 | 9 min | 3 tasks | 12 files |
| Phase 04-web-application P04-03 | 12 min | 3 tasks | 16 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 8-phase structure derived from 71 requirements across 9 categories
- [Roadmap]: Custom user model (API-02) placed in Phase 1 dependency chain (before first migration)
- [Roadmap]: AUTH requirements split: backend config (AUTH-08, AUTH-09) in Phase 2, web auth flows (AUTH-01 through AUTH-06) in Phase 4, mobile JWT (AUTH-07) in Phase 5
- [Roadmap]: AI-07 (CLI exclusion of AI module) placed in Phase 8 (CLI Scaffolder) not Phase 6 (AI Module)
- [Phase 01]: Linked @repo/config-* packages in root devDependencies to allow Node/tsc module resolution for config verification
- [Phase 01]: Aligned Expo SDK dependencies to expo-doctor expected versions (react 18.3.1, safe-area-context 4.12.0) to ensure validation passes.
- [Phase 02]: Expose API docs at /api/docs while keeping /api/v1/ base path — Allows stable v1 routing without changing endpoint prefix
- [Phase 02]: Require authentication for docs in dev and staff-only in production — Prevents public exposure of API docs
- [Phase 02]: Use HS256 for headless JWTs backed by SECRET_KEY to avoid RSA key provisioning in the template.
- [Phase 02]: Expose headless browser/app endpoints under /api/v1/auth/ with explicit session logout overrides returning 204.
- [Phase 02]: Apply dual auth at the controller level using SessionAuth + jwt_token_auth — Keeps public routes unauthenticated while enabling cookies and bearer tokens on /users/me.
- [Phase 02-api-core-auth-backend]: Session-aware JWT strategy: Only issue JWT tokens when request has Authorization header — Prevents session-based logins from receiving JWT tokens while still allowing JWT token refresh flows
- [Phase 02-api-core-auth-backend]: Token revocation: Clear refresh tokens from all user sessions on password reset — Since refresh tokens are stored in Django sessions, clearing them invalidates JWT authentication
- [Phase 03-shared-packages-type-generation]: Deferred pnpm-lock.yaml update until packages/ui staged work is ready
- [Phase 03]: Align Expo type environment with React 19 definitions — TS ReactNode mismatch blocked metro type-check; matching @types/react versions keeps shared primitives compiling
- [Phase 03]: Scope turbo generate:api-types to @repo/api — Root workspace is not part of the Turbo graph, so filtering to the backend package keeps the generator focused and prevents failures.
- [Phase 03-shared-packages-type-generation]: Expose @repo/api-client/gen/v1 from the tracked OpenAPI snapshot instead of copying it into dist — Keeps generated artifacts diffable and avoids redundant build steps while remaining within the workspace package
- [Phase 03-shared-packages-type-generation]: Manual fetch for Allauth auth endpoints — OpenAPI snapshot lacks login/logout routes, so hooks call fetch until spec adds them
- [Phase 04-web-application]: Use Tailwind CSS 3.4 toolchain — Tailwind 4 preview plugin crashes Next.js PostCSS, so reverting to v3 keeps builds and lint/type-check commands green.
- [Phase 04-web-application]: Centralize API base URL helper — Moved buildApiBaseUrl into app/base-url.ts so layouts and future routes can reuse it without duplicating logic.
- [Phase 04-web-application]: Centralized a CSRF-aware postJson helper so every auth mutation shares the same Django headless request wiring.
- [Phase 04-web-application]: Extended @repo/validation with emailVerificationSchema so verify-email flows follow the shared schema package.
- [Phase 04-web-application]: Proxy guard enforces redirects centrally — Keeps layouts/pages session-agnostic and ensures consistent redirect behavior.
- [Phase 04-web-application]: sessionExpired query flag powers toast messaging — Shared search param keeps login/signup UX consistent while preserving safe redirect targets.

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 2]: Django Allauth headless mode + dual auth strategy needs deeper research during planning (sparse documentation, complex cross-platform auth)
- [Phase 6]: LangGraph API may have evolved since training data cutoff (May 2025); verify current API during planning

## Session Continuity

**Last Session:** 2026-02-16T12:52:06.136Z
**Stopped At:** Completed 04-web-application-04-03-PLAN.md
**Resume File:** None
