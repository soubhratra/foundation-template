# Conventions Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

This document defines naming, structure, and style conventions for every language and framework in the Foundation Template. Consistency across the monorepo reduces cognitive load, enables effective code review, and makes the codebase navigable for new developers. These conventions are enforced by automated tooling (ruff, ESLint, Prettier, pre-commit) where possible.

## Specifications

### Python Conventions (Django / apps/api/)

#### Module and File Naming

| Item                    | Convention                | Example                                          |
| ----------------------- | ------------------------- | ------------------------------------------------ |
| Django app names        | snake_case, plural nouns  | `accounts`, `core`, `ai`                         |
| Python files            | snake_case                | `user_service.py`, `auth_schemas.py`             |
| Classes                 | PascalCase                | `UserService`, `AccountController`               |
| Functions / methods     | snake_case                | `get_current_user()`, `create_embedding()`       |
| Constants               | UPPER_SNAKE_CASE          | `MAX_EMBEDDING_DIMENSIONS`, `DEFAULT_PAGE_SIZE`  |
| Private methods         | leading underscore        | `_validate_token()`                              |
| Django model classes    | PascalCase, singular noun | `User`, `Document`, `Embedding`                  |
| Pydantic schema classes | PascalCase with suffix    | `UserOut`, `UserCreateIn`, `LoginIn`, `TokenOut` |

#### Pydantic Schema Naming Convention

| Suffix   | Usage                        | Example                                      |
| -------- | ---------------------------- | -------------------------------------------- |
| `In`     | Request body schemas (input) | `UserCreateIn`, `LoginIn`, `PasswordResetIn` |
| `Out`    | Response schemas (output)    | `UserOut`, `TokenOut`, `ErrorOut`            |
| `Filter` | Query parameter schemas      | `UserFilter`, `DocumentFilter`               |
| `Update` | Partial update schemas       | `UserUpdateIn`, `ProfileUpdateIn`            |

#### Django App Structure (Layered Pattern)

Every Django app follows this structure:

```
apps/api/apps/<app_name>/
+-- __init__.py
+-- models.py           # Django ORM models
+-- schemas.py          # Pydantic schemas for Ninja Extra
+-- controllers.py      # Ninja Extra controllers (HTTP layer)
+-- services.py         # Business logic (testable without HTTP)
+-- admin.py            # Django admin configuration
+-- tests/
|   +-- __init__.py
|   +-- test_services.py
|   +-- test_controllers.py
|   +-- conftest.py     # App-specific fixtures
+-- migrations/
    +-- __init__.py
```

**Layer responsibilities:**

- **controllers.py**: HTTP concerns only. Request parsing, auth checking, delegating to services, returning responses.
- **services.py**: Business logic. Testable without HTTP context. Receives typed inputs, returns domain objects.
- **models.py**: Data layer. Django ORM models, custom managers, querysets.
- **schemas.py**: Pydantic schemas defining the API contract. Input validation and output serialization.

#### ruff Configuration

```toml
# ruff.toml (repo root)
[lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "SIM", "TCH"]
ignore = ["E501"]  # Line length handled by formatter

[lint.isort]
known-first-party = ["apps", "config"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

#### Import Ordering

ruff enforces import ordering (replaces isort):

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
from django.db import models
from ninja_extra import api_controller, route
from pydantic import BaseModel

# 3. First-party (project)
from apps.core.models import BaseModel as BaseDBModel
from apps.accounts.services import UserService
```

#### Django Settings Structure

```
config/settings/
+-- __init__.py         # Empty
+-- base.py             # Shared settings (INSTALLED_APPS, MIDDLEWARE, etc.)
+-- development.py      # from .base import *; DEBUG=True, console email, etc.
+-- production.py       # from .base import *; DEBUG=False, real email, etc.
```

Selected via `DJANGO_SETTINGS_MODULE=config.settings.development` environment variable.

### TypeScript/JavaScript Conventions

#### File Naming

| Item            | Convention                   | Example                                     |
| --------------- | ---------------------------- | ------------------------------------------- |
| Component files | kebab-case                   | `user-profile.tsx`, `auth-form.tsx`         |
| Hook files      | kebab-case with use- prefix  | `use-auth.ts`, `use-current-user.ts`        |
| Utility files   | kebab-case                   | `format-date.ts`, `api-helpers.ts`          |
| Type files      | kebab-case                   | `user-types.ts`, `api-types.d.ts`           |
| Test files      | kebab-case with .test suffix | `user-profile.test.tsx`, `use-auth.test.ts` |
| Config files    | kebab-case or standard names | `eslint.config.js`, `tailwind.config.ts`    |
| Constant files  | kebab-case                   | `route-paths.ts`, `api-endpoints.ts`        |

#### Component and Export Naming

| Item             | Convention                | Example                                           |
| ---------------- | ------------------------- | ------------------------------------------------- |
| React components | PascalCase                | `UserProfile`, `AuthForm`, `DashboardLayout`      |
| Hooks            | camelCase with use prefix | `useAuth`, `useCurrentUser`, `useApiClient`       |
| Utilities        | camelCase                 | `formatDate`, `parseApiError`, `buildQueryString` |
| Constants        | UPPER_SNAKE_CASE          | `API_BASE_URL`, `MAX_FILE_SIZE`                   |
| Types/Interfaces | PascalCase                | `User`, `AuthState`, `ApiResponse<T>`             |
| Enums            | PascalCase                | `UserRole`, `AuthStatus`                          |

#### Barrel Exports

Every package and significant directory uses an `index.ts` barrel export:

```typescript
// packages/schemas/src/index.ts
export { loginSchema, signupSchema } from "./auth";
export { userProfileSchema } from "./user";
export { emailSchema, passwordSchema } from "./common";
export type { LoginInput, SignupInput } from "./auth";
```

**Rules:**

- Barrel exports in `packages/*/src/index.ts` -- always.
- Barrel exports in `apps/*/components/` -- optional, use when directory has 5+ components.
- Never re-export third-party libraries through barrels.

#### ESLint 9 Flat Config

```javascript
// packages/config-eslint/index.js
import tseslint from "typescript-eslint";

export const baseConfig = tseslint.config(...tseslint.configs.recommended, {
  ignores: ["**/dist/**", "**/.next/**", "**/node_modules/**"],
});

// packages/config-eslint/next.js
import { baseConfig } from "./index.js";
import reactPlugin from "eslint-plugin-react";
import nextPlugin from "@next/eslint-plugin-next";

export const nextConfig = tseslint.config(...baseConfig, {
  plugins: { react: reactPlugin, "@next/next": nextPlugin },
});

// packages/config-eslint/react-native.js
import { baseConfig } from "./index.js";
import reactPlugin from "eslint-plugin-react";

export const reactNativeConfig = tseslint.config(...baseConfig, {
  plugins: { react: reactPlugin },
});
```

**ESLint 9 flat config is mandatory.** Legacy `.eslintrc` files must not exist anywhere in the repo.

### Monorepo Conventions

#### Package Scope

All internal packages use the `@repo/` scope:

| Package                 | Name                  |
| ----------------------- | --------------------- |
| API client              | `@repo/api-client`    |
| Validation schemas      | `@repo/schemas`       |
| UI primitives           | `@repo/ui-primitives` |
| ESLint config           | `@repo/config-eslint` |
| TypeScript config       | `@repo/config-ts`     |
| Django API (tasks only) | `@repo/api`           |

**Rules:**

- `@repo/` scope is reserved for internal packages. Never publish to npm.
- Each package.json declares `"private": true`.
- Internal dependencies use `"workspace:*"` protocol in pnpm.

#### Package.json `exports` Field

Every shared package must declare proper `exports` for both dev and build:

```json
{
  "name": "@repo/schemas",
  "private": true,
  "main": "src/index.ts",
  "types": "src/index.ts",
  "exports": {
    ".": {
      "types": "./src/index.ts",
      "default": "./src/index.ts"
    }
  }
}
```

### Git Conventions

#### Branch Naming

| Pattern                  | Usage                 | Example                       |
| ------------------------ | --------------------- | ----------------------------- |
| `main`                   | Production-ready code | --                            |
| `feat/<description>`     | New features          | `feat/user-profile-page`      |
| `fix/<description>`      | Bug fixes             | `fix/login-csrf-token`        |
| `chore/<description>`    | Maintenance tasks     | `chore/update-dependencies`   |
| `docs/<description>`     | Documentation only    | `docs/api-contracts-spec`     |
| `refactor/<description>` | Code restructuring    | `refactor/auth-service-layer` |

#### Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `style`

**Scopes:** `api`, `web`, `mobile`, `api-client`, `schemas`, `ui`, `config`, `docker`, `ci`

**Examples:**

```
feat(api): add user profile update endpoint
fix(web): resolve CSRF token forwarding in auth proxy
chore(config): update ruff to v0.8.1
refactor(api): extract user service from controller
test(api): add auth flow integration tests
ci: add OpenAPI spec drift detection
```

### Environment Variables

#### Strategy Per Service

| Service        | Env File              | Gitignored | Prefix Rules                           |
| -------------- | --------------------- | ---------- | -------------------------------------- |
| Docker Compose | `.env`                | Yes        | None                                   |
| Django         | `apps/api/.env`       | Yes        | None                                   |
| Next.js        | `apps/web/.env.local` | Yes        | `NEXT_PUBLIC_` for client-exposed vars |
| Expo           | `apps/mobile/.env`    | Yes        | `EXPO_PUBLIC_` for client-exposed vars |

Each service has a committed `.env.example` with dummy values:

```
# apps/api/.env.example
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=postgres://foundation:foundation@localhost:5432/foundation
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# apps/web/.env.example
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Rules:**

- `.env` files are ALWAYS gitignored. Never commit secrets.
- `.env.example` files are ALWAYS committed. Document every required variable.
- Validate env vars on startup (Django: django-environ, Next.js: built-in).
- Never hardcode URLs. Use environment variables for all service URLs.

### File Organization Patterns

#### Next.js App Router (apps/web/)

```
app/
+-- (auth)/                  # Route group: unauthenticated pages
|   +-- login/
|   |   +-- page.tsx
|   +-- signup/
|   |   +-- page.tsx
|   +-- layout.tsx           # Auth layout (centered card)
+-- (dashboard)/             # Route group: authenticated pages
|   +-- page.tsx             # Dashboard home
|   +-- settings/
|   |   +-- page.tsx
|   +-- layout.tsx           # Dashboard layout (sidebar + header)
+-- api/                     # BFF proxy routes
|   +-- auth/
|       +-- [...path]/
|           +-- route.ts     # Proxy to Django auth endpoints
+-- layout.tsx               # Root layout (providers, fonts)
+-- page.tsx                 # Landing page
```

#### Expo Router (apps/mobile/)

```
app/
+-- (auth)/                  # Auth screens
|   +-- login.tsx
|   +-- signup.tsx
|   +-- _layout.tsx          # Stack navigator
+-- (tabs)/                  # Tab navigation
|   +-- index.tsx            # Home tab
|   +-- settings.tsx         # Settings tab
|   +-- _layout.tsx          # Tab navigator
+-- _layout.tsx              # Root layout (auth check)
```

#### Django Ninja Extra (apps/api/)

```
apps/
+-- accounts/                # User-related
|   +-- controllers.py       # @api_controller('/users')
|   +-- services.py          # UserService class
|   +-- models.py            # CustomUser(AbstractUser)
|   +-- schemas.py           # UserOut, LoginIn, etc.
+-- core/                    # Shared utilities
|   +-- models.py            # BaseModel mixin (timestamps, soft delete)
|   +-- schemas.py           # PaginatedResponse, ErrorOut
|   +-- exceptions.py        # Custom exception classes
+-- ai/                      # AI module (removable)
    +-- controllers.py       # @api_controller('/ai')
    +-- services.py          # AI service layer
    +-- graphs/              # LangGraph definitions
    +-- models.py            # EmbeddingMixin
    +-- tasks.py             # Celery tasks
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Python quality
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0 # Pin to specific version
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # JS/TS quality (via lint-staged)
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
      - id: check-merge-conflict
```

**lint-staged config (root package.json):**

```json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,yml,yaml}": ["prettier --write"]
  }
}
```

**Pre-Commit Implementation Strategy:**

- **Auto-fix with Block:** Hooks auto-fix format and lint issues where possible (`ruff --fix`, `eslint --fix`, `prettier --write`), but block commits if violations remain. Balances speed and control. _(Decision: Phase 07-devex-ci-cd)_

- **Staged Files Only:** Pre-commit runs only on staged files for speed (typical runtime <5 seconds). CI runs full checks on all files for completeness. _(Decision: Phase 07-devex-ci-cd)_

- **Scope:** Python (ruff), JS/TS (ESLint + Prettier via lint-staged), file hygiene (trailing whitespace, end-of-file, YAML syntax).

**Testing Conventions:**

- **Django Test Client:** Use Django's test client for Ninja Extra controllers, not direct controller instantiation. Avoids registry conflicts. _(Decision: Phase 07)_

- **PGVector Extension Ordering:** Create PGVector extension before any tables with vector fields in migration dependencies. Fields depend on extension types. _(Decision: Phase 07)_

- **Mobile E2E Scope:** Template includes iOS-only Detox configuration. Android can be added by users; keeping template simple. _(Decision: Phase 07)_

## Constraints

1. **File naming is enforced.** Python files: snake_case. TypeScript files: kebab-case. No exceptions. Linters catch violations.
2. **ESLint 9 flat config only.** No `.eslintrc`, `.eslintrc.json`, or `.eslintrc.yml` files anywhere in the repo.
3. **No `any` types in committed code.** TypeScript strict mode is enforced. Generated types from openapi-typescript are the only exception.
4. **Barrel exports required for all packages.** Every `packages/*/src/index.ts` must exist and export all public API.
5. **Django apps follow layered pattern.** Controllers, services, schemas, models -- not fat views.
6. **Commit messages follow conventional commits.** Pre-commit hook validates format.
7. **Environment variables are never hardcoded.** Use `.env.example` for documentation, `.env` for values, env var reads at runtime.

## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
