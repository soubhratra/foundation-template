# GSD → OpenSpec Sync Plan

**Created:** 2026-02-18
**Purpose:** Map implementation decisions from GSD execution to OpenSpec foundation specs

## Overview

During GSD execution (Phases 1-8), **76 implementation decisions** were captured in STATE.md. These decisions reflect actual implementation choices and should be synchronized to OpenSpec foundation specs to ensure specs match reality.

## Sync Strategy

**Approach:** Systematic review with targeted spec updates
**Scope:** 7 existing specs + 1 new spec
**Source:** `.planning/STATE.md` lines 85-155

## Spec-by-Spec Sync Plan

### 1. stack.md

**Current State:** Lists approved technologies
**Needs:** Tool-specific version decisions from implementation

**Decisions to Add:**

```markdown
### Python Tooling

- **Linter/Formatter:** Ruff (replaces black + flake8 + isort)
  - Rationale: 10-100x faster, now standard for Python projects
  - Decision: Phase 07-devex-ci-cd

### Frontend Web Styling

- **CSS Framework:** Tailwind CSS 3.4
  - Rationale: Tailwind 4 preview plugin crashes Next.js PostCSS
  - Decision: Phase 04-web-application
  - Note: Not using Tailwind 4 beta

### Testing

- **Frontend Web Tests:** Vitest (not Jest)
  - Rationale: ESM-native, faster than Jest, better Next.js 15 compatibility
  - Decision: Phase 07

- **Mobile E2E:** Detox (iOS-only in template)
  - Rationale: Android can be added by users
  - Decision: Phase 07
```

**Impact:** Medium - clarifies tool choices made during implementation

---

### 2. auth.md

**Current State:** Describes dual auth strategy conceptually
**Needs:** Specific implementation patterns and workarounds

**Decisions to Add:**

```markdown
## JWT Implementation Details

### Signing Algorithm

- **Algorithm:** HS256 (symmetric)
- **Key:** Django SECRET_KEY
- **Rationale:** Avoids RSA key provisioning in template; simpler for starter
- **Decision:** Phase 02

### Session-Aware JWT Strategy

- **Pattern:** Only issue JWT tokens when `Authorization` header present in request
- **Rationale:** Prevents session-based logins from receiving JWT tokens
- **Benefit:** Allows JWT token refresh flows without creating tokens for cookie-based users
- **Decision:** Phase 02-api-core-auth-backend

### Token Revocation

- **Pattern:** Clear refresh tokens from all user sessions on password reset
- **Implementation:** Django sessions store refresh tokens; clearing sessions invalidates JWTs
- **Decision:** Phase 02-api-core-auth-backend

## Controller-Level Auth

### Dual Auth Application

- **Pattern:** Apply `SessionAuth + jwt_token_auth` at controller level
- **Benefit:** Keeps public routes unauthenticated while enabling both auth methods on protected routes
- **Example:** `/api/v1/users/me` accepts both cookies and bearer tokens
- **Decision:** Phase 02

## Known Gaps

### Missing OpenAPI Endpoints

- **Issue:** Django Allauth headless endpoints (login, logout, JWT refresh) not in OpenAPI spec
- **Workaround:** Manual `fetch()` calls in business-logic package
- **Temporary:** Until Allauth adds OpenAPI schema support
- **Decisions:** Phase 03, Phase 05
```

**Impact:** High - critical for developers implementing auth

---

### 3. api-contracts.md

**Current State:** Describes OpenAPI generation patterns
**Needs:** Workspace integration and snapshot patterns

**Decisions to Add:**

```markdown
## OpenAPI Snapshot Pattern

### Tracked Snapshot

- **Location:** `apps/api/openapi.json`
- **Pattern:** Export OpenAPI spec to tracked file, not ephemeral endpoint
- **Benefit:** Diffable in version control, enables staleness detection

### Type Generation Scope

- **Turbo Filter:** `pnpm turbo generate:api-types --filter=@repo/api`
- **Rationale:** Root workspace not part of Turbo graph; scoping prevents failures
- **Decision:** Phase 03

### Generated Artifacts Exposure

- **Pattern:** Expose `@repo/api-client/gen/v1` from tracked OpenAPI snapshot
- **Avoid:** Copying generated files into dist/
- **Benefit:** Keeps artifacts diffable, avoids redundant build steps
- **Decision:** Phase 03-shared-packages-type-generation

## API Routing

### Documentation Endpoints

- **Docs URL:** `/api/docs`
- **API Base:** `/api/v1/`
- **Rationale:** Stable v1 routing without changing endpoint prefix
- **Auth:** Authenticated in dev, staff-only in production
- **Decision:** Phase 02
```

**Impact:** Medium - helps developers understand type generation

---

### 4. architecture.md

**Current State:** Monorepo structure and boundaries
**Needs:** Workspace configuration patterns

**Decisions to Add:**

```markdown
## Workspace Configuration Patterns

### Config Packages in Root

- **Pattern:** Link `@repo/config-*` packages in root `devDependencies`
- **Rationale:** Allows Node/tsc module resolution for config verification
- **Packages:** `@repo/config-eslint`, `@repo/config-ts`
- **Decision:** Phase 01

### Root ESLint Config

- **Location:** `eslint.config.js` at repo root
- **Rationale:** lint-staged runs from root, needs config for package discovery
- **Decision:** Phase 08-cli-scaffolder

## Expo Type Environment Alignment

### React Type Definitions

- **Pattern:** Match `@types/react` versions between Expo and web packages
- **Issue:** TS ReactNode mismatch blocks metro type-check
- **Solution:** Align to React 19 definitions
- **Decision:** Phase 03

### Metro Workspace Aliases

- **Pattern:** Add Metro alias for `@repo/api-client`
- **Rationale:** Expo bundler needs explicit workspace alias to resolve shared packages
- **Decision:** Phase 05-mobile-application

## Centralization Patterns

### API Base URL Helper

- **Location:** `apps/web/app/base-url.ts`
- **Rationale:** Layouts and routes reuse without duplicating logic
- **Decision:** Phase 04-web-application

### CSRF-Aware API Helper

- **Location:** `apps/web/lib/postJson` (or similar)
- **Rationale:** Every auth mutation shares Django headless request wiring
- **Decision:** Phase 04-web-application
```

**Impact:** High - guides monorepo setup for new developers

---

### 5. ai-stack.md

**Current State:** High-level AI module description
**Needs:** Specific implementation patterns and security decisions

**Decisions to Add:**

```markdown
## Vector Index Implementation

### HNSW Index Placement

- **Pattern:** Declare index in concrete model, not abstract mixin
- **Rationale:** Django migration system requires explicit index declarations
- **Decision:** Phase 06-ai-module

### PGVector Extension Creation

- **Pattern:** `CREATE EXTENSION IF NOT EXISTS pgvector`
- **Rationale:** Avoids permission errors in production where extension may be pre-installed
- **Decision:** Phase 06-ai-module

## Celery Configuration

### Result Backend

- **Setting:** `CELERY_RESULT_BACKEND = 'django-db'`
- **Rationale:** Stores results in PostgreSQL, keeps all data centralized
- **Alternative:** Could use Redis, but adds dependency
- **Decision:** Phase 06-ai-module

## Embedding Pipeline

### Chunking Strategy

- **Chunk Size:** 512 tokens
- **Overlap:** 200 tokens
- **Tokenizer:** tiktoken `cl100k_base`
- **Rationale:** Balances granularity with semantic context for better search
- **Decision:** Phase 06-ai-module

### Idempotent Task Design

- **Pattern:** Delete existing chunks before processing document
- **Benefit:** Safe task retries and re-embedding after model upgrades
- **Decision:** Phase 06-ai-module

## LangGraph Agent Patterns

### Intent Detection

- **Pattern:** Keyword matching (not LLM-based)
- **Rationale:** Avoids API dependency in scaffold, faster
- **Decision:** Phase 06-ai-module

### Tool Security

- **Calculator:** AST parsing (prevents arbitrary code execution)
- **Authentication:** Requires `OPENAI_API_KEY` at runtime
- **Error Handling:** Degraded responses instead of crashes
- **Decisions:** Phase 06-ai-module

## API Endpoints

### Authentication

- **Requirement:** All AI endpoints require `IsAuthenticated` permission
- **Controller:** Auto-discovered by Django Ninja Extra (no manual registration)
- **Decision:** Phase 06-04
```

**Impact:** High - critical for developers extending AI features

---

### 6. deployment.md

**Current State:** Docker and CI/CD overview
**Needs:** Specific build patterns and Next.js deployment

**Decisions to Add:**

```markdown
## Docker Build Patterns

### Multi-Stage Builds

- **Pattern:** Use multi-stage Dockerfiles for both API and web
- **Benefit:** Minimizes final image size
- **Files:** `apps/api/Dockerfile.prod`, `apps/web/Dockerfile.prod`
- **Decision:** Phase 07

### Next.js Standalone Mode

- **Setting:** `output: 'standalone'` in `next.config.js`
- **Benefit:** Minimal Docker deployment, smaller images
- **Requirement:** Suspense boundary for `useSearchParams()` in root layout
- **Decision:** Phase 07

## CI/CD Optimization

### Parallel Job Execution

- **Pattern:** Separate jobs for `api`, `web`, `mobile`
- **Benefit:** Max CI speed, failures isolated by platform
- **Decision:** Phase 07-03

### Triple-Layer Caching

- **Layers:** pip (uv compatible), pnpm, turbo
- **Impact:** Reduces CI from 10+ min to 2-3 min
- **Decision:** Phase 07-03

### Type Staleness Gate

- **Pattern:** Separate type-check workflow with hash-based detection
- **Hash:** SHA-256 of `openapi.json`
- **Benefit:** Clear failure messaging when types drift from spec
- **Decision:** Phase 07-03
```

**Impact:** Medium - helps developers optimize deployments

---

### 7. conventions.md

**Current State:** Code style and file organization
**Needs:** Pre-commit and testing patterns

**Decisions to Add:**

```markdown
## Pre-Commit Hooks

### Strategy

- **Auto-fix:** Format and lint issues automatically
- **Block:** Violations prevent commit
- **Scope:** Only staged files (speed: <5s typical)
- **CI Complement:** CI runs full checks on all files
- **Rationale:** Balances speed and control
- **Decision:** Phase 07-devex-ci-cd

## Testing Conventions

### Django Ninja Extra Controllers

- **Pattern:** Use Django test client (not direct controller calls)
- **Rationale:** Avoids registry conflicts
- **Decision:** Phase 07

### Migration Order

- **Pattern:** Create PGVector extension before vector field tables
- **Rationale:** Fields depend on extension types
- **Decision:** Phase 07

### Mobile E2E

- **Scope:** iOS-only in template
- **Rationale:** Android can be added by users, keeps template simple
- **Decision:** Phase 07
```

**Impact:** Medium - standardizes development workflows

---

### 8. cli-scaffolder.md (NEW)

**Current State:** Does not exist
**Needs:** Full spec for CLI scaffolder patterns

**Content to Create:**

```markdown
# CLI Scaffolder

## Overview

Interactive CLI for generating new projects from the Foundation Template. Implements project name transformation, feature selection, secret generation, and post-generation validation.

## User Experience

### Prompting Strategy

- **Pattern:** Hybrid flow - name first, then features, then output dir
- **Validation:** Re-prompt on errors (don't exit CLI)
- **Defaults:** All platforms checked by default
- **Rationale:** Most users want full stack
- **Decision:** Phase 08-cli-scaffolder, Phase 08-CONTEXT.md

### Feature Selection

- **Toggles:** web, mobile, landing, ai
- **Default:** All included
- **Removal:** Complete (directories + dependencies + config)

## Implementation Patterns

### File Exclusion

- **Package:** `ignore` (gitignore-style patterns)
- **Decision:** Phase 08-02

### Placeholder Transformation

- **Files:** All text files (tsconfig.json, Dockerfiles, _.json, _.py, \*.ts)
- **Dot-dirs:** Include `.github/` using `dot:true`
- **Decision:** Phase 08-02

### Secret Generation

- **Django SECRET_KEY:** 50 chars using `crypto.randomBytes`
- **Follows:** Django documentation standards
- **Decision:** Phase 08-02

## Feature Removal

### Complete Cleanup

- **Pattern:** Delete directories, remove dependencies, update workspace files
- **Example (AI):** Delete `apps/api/apps/ai/`, remove 8 Python deps, update pyproject.toml
- **Decision:** Phase 08-03

## Validation

### Post-Generation

- **Commands:** pnpm install, uv sync, turbo lint, ruff check, turbo type-check, mypy
- **Timeout:** 10 minutes per install step
- **Optional:** `--skip-validation` flag for faster generation
- **Decision:** Phase 08-03

### Error Handling

- **Pattern:** Automatic rollback (delete entire output directory)
- **Rationale:** Better UX than leaving broken projects
- **Decision:** Phase 08-03, Phase 08-CONTEXT.md

## ESLint Configuration

### Root Config

- **Location:** `eslint.config.js` at monorepo root
- **Rationale:** lint-staged runs from root, needs config for package discovery
- **Decision:** Phase 08-cli-scaffolder
```

**Impact:** High - critical for CLI scaffolder usage

---

## Execution Plan

### Phase 1: Review (Manual)

- [ ] Read each spec alongside mapped decisions
- [ ] Identify conflicts or outdated info
- [ ] Note any additional context needed

### Phase 2: Update Specs

- [ ] Update 7 existing specs with decision sections
- [ ] Create new `cli-scaffolder.md` spec
- [ ] Maintain spec structure and formatting

### Phase 3: Verify

- [ ] Check all 76 decisions are reflected
- [ ] Ensure no duplication between specs
- [ ] Verify links and cross-references

### Phase 4: Commit

- [ ] Commit spec updates with clear message
- [ ] Reference this SYNC_PLAN.md in commit
- [ ] Push to remote

## Notes

**Why Now:** All 8 phases complete, decisions finalized, no more drift expected
**Impact:** Makes OpenSpec specs the source of truth for actual implementation
**Audience:** Developers using the template, AI agents reading specs
**Maintenance:** Future changes should update both STATE.md (during execution) and specs (after phase completion)
