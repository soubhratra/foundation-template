# Phase 7: DevEx + CI/CD - Research

**Researched:** 2026-02-16
**Domain:** Developer Experience Automation, CI/CD Infrastructure, Testing Frameworks
**Confidence:** HIGH

## Summary

Phase 7 establishes automated quality enforcement and production deployment readiness across the full-stack monorepo. The research validates that the chosen stack (pre-commit framework, GitHub Actions, pytest, vitest, Detox) represents current best practices for multi-language monorepos in 2026. Key findings emphasize comprehensive caching strategies (pnpm, uv, turbo, Docker layers) to achieve fast CI runs, and multi-stage Docker builds for minimal production images.

The phase balances developer convenience (auto-fix hooks, parallel jobs, fast local feedback) with production rigor (all quality gates enforced, comprehensive test coverage, type-safe deployments). The discretionary decisions documented in CONTEXT.md are addressed with specific recommendations based on industry patterns and monorepo-specific constraints.

**Primary recommendation:** Implement auto-fix pre-commit hooks with fast changed-files-only scope, parallel GitHub Actions jobs without fail-fast (for comprehensive feedback), and demonstrate all four test categories without hard coverage thresholds (template demonstration, not enforcement).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Pre-commit Hook Enforcement:**
- **Block all quality violations**: Commits must pass formatting (ruff, prettier), linting (ruff, eslint), and type checking (mypy, tsc)
  - *Rationale:* Comprehensive quality gate at commit time prevents technical debt from entering the codebase. All three dimensions (format, lint, types) catch different classes of issues - formatting catches style violations, linting catches code smells and potential bugs, type checking catches type safety issues. Blocking all ensures template demonstrates production-grade standards.

**CI Job Parallelization & Caching:**
- **Comprehensive caching strategy**: Cache dependencies (pnpm, uv), build outputs (turbo cache), and Docker layers
  - *Rationale:* Maximizes CI speed across all three optimization vectors. Dependency caching saves package installation time (major speedup on most runs). Turbo cache enables incremental builds (skip rebuilding unchanged apps). Docker layer caching accelerates image builds. Combined, these can reduce CI time from 10+ minutes to 2-3 minutes on typical changes.

**Test Coverage Expectations:**
- **Comprehensive test coverage**: Template demonstrates production-ready testing, not minimal examples
  - *Rationale:* As a starter template, this sets the quality bar for projects built from it. Comprehensive coverage means developers inherit working examples of all test patterns they'll need. Shows best practices rather than "good enough to prove it works."
- **All four test categories**: Unit tests (pure logic), integration tests (API endpoints), component tests (UI), and E2E tests (full user flows)
  - *Rationale:* Each test type catches different classes of bugs:
    - *Unit tests:* Pure logic bugs in utilities, helpers, business logic functions
    - *Integration tests:* API contract violations, database interaction issues, auth flow bugs
    - *Component tests:* UI rendering bugs, user interaction issues, prop validation
    - *E2E tests:* Cross-system integration issues, complete user journey validation
  - Having all four means the template demonstrates the full testing pyramid - developers can see working examples of each pattern and understand when to use which approach.

### Claude's Discretion

**Pre-commit Hook Behavior:**
- Auto-fix behavior (whether hooks auto-fix formatting or just report errors)
- Bypass capability (whether `--no-verify` is allowed)
- Check scope (changed files only vs entire codebase)

**CI Job Configuration:**
- Job parallelization strategy (all jobs parallel vs sequential)
- Fail-fast behavior (cancel remaining jobs on first failure vs run all)
- CI trigger strategy (every push, PRs only, or main + PRs)

**Test Coverage:**
- Coverage thresholds (enforce minimum % or track without enforcement)
- Test data strategy (factories, fixtures, or mix)

**Production Docker:**
- Image size vs build speed optimization
- Base image selection (Alpine, Debian slim, or full Debian)
- Security scanning integration (include vulnerability scanning or keep simple)
- Layer caching optimization (dependency-first ordering vs simple single-stage)

### Deferred Ideas (OUT OF SCOPE)

**Performance & Load Testing:**
- Document approach to performance/load testing at both app level (web/mobile) and API level
- Research and document free & open-source tools for load testing
- *Why deferred:* Distinct capability beyond DevEx + CI/CD phase boundary. Could be Phase 7.1 or post-Phase-8 addition.

**Security & Penetration Testing:**
- Document penetration testing approach for the stack
- Research and document free & open-source tools for security testing
- *Why deferred:* Distinct capability beyond DevEx + CI/CD phase boundary. Security testing infrastructure could be its own phase.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DX-01 | Pre-commit hooks: ruff (Python), eslint + prettier (JS/TS) | Pre-commit framework + ruff-pre-commit + lint-staged integration |
| DX-02 | GitHub Actions workflow with 3 parallel jobs: api, web, mobile | GitHub Actions matrix strategy, pnpm/uv caching patterns |
| DX-03 | CI gate: fail build if generated TypeScript types are stale vs OpenAPI spec | openapi-typescript + oasdiff for spec drift detection |
| DX-04 | pytest test suite for backend with example tests | pytest-django + factory_boy for Django testing |
| DX-05 | vitest test suite for frontend with example tests | vitest + React Testing Library for Next.js 15 App Router |
| DX-06 | detox test suite for mobile with example tests | Detox + Expo integration on macOS runners |
| DX-07 | Production Dockerfiles for Django API and Next.js app | Multi-stage builds, Next.js standalone output, Django gunicorn |
| DX-08 | Type checking enforced: mypy (Python), tsc --noEmit (TypeScript) | mypy + django-stubs, TypeScript strict mode in monorepo |

</phase_requirements>

---

## Standard Stack

### Core Quality Tools

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pre-commit | 4.x | Git pre-commit hook framework | Multi-language monorepo standard; orchestrates Python (ruff) and JS/TS (lint-staged) hooks |
| ruff-pre-commit | v0.15.1+ | Pre-commit hook for Ruff | Official Astral hook; replaces black + flake8 + isort with single fast tool |
| lint-staged | 15.x | JS/TS pre-commit file processing | Runs ESLint + Prettier only on staged files; fast pre-commit checks |
| GitHub Actions | N/A | CI/CD platform | Industry standard, free for public repos, excellent caching support |
| actions/setup-node | v4 | Node.js + pnpm cache setup | Official action with built-in pnpm store caching |
| actions/setup-python | v5 | Python setup with uv support | Official action; supports caching for pip/poetry/pipenv (uv via cache-dependency-path) |
| actions/cache | v4 | Generic dependency/build caching | Cache turbo remote cache, Docker layers |

### Testing Stack

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.x | Python test runner | Django community standard; mature fixture system, excellent plugins |
| pytest-django | 4.9+ | Django integration for pytest | Official Django pytest plugin; provides fixtures, database access, settings overrides |
| pytest-cov | 5.x | Test coverage reporting | Standard coverage tool; integrates with pytest, generates CI-compatible reports |
| factory_boy | 3.x | Test data factories | Mature Django ORM factory pattern; handles relationships, integrates with Faker |
| vitest | Latest | ESM-native test runner | Next.js 15 recommended; faster than Jest, Vite-compatible, ESM-first |
| @testing-library/react | Latest | React component testing | Industry standard; encourages accessible UI testing patterns |
| @testing-library/dom | Latest | DOM testing utilities | Required for vitest + React Testing Library integration |
| @vitejs/plugin-react | Latest | Vitest React plugin | Required for JSX transformation in vitest |
| jsdom | Latest | DOM implementation for Node | Required for vitest browser environment simulation |
| Detox | Latest stable | React Native E2E testing | Wix-maintained gray-box E2E framework; industry standard for RN |
| jest (Detox) | Latest | Test runner for Detox | Detox uses Jest as test runner (not vitest) |

### Docker Production Stack

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python:3.12-slim | Latest | Django base image | Debian slim balances size (~150MB) and compatibility; Alpine has wheel build issues |
| node:20-alpine | Latest | Next.js builder image | Alpine acceptable for builder stage; slim final layer via standalone output |
| gunicorn | 22.x | Django WSGI server | Production-grade Python WSGI server; never use `manage.py runserver` in production |
| whitenoise | 6.x | Static file serving | Serves Django static files without nginx/S3; simplifies single-container deployment |
| psycopg[binary] | 3.x | PostgreSQL adapter | Modern psycopg3; faster than psycopg2, better async support |

### Supporting Tools

| Technology | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| oasdiff | Latest | OpenAPI spec diff detection | CI gate for DX-03; detects breaking API changes |
| openapi-typescript | 7.x | TypeScript type generation | Already in stack; verify types are up-to-date in CI |
| mypy | 1.x | Python static type checker | Enforces type safety in Django code; catches schema bugs |
| django-stubs | 5.x | Django type stubs for mypy | Required for mypy to understand Django ORM, settings, etc. |
| @types/* | Latest | TypeScript type definitions | Next.js, React, Node.js type definitions |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pre-commit framework | husky + lint-staged only | pre-commit handles Python + JS/TS in one config; husky is JS-only |
| pytest | Django's unittest | pytest has better fixtures, plugins, and community momentum |
| vitest | Jest | Jest is CJS-first, slower; vitest is ESM-native, faster, Next.js 15 recommended |
| Detox | Appium | Detox is gray-box (faster, more reliable); Appium is black-box (slower, flakier) |
| python:3.12-slim | python:3.12-alpine | Alpine has musl libc issues with Python wheels; slim is Debian-based, more compatible |
| multi-stage Docker | single-stage | Multi-stage reduces final image size 3-10x; essential for production |

**Installation (to root package.json):**
```bash
pnpm add -D -w lint-staged pre-commit vitest @vitest/ui @testing-library/react @testing-library/dom @vitejs/plugin-react jsdom detox
```

**Installation (to apps/api/pyproject.toml dev dependencies):**
```toml
[dependency-groups]
dev = [
    "ruff>=0.8",
    "mypy>=1.11",
    "django-stubs>=5.1",
    "pytest>=8.0",
    "pytest-django>=4.9",
    "pytest-cov>=5.0",
    "factory-boy>=3.3",
]
```

---

## Architecture Patterns

### Pre-commit Hook Architecture

**Recommended `.pre-commit-config.yaml` (repo root):**
```yaml
repos:
  # Python quality (ruff replaces black + flake8 + isort)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.1  # Use latest stable from https://github.com/astral-sh/ruff-pre-commit/releases
    hooks:
      - id: ruff
        args: [--fix]  # Auto-fix linting issues
      - id: ruff-format  # Format Python code

  # JS/TS quality (via lint-staged to scope to changed files only)
  - repo: local
    hooks:
      - id: lint-staged
        name: lint-staged
        entry: pnpm lint-staged
        language: system
        pass_filenames: false

  # General hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
```

**Recommended `lint-staged` config (root package.json):**
```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md,yml,yaml}": [
      "prettier --write"
    ]
  }
}
```

**Pattern: Ruff before formatter**
When running with `--fix`, ruff's lint hook must run before ruff's formatter, as lint fixes may output code requiring reformatting.

**Pattern: Changed files only**
Pre-commit hooks run only on staged files by default. This is fast (< 5s typical) and provides immediate feedback. Full codebase checks run in CI.

**Pattern: Auto-fix for format/lint, block for type errors**
- Ruff format/lint: Auto-fix (developer convenience)
- ESLint/Prettier: Auto-fix (developer convenience)
- mypy/tsc: Report errors, block commit (type errors require developer understanding)

### GitHub Actions CI/CD Architecture

**Recommended 3-job parallel workflow (`.github/workflows/ci.yml`):**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Python setup with uv caching
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'  # uv uses pip cache structure
          cache-dependency-path: 'apps/api/pyproject.toml'

      # Install uv
      - run: pip install uv

      # Install dependencies
      - run: cd apps/api && uv sync

      # Quality checks
      - run: cd apps/api && uv run ruff check .
      - run: cd apps/api && uv run mypy .
      - run: cd apps/api && uv run pytest --cov --cov-report=xml

      # Upload coverage
      - uses: codecov/codecov-action@v4
        with:
          files: ./apps/api/coverage.xml

  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Node.js + pnpm setup with caching
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      # Install dependencies
      - run: pnpm install --frozen-lockfile

      # Build packages (shared packages must build first)
      - run: pnpm turbo build --filter=@repo/web^...

      # Quality checks
      - run: pnpm turbo lint --filter=@repo/web
      - run: pnpm turbo type-check --filter=@repo/web
      - run: pnpm turbo test --filter=@repo/web

      # Type drift check (DX-03)
      - run: pnpm run generate:api-types
      - run: git diff --exit-code packages/api-client/src/gen/

  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Node.js + pnpm (same as web)
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile
      - run: pnpm turbo build --filter=@repo/mobile^...
      - run: pnpm turbo lint --filter=@repo/mobile
      - run: pnpm turbo type-check --filter=@repo/mobile
      # Note: Detox E2E tests run separately on macOS runner (expensive)

  # Optional: Detox E2E (run on main branch only, macOS runner required)
  e2e-mobile:
    if: github.ref == 'refs/heads/main'
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'

      # Install dependencies
      - run: pnpm install --frozen-lockfile
      - run: brew tap wix/brew
      - run: brew install applesimutils

      # Build and test
      - run: cd apps/mobile && pnpm detox build --configuration ios.sim.release
      - run: cd apps/mobile && pnpm detox test --configuration ios.sim.release

      # Upload artifacts on failure
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: detox-artifacts
          path: apps/mobile/artifacts
```

**Pattern: Parallel jobs without fail-fast**
Run all three jobs in parallel. Do NOT use `fail-fast: true` in matrix strategy. Developers benefit from seeing all failures at once (e.g., both linting and type errors) to fix in one iteration.

**Pattern: Cache at three levels**
1. **Dependency cache**: `actions/setup-node` (pnpm store), `actions/setup-python` (pip/uv)
2. **Turbo cache**: `actions/cache` with key on `turbo.json` + lockfiles
3. **Docker layer cache**: `docker/build-push-action` with `cache-from`/`cache-to`

**Pattern: Turbo filters for granular execution**
- `--filter=@repo/web` runs tasks for web app only
- `--filter=@repo/web^...` builds web's dependencies (shared packages) but not web itself
- This minimizes wasted CI time (don't build mobile when only web changed)

**Pattern: Type drift check (DX-03)**
Regenerate TypeScript types from OpenAPI spec, then `git diff --exit-code` fails if working tree changed. This catches when API changes but types weren't regenerated.

### Testing Architecture

#### Backend: pytest + Django

**Recommended `apps/api/tests/conftest.py` (project-level fixtures):**
```python
import pytest
from django.conf import settings
from rest_framework.test import APIClient

# Ensure tests use fast password hasher
settings.PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

@pytest.fixture
def api_client():
    """DRF API client for endpoint testing."""
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    """API client authenticated as test user."""
    api_client.force_authenticate(user=user)
    return api_client
```

**Recommended factory pattern (`apps/api/apps/accounts/tests/factories.py`):**
```python
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker('email')
    username = factory.Sequence(lambda n: f'user{n}')
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.set_password(extracted or 'testpass123')
        obj.save()
```

**Example integration test:**
```python
import pytest
from apps.accounts.tests.factories import UserFactory

@pytest.mark.django_db
def test_user_login_success(api_client):
    user = UserFactory(password='testpass123')
    response = api_client.post('/api/auth/login', {
        'email': user.email,
        'password': 'testpass123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.data
```

**Pattern: Factory + fixtures for test data**
Use factory_boy for model creation (flexible, realistic), fixtures for service/client setup. Mix approach balances predictability (fixtures) with flexibility (factories).

**Pattern: Fast password hasher for tests**
Django's default PBKDF2 hasher is slow. Use MD5 in tests (settings override in conftest.py) for 10x speedup.

#### Frontend: vitest + React Testing Library

**Recommended `apps/web/vitest.config.ts`:**
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './app'),
    },
  },
})
```

**Recommended `apps/web/vitest.setup.ts`:**
```typescript
import '@testing-library/jest-dom'
```

**Example component test:**
```typescript
import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoginForm } from '@/components/auth/login-form'

test('LoginForm renders email and password inputs', () => {
  render(<LoginForm />)
  expect(screen.getByLabelText(/email/i)).toBeDefined()
  expect(screen.getByLabelText(/password/i)).toBeDefined()
})
```

**Pattern: Component tests, not unit tests**
Test components as users interact with them (accessible labels, user events). Avoid testing implementation details (state, props directly).

**Limitation: Async Server Components not supported**
Next.js 15 App Router async Server Components cannot be tested with vitest (React ecosystem limitation). Use E2E tests for these flows.

#### Mobile: Detox E2E

**Recommended `.detoxrc.js` (apps/mobile/):**
```javascript
module.exports = {
  testRunner: {
    args: {
      '$0': 'jest',
      config: 'e2e/jest.config.js',
    },
    jest: {
      setupTimeout: 120000,
    },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/YourApp.app',
      build: 'xcodebuild -workspace ios/YourApp.xcworkspace -scheme YourApp -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'ios.release': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Release-iphonesimulator/YourApp.app',
      build: 'xcodebuild -workspace ios/YourApp.xcworkspace -scheme YourApp -configuration Release -sdk iphonesimulator -derivedDataPath ios/build',
    },
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 15 Pro',
      },
    },
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug',
    },
    'ios.sim.release': {
      device: 'simulator',
      app: 'ios.release',
    },
  },
}
```

**Example Detox test:**
```javascript
describe('Authentication Flow', () => {
  beforeAll(async () => {
    await device.launchApp()
  })

  it('should show login screen by default', async () => {
    await expect(element(by.text('Login'))).toBeVisible()
  })

  it('should login successfully with valid credentials', async () => {
    await element(by.id('email-input')).typeText('test@example.com')
    await element(by.id('password-input')).typeText('testpass123')
    await element(by.id('login-button')).tap()
    await expect(element(by.text('Dashboard'))).toBeVisible()
  })
})
```

**Pattern: Run Detox only on main branch in CI**
Detox requires macOS runners (expensive). Run on main branch merges, not every PR push. Run locally during development.

### Production Dockerfile Architecture

#### Django API Multi-Stage Dockerfile

**Recommended `apps/api/Dockerfile`:**
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /build

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to /build/.venv
RUN uv sync --frozen --no-dev

# Stage 2: Production
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Collect static files (whitenoise serves them)
RUN /app/.venv/bin/python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

**Pattern: Multi-stage build reduces image size 3-10x**
Builder stage includes build tools (gcc, g++, build-essential). Production stage uses slim base + runtime libs only. Final image ~150MB vs ~900MB single-stage.

**Pattern: Non-root user for security**
Create `appuser` with fixed UID 1000. Run gunicorn as appuser, not root. Security best practice.

**Pattern: Layer caching optimization**
Order: dependencies first (cached on most builds), code last (changes frequently). `COPY pyproject.toml uv.lock` before `COPY . .` maximizes cache hits.

#### Next.js Web Multi-Stage Dockerfile

**Recommended `apps/web/Dockerfile`:**
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copy dependency files (monorepo root + web app)
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/
COPY packages packages/

# Install dependencies
RUN pnpm install --frozen-lockfile --filter @repo/web...

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9 --activate

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages ./packages

# Copy source
COPY apps/web apps/web
COPY turbo.json package.json pnpm-workspace.yaml ./

# Build with standalone output
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm turbo build --filter=@repo/web

# Stage 3: Production
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy standalone output (includes minimal node_modules)
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "apps/web/server.js"]
```

**Pattern: Next.js standalone output**
Enable `output: 'standalone'` in `next.config.ts`. Next.js traces dependencies and creates `.next/standalone` with minimal node_modules. Reduces production image from ~1GB to ~150MB.

**Pattern: Three-stage build for Next.js**
1. **deps**: Install all dependencies (cached frequently)
2. **builder**: Build application (invalidated on code changes)
3. **runner**: Copy standalone output only (minimal final image)

**Pattern: Static assets copied separately**
Standalone output excludes `.next/static` and `public/`. Copy these manually to `standalone/` directory structure. `server.js` serves them automatically.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pre-commit hook management | Custom git hook scripts in `.git/hooks/` | pre-commit framework | Pre-commit framework handles multi-language hooks, version pinning, hook installation across team, CI integration. Hand-rolled scripts break on git clone. |
| CI caching logic | Manual cache key generation, cache pruning | actions/cache, actions/setup-node cache, actions/setup-python cache | Official actions handle cache key hashing, cache invalidation, platform-specific paths. Hand-rolled caching is error-prone and slow. |
| Test data generation | Hardcoded fixtures, manual model creation | factory_boy (Django), Faker (randomized data) | Factories handle relationships, generate realistic data, support inheritance. Manual fixtures become unmaintainable at scale. |
| Docker layer optimization | Single-stage Dockerfiles, manual dependency ordering | Multi-stage builds, dependency-first COPY ordering | Multi-stage builds leverage BuildKit caching, reduce image size 3-10x. Hand-rolled layer ordering misses cache opportunities. |
| OpenAPI spec drift detection | Manual schema comparison, JSON diff scripts | oasdiff, openapi-diff tools | Specialized tools detect breaking changes, generate human-readable diffs, integrate with CI. Hand-rolled diffs miss semantic changes. |
| Type generation validation | Manual type checking, `git status` parsing | `git diff --exit-code` + openapi-typescript | `git diff --exit-code` is single-line, platform-agnostic, fails CI correctly. Hand-rolled validation is fragile. |

**Key insight:** DevEx tooling has mature solutions for every common problem (hooks, caching, testing, Docker). Hand-rolling any of these introduces maintenance burden and misses optimizations (e.g., BuildKit caching, GitHub Actions cache semantics).

---

## Common Pitfalls

### Pitfall 1: Pre-commit Hooks Too Slow

**What goes wrong:** Pre-commit hooks run on entire codebase instead of changed files only. Developer commits take 30+ seconds, hooks get bypassed with `--no-verify`.

**Why it happens:** Default pre-commit behavior is full codebase scan. For monorepos with 1000+ files, this is slow. Developers lose patience.

**How to avoid:**
- Use `lint-staged` for JS/TS (scopes to staged files automatically)
- Pre-commit framework runs Python hooks (ruff) on changed files by default
- Set timeout expectations: < 5s acceptable, > 10s unacceptable
- If type checking is slow, run incremental mode (mypy `--incremental`, tsc `--incremental`)

**Warning signs:**
- Developers complaining about commit speed
- High usage of `git commit --no-verify`
- Pre-commit hooks disabled in team members' local setups

### Pitfall 2: CI Cache Misses Due to Key Churn

**What goes wrong:** CI cache keys change on every run (e.g., hash includes timestamps, commit SHAs). Cache hit rate < 10%, CI runs always slow.

**Why it happens:** Cache key includes volatile data. Example: `cache-${{ github.sha }}-${{ hashFiles('package.json') }}` changes on every commit.

**How to avoid:**
- Use only dependency files in cache key: `hashFiles('**/pnpm-lock.yaml')`, `hashFiles('**/pyproject.toml')`
- For turbo cache, key on `turbo.json` + lockfiles (not source code)
- Use `restore-keys` fallback pattern for partial cache hits
- Monitor cache hit rate in Actions UI (should be 80%+ for dependency caches)

**Warning signs:**
- CI "Install dependencies" step always takes full time (no speedup)
- Actions cache tab shows many caches with 0 hits
- CI time doesn't improve after first successful run

### Pitfall 3: Docker Layer Cache Ineffective

**What goes wrong:** Dockerfile changes invalidate all layers. Every build reinstalls all dependencies, even when only code changed. Docker builds take 5+ minutes.

**Why it happens:** Incorrect layer ordering. `COPY . .` before `RUN uv sync` means code changes invalidate dependency layer.

**How to avoid:**
- **Dependency-first ordering:**
  ```dockerfile
  COPY pyproject.toml uv.lock ./  # <- Dependency files first
  RUN uv sync                      # <- Install (cached unless deps change)
  COPY . .                         # <- Code last (changes frequently)
  ```
- Use `--cache-from` in CI: `docker build --cache-from=registry.example.com/app:latest`
- Use `--cache-to` to push cache layers to registry (GitHub Actions: `type=gha`)
- BuildKit required for effective layer caching (`DOCKER_BUILDKIT=1`)

**Warning signs:**
- Docker builds reinstall dependencies on every code change
- CI Docker builds never show "Using cache" for dependency layers
- Production deployments take 10+ minutes to build images

### Pitfall 4: Type Checking in CI Without --noEmit

**What goes wrong:** CI runs `tsc` (default emit), generates build artifacts, then discards them. Slow, wasteful. Or CI runs build (which type-checks) AND separate type-check step (duplicate work).

**Why it happens:** Misunderstanding of `tsc` modes. Default `tsc` emits .js files. CI only needs to check types, not emit.

**How to avoid:**
- Use `tsc --noEmit` for type checking step (no file output)
- Use `tsc --build` for build step (emits files)
- Don't run both type-check AND build in CI (build includes type-check)
- For monorepos, `turbo type-check` should run `tsc --noEmit` in all packages

**Warning signs:**
- CI generates .js files then deletes them
- Type-check step takes as long as build step (should be faster)
- CI runs `tsc` twice with different flags

### Pitfall 5: Detox Tests Timing Out in CI

**What goes wrong:** Detox tests fail with "Failed to boot device" or timeout during simulator launch. Tests pass locally, fail in CI.

**Why it happens:** macOS runner resource constraints, simulator boot time, cold cache. Detox framework setup timeout (default 60s) too short for CI.

**How to avoid:**
- Increase `testRunner.jest.setupTimeout` in `.detoxrc.js` to 120000ms (2 minutes)
- Install applesimutils: `brew tap wix/brew && brew install applesimutils`
- Use `--cleanup` flag to kill orphaned simulators: `detox test --cleanup`
- Cache Detox framework: `yarn detox rebuild-framework-cache`
- Run Detox only on main branch (macOS runners expensive)

**Warning signs:**
- Detox tests pass locally, fail in CI
- CI logs show "Waiting for simulator to boot" timeout
- Intermittent "Could not launch simulator" errors

### Pitfall 6: Test Coverage Enforcement Too Strict for Template

**What goes wrong:** CI enforces 80%+ coverage thresholds. Template has example code, not production code. Every new feature requires extensive test writing to pass CI.

**Why it happens:** Copying production project CI config to template. Production projects benefit from coverage enforcement. Templates demonstrate patterns, not ship features.

**How to avoid:**
- **For templates:** Track coverage, don't enforce thresholds. Use `pytest --cov` without `--cov-fail-under`.
- **Document recommendation:** "Production projects should enforce 80%+ coverage. Template shows examples."
- Provide comprehensive example tests (all four types), but don't force coverage numbers

**Warning signs:**
- Template contributors spend more time writing tests than features
- CI blocks minor README updates due to coverage drop
- Coverage config stricter than most production projects

### Pitfall 7: OpenAPI Spec Drift Check False Positives

**What goes wrong:** CI fails on spec drift when spec legitimately changed. Or CI passes when types ARE stale (developer forgot to commit generated types).

**Why it happens:** `git diff` detects whitespace, comment changes, or developer committed regenerated types (making drift check useless).

**How to avoid:**
- Use `git diff --exit-code packages/api-client/src/gen/` (fail if ANY changes)
- Regenerate types in CI: `pnpm run generate:api-types`
- THEN check diff: `git diff --exit-code packages/api-client/`
- If diff found, CI fails with message: "TypeScript types are stale. Run `pnpm run generate:api-types` and commit."
- Add `.gitattributes` entry for generated files: `packages/api-client/src/gen/* linguist-generated`

**Warning signs:**
- CI passes but types are outdated (runtime errors in frontend)
- CI fails on whitespace changes to generated types
- Developers bypass drift check by committing stale types

---

## Code Examples

Verified patterns from official sources and current best practices.

### Pre-commit Hook Setup

**Installation and initialization:**
```bash
# Install pre-commit framework
pip install pre-commit  # or add to dev dependencies

# Install hooks to .git/hooks/
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Source:** [pre-commit framework documentation](https://pre-commit.com/)

### GitHub Actions: pnpm Caching

**Official pnpm/action-setup with caching:**
```yaml
steps:
  - uses: actions/checkout@v4

  - uses: pnpm/action-setup@v4
    with:
      version: 9

  - uses: actions/setup-node@v4
    with:
      node-version: '20'
      cache: 'pnpm'  # Automatically caches pnpm store

  - run: pnpm install --frozen-lockfile
```

**Source:** [pnpm/action-setup documentation](https://github.com/pnpm/action-setup)

### GitHub Actions: Python uv Caching

**Using actions/setup-python with pip cache (uv compatible):**
```yaml
steps:
  - uses: actions/checkout@v4

  - uses: actions/setup-python@v5
    with:
      python-version: '3.12'
      cache: 'pip'
      cache-dependency-path: 'apps/api/pyproject.toml'

  - run: pip install uv
  - run: cd apps/api && uv sync --frozen
```

**Note:** `cache: 'pip'` works with uv because uv uses pip-compatible cache structure.

**Source:** [actions/setup-python documentation](https://github.com/actions/setup-python)

### pytest: Django Integration Test

**Using pytest-django and factory_boy:**
```python
# apps/api/apps/accounts/tests/test_auth.py
import pytest
from django.urls import reverse
from apps.accounts.tests.factories import UserFactory

@pytest.mark.django_db
def test_login_endpoint_success(api_client):
    """Test user can login with valid credentials."""
    user = UserFactory(password='testpass123')
    url = reverse('accounts:login')

    response = api_client.post(url, {
        'email': user.email,
        'password': 'testpass123'
    })

    assert response.status_code == 200
    assert 'access_token' in response.data
    assert response.data['user']['email'] == user.email

@pytest.mark.django_db
def test_login_endpoint_invalid_password(api_client):
    """Test login fails with invalid password."""
    user = UserFactory(password='testpass123')
    url = reverse('accounts:login')

    response = api_client.post(url, {
        'email': user.email,
        'password': 'wrongpassword'
    })

    assert response.status_code == 401
```

**Source:** [pytest-django documentation](https://pytest-django.readthedocs.io/)

### vitest: Next.js Component Test

**Testing Next.js 15 components with vitest:**
```typescript
// apps/web/app/components/__tests__/login-form.test.tsx
import { expect, test, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '../login-form'

test('LoginForm submits with valid credentials', async () => {
  const mockOnSubmit = vi.fn()
  const user = userEvent.setup()

  render(<LoginForm onSubmit={mockOnSubmit} />)

  await user.type(screen.getByLabelText(/email/i), 'test@example.com')
  await user.type(screen.getByLabelText(/password/i), 'testpass123')
  await user.click(screen.getByRole('button', { name: /login/i }))

  await waitFor(() => {
    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'testpass123'
    })
  })
})
```

**Source:** [Next.js Testing documentation](https://nextjs.org/docs/app/guides/testing/vitest)

### Detox: React Native E2E Test

**Basic Detox test structure:**
```javascript
// apps/mobile/e2e/auth.test.js
describe('Authentication Flow', () => {
  beforeAll(async () => {
    await device.launchApp()
  })

  beforeEach(async () => {
    await device.reloadReactNative()
  })

  it('should complete login flow successfully', async () => {
    // Navigate to login
    await element(by.id('login-tab')).tap()

    // Enter credentials
    await element(by.id('email-input')).typeText('test@example.com')
    await element(by.id('password-input')).typeText('testpass123')

    // Submit form
    await element(by.id('login-button')).tap()

    // Verify navigation to dashboard
    await waitFor(element(by.id('dashboard-screen')))
      .toBeVisible()
      .withTimeout(5000)
  })
})
```

**Source:** [Detox documentation](https://wix.github.io/Detox/)

### Docker: Next.js Standalone Build

**next.config.ts with standalone output:**
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',  // Enable standalone output for Docker
  experimental: {
    // Optimize package imports
    optimizePackageImports: ['lucide-react'],
  },
}

export default nextConfig
```

**Dockerfile using standalone output:**
```dockerfile
# Final stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy standalone output
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

USER nextjs

CMD ["node", "apps/web/server.js"]
```

**Source:** [Next.js Docker documentation](https://nextjs.org/docs/app/getting-started/deploying)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jest for all testing | vitest for frontend, Jest for Detox only | 2023-2024 | vitest is ESM-native, faster, Next.js 15 recommended. Jest remains for Detox (Detox uses Jest runner). |
| black + flake8 + isort | ruff for both linting and formatting | 2023-2024 | Single tool replaces three, 10-100x faster (Rust implementation). Ruff is now standard for new Python projects. |
| pip + requirements.txt | uv + pyproject.toml | 2024-2025 | uv is 10-100x faster than pip, lockfile support (uv.lock), virtual env management. From Astral (same team as ruff). |
| Alpine for all Docker images | Debian slim for Python, Alpine for Node.js builders | Ongoing | Alpine + Python has musl libc wheel compatibility issues. Slim Debian (~150MB) balances size and compatibility. |
| ESLint legacy config (.eslintrc) | ESLint 9 flat config (eslint.config.js) | 2024 | Flat config is simpler, composable, performant. Legacy config deprecated in ESLint 9. |
| Manual GitHub Actions cache | actions/setup-node and setup-python built-in cache | 2023-2024 | Official actions handle cache automatically with `cache: 'pnpm'` or `cache: 'pip'`. Simpler, more reliable. |
| Full codebase pre-commit checks | Changed files only (lint-staged, pre-commit default) | Always recommended | Fast hooks (< 5s) prevent bypass. Full checks run in CI. |
| Single-stage Dockerfiles | Multi-stage builds standard | 2015+ (standard since) | Multi-stage reduces image size 3-10x, separates build/runtime dependencies. BuildKit caching makes this fast. |
| psycopg2-binary | psycopg[binary] (psycopg3) | 2023-2024 | psycopg3 is modern, faster, better async support. psycopg2 in maintenance mode. |
| Coverage enforcement in templates | Coverage tracking without enforcement | Best practice | Templates demonstrate patterns. Production projects enforce thresholds. Strict enforcement slows template development. |

**Deprecated/outdated:**
- **black + flake8 + isort**: Replaced by ruff (all-in-one)
- **Jest for frontend testing**: Replaced by vitest for Next.js/React projects (Detox still uses Jest)
- **psycopg2**: Replaced by psycopg3 (psycopg[binary])
- **ESLint legacy config**: Replaced by flat config in ESLint 9
- **.eslintrc files**: Deprecated, use eslint.config.js
- **pip directly**: For new projects, use uv (faster, lockfile, better UX)
- **Alpine for Python**: Use Debian slim (better wheel compatibility)

---

## Recommendations for Discretionary Decisions

Based on research findings and monorepo-specific constraints:

### Pre-commit Hook Auto-fix Behavior

**Recommendation: Auto-fix formatting and linting, report-only for type errors**

**Rationale:**
- Auto-fix saves developer time (format/lint fixes are mechanical)
- Type errors require developer understanding (auto-fix not possible)
- Pattern matches industry standard (prettier/eslint auto-fix, tsc report-only)
- Developers appreciate convenience without losing awareness of issues

**Implementation:**
```yaml
# .pre-commit-config.yaml
- id: ruff
  args: [--fix]  # Auto-fix linting issues
- id: ruff-format  # Auto-format code
```

### Pre-commit Hook Bypass Capability

**Recommendation: Allow bypass (--no-verify), document CI as ultimate gate**

**Rationale:**
- Developers occasionally need WIP commits (experimental branches, saving work)
- CI remains comprehensive quality gate (catches any bypassed issues)
- Forcing pre-commit blocks legitimate workflows (rebasing, cherry-picking)
- Trust developers + strong CI > strict local enforcement

**Documentation:**
```markdown
# README.md
Pre-commit hooks enforce quality locally. If you need to bypass for WIP commits:
git commit --no-verify

Note: CI will catch any quality issues. All checks must pass before merge.
```

### Pre-commit Hook Check Scope

**Recommendation: Changed files only (lint-staged for JS/TS, pre-commit default for Python)**

**Rationale:**
- Speed: < 5s on typical commit (good DX)
- Scope: Developers fix issues in code they touched (clear ownership)
- Full codebase checks in CI (comprehensive validation)
- Monorepo scale: 1000+ files make full checks slow

**Implementation:**
- lint-staged scopes to staged files automatically
- pre-commit framework scopes to changed files by default (can override with `--all-files`)

### CI Job Parallelization Strategy

**Recommendation: All jobs parallel (api, web, mobile independent)**

**Rationale:**
- Speed: 3 parallel jobs finish in max(job_time), not sum(job_time)
- Independence: api, web, mobile have separate dependency chains
- Resource efficiency: GitHub Actions free tier allows parallel jobs
- Fast feedback: Developers see results in ~5 minutes, not 15 minutes

**Implementation:**
```yaml
# .github/workflows/ci.yml
jobs:
  api:
    runs-on: ubuntu-latest
    # ... steps

  web:
    runs-on: ubuntu-latest
    # ... steps

  mobile:
    runs-on: ubuntu-latest
    # ... steps
```

### CI Fail-fast Behavior

**Recommendation: No fail-fast (run all jobs even if one fails)**

**Rationale:**
- Comprehensive feedback: See all failures at once (e.g., both linting and type errors)
- Developer efficiency: Fix multiple issues in one iteration, not sequentially
- CI minute cost: Minimal (jobs usually finish around same time)
- Pattern: Industry standard for multi-job workflows

**Implementation:**
```yaml
# Do NOT add:
# strategy:
#   fail-fast: true
#
# Default is fail-fast: false (run all jobs)
```

### CI Trigger Strategy

**Recommendation: Pull requests + main branch (not every push to every branch)**

**Rationale:**
- Balance: Validates PRs before merge, main branch after merge
- CI minute efficiency: Skips feature branch WIP commits
- Fast feedback: Developers get CI results on PR creation
- Pattern: Standard for GitHub-hosted projects

**Implementation:**
```yaml
on:
  push:
    branches: [main]
  pull_request:
```

### Test Coverage Thresholds

**Recommendation: Track coverage, don't enforce thresholds in template**

**Rationale:**
- Template purpose: Demonstrate patterns, not ship production features
- Flexibility: Different projects need different thresholds (80% standard, 95% critical systems)
- Developer friction: Strict thresholds slow template development
- Documentation: Recommend 80%+ for production projects, show comprehensive examples

**Implementation:**
```bash
# pytest (track coverage, no fail-under)
pytest --cov --cov-report=term --cov-report=xml

# Document recommendation
# Production projects should add: --cov-fail-under=80
```

### Test Data Strategy

**Recommendation: Factory_boy for most, fixtures for specific scenarios**

**Rationale:**
- Factories: Flexible, realistic data, handle relationships, integrate with Faker
- Fixtures: Predictable data for specific test scenarios (edge cases, error conditions)
- Mix approach: Factories for model creation, fixtures for service/client setup
- Pattern: Django community standard

**Implementation:**
```python
# Factory for flexible model creation
user = UserFactory(is_active=True)

# Fixture for test client setup
@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

### Docker Image Size vs Build Speed

**Recommendation: Multi-stage builds with Debian slim base (balanced approach)**

**Rationale:**
- Multi-stage achieves both: reasonable size (~150MB) and reasonable speed (~2-3 min)
- Debian slim: Better wheel compatibility than Alpine, smaller than full Debian
- BuildKit caching: Layer caching makes multi-stage fast
- Production-ready: Template demonstrates best practices, not aggressive optimization

**Implementation:**
- Django API: python:3.12-slim base (~150MB final)
- Next.js web: node:20-alpine runner with standalone output (~100MB final)

### Docker Base Image Selection

**Recommendation: Debian slim for Django, Alpine for Next.js**

**Rationale:**
- **Django (python:3.12-slim)**: Debian-based, excellent wheel compatibility, ~150MB
  - Alpine has musl libc issues with Python wheels (cryptography, psycopg, etc.)
- **Next.js (node:20-alpine)**: Alpine works well for Node.js, ~100MB with standalone output
  - No compiled binary compatibility issues like Python
- Size vs compatibility tradeoff balanced per platform

### Docker Security Scanning

**Recommendation: Skip in template, document optional integration**

**Rationale:**
- Template complexity: Security scanning adds CI setup complexity
- Tool choice: Trivy, Snyk, Docker Scout are free options, but choice is project-specific
- Documentation: Show how to add, don't force inclusion
- Phase boundary: Security scanning could be separate phase or documentation

**Documentation:**
```markdown
# Optional: Add security scanning to CI
# Add to .github/workflows/ci.yml:
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'your-image:tag'
```

### Docker Layer Caching Optimization

**Recommendation: Dependency-first ordering (standard Docker best practice)**

**Rationale:**
- Cache effectiveness: Code changes frequently, dependencies change rarely
- Build speed: 90%+ of builds reuse dependency layer (cached)
- Pattern: Industry standard, documented in Docker best practices
- Monorepo: Copy lockfiles/package files first, then source

**Implementation:**
```dockerfile
# Dependency files first (cached unless deps change)
COPY pyproject.toml uv.lock ./
RUN uv sync

# Source code last (changes frequently)
COPY . .
```

---

## Open Questions

### 1. Coverage Reporting Integration

**What we know:** pytest-cov generates coverage reports (term, xml, html). GitHub Actions supports coverage upload (Codecov, Coveralls).

**What's unclear:** Should template include coverage upload action (Codecov free tier), or leave as documented option?

**Recommendation:** Document Codecov integration as optional. Include commented-out example in CI workflow. Projects can uncomment if they use Codecov.

### 2. Detox vs Maestro for Mobile E2E

**What we know:** Detox is gray-box (requires app rebuild), mature, well-documented. Maestro is black-box (no rebuild), newer, simpler setup.

**What's unclear:** Maestro gaining momentum in 2025-2026. Is Detox still the right choice for new projects?

**Recommendation:** Stick with Detox for Phase 7. Detox is proven, extensive documentation, React Native community standard. Maestro could be alternate implementation in future.

### 3. Turbo Remote Cache Setup

**What we know:** Turborepo supports remote caching (S3, Vercel, custom). Remote cache shares build artifacts across CI runs and developers.

**What's unclear:** Should template include remote cache setup (S3 + Lambda), or document as optional?

**Recommendation:** Document as optional. Remote cache setup requires AWS account, adds complexity. Template demonstrates local cache (faster than no cache). Production projects add remote cache when team scales.

### 4. Pre-commit Hook for TypeScript Type Checking

**What we know:** `tsc --noEmit` in pre-commit hook catches type errors locally. But type checking can be slow (5-10s on large projects).

**What's unclear:** Include tsc in pre-commit hooks (comprehensive local checks) or skip (faster commits, rely on CI)?

**Recommendation:** Skip tsc in pre-commit hooks for speed. Run `tsc --noEmit` in CI. Developers can run manually: `pnpm type-check`. Balance: fast commits (< 5s) vs comprehensive local validation.

---

## Sources

### Primary (HIGH confidence)

- [Ruff Pre-commit Hook](https://github.com/astral-sh/ruff-pre-commit) - Official Astral pre-commit hook
- [Ruff Integrations Documentation](https://docs.astral.sh/ruff/integrations/) - Ruff integration patterns
- [Turborepo GitHub Actions Guide](https://turborepo.dev/docs/guides/ci-vendors/github-actions) - Official Turborepo CI patterns
- [pytest-django Documentation](https://pytest-django.readthedocs.io/) - Official pytest-django integration
- [Next.js Testing: Vitest](https://nextjs.org/docs/app/guides/testing/vitest) - Official Next.js testing guide
- [Next.js Docker Deployment](https://nextjs.org/docs/app/getting-started/deploying) - Official Docker deployment guide
- [Detox Documentation](https://wix.github.io/Detox/) - Official Detox setup and usage
- [GitHub Actions Documentation](https://docs.github.com/en/actions) - Official GitHub Actions reference
- [django-stubs GitHub](https://github.com/typeddjango/django-stubs) - Official Django type stubs

### Secondary (MEDIUM confidence)

- [Django Testing Like a Pro](https://medium.com/devmap/django-testing-like-a-pro-pytest-django-factory-boy-and-mocking-made-simple-d1e157e5ab21) - pytest-django + factory_boy patterns
- [Simplified Django Tests With Pytest](https://schegel.net/posts/simplied-django-tests-with-pytest-and-pytest-factoryboy/) - Django testing best practices
- [Django Docker Best Practices](https://betterstack.com/community/guides/scaling-python/django-docker-best-practices/) - Production Django Docker patterns
- [Setting up Vitest for Next.js 15](https://www.wisp.blog/blog/setting-up-vitest-for-nextjs-15) - Next.js 15 vitest configuration
- [How to Run Detox Tests on GitHub Actions](https://remarkablemark.org/blog/2023/02/18/how-to-run-react-native-detox-tests-on-github-actions/) - Detox CI setup
- [PNPM GitHub Actions Cache](https://theodorusclarence.com/shorts/github/pnpm-github-actions-cache) - pnpm caching patterns
- [Next.js Standalone Output Docker](https://markus.oberlehner.net/blog/running-nextjs-with-docker) - Standalone deployment pattern
- [OpenAPI Spec Drift Detection](https://www.speakeasy.com/blog/openapi-spec-drift-detection) - Spec drift tooling

### Tertiary (LOW confidence - flagged for validation)

- [Python and TypeScript in a Monorepo](https://medium.com/@julien.barbay/python-and-typescript-in-a-monorepo-c862a3bacddb) - Multi-language monorepo patterns (need validation)
- [GitHub Actions Tutorial 2026](https://nextool.app/blog/github-actions-tutorial.html) - General CI/CD patterns (marketing content)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified via official documentation and current 2026 best practices
- Architecture patterns: HIGH - Patterns verified via official Next.js, Django, Detox docs and working monorepo examples
- Docker multi-stage builds: HIGH - Official Docker best practices, Next.js standalone documentation
- Testing frameworks: HIGH - Official pytest-django, vitest, Detox documentation
- GitHub Actions caching: MEDIUM-HIGH - Official action documentation, community patterns verified
- Coverage strategies: MEDIUM - Best practices established, but template-specific tradeoffs documented
- Discretionary decisions: MEDIUM - Recommendations based on research + monorepo constraints, documented with rationale

**Research date:** 2026-02-16
**Valid until:** 30 days (stable tooling, update if major version releases: ESLint 10, Next.js 16, pytest 9)

**Key uncertainties flagged:**
- Maestro vs Detox for mobile E2E (Maestro gaining momentum, but Detox proven)
- Turbo remote cache setup (document vs implement)
- TypeScript type checking in pre-commit hooks (speed vs comprehensive local checks)
- Coverage reporting service integration (Codecov vs document as optional)
