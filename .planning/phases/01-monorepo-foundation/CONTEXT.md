# Phase 1: Monorepo Foundation — Context

## Phase Goal

Developer can clone the repo, run `docker compose up`, and have Postgres + Redis running with an empty Django project, Next.js app, and Expo app all hot-reloading in the monorepo. A single `turbo dev` command starts all three application processes.

## Plans

- **01-01**: Turborepo + pnpm workspace scaffolding with shared config packages
- **01-02**: Docker Compose (Postgres + PGVector + Redis) and Django project with custom user model
- **01-03**: Next.js and Expo app scaffolds with Metro monorepo config
- **01-04**: Hybrid dev orchestration (`turbo dev`) and environment variable management

## Decisions Made (from Discussion)

### Decision 1: Django as pnpm Workspace for Turborepo Task Orchestration

**Context:** The architecture spec originally stated "apps/api is NOT a pnpm workspace" to emphasize that Python dependencies are managed by uv, not pnpm. However, Turborepo discovers tasks via `package.json` files in workspaces.

**Decision:** Add `apps/api` to `pnpm-workspace.yaml`. It will have a minimal `package.json` with only task scripts (`dev`, `lint`, `test`, `type-check`). No JS/TS dependencies — Python dependencies stay in `pyproject.toml` managed by uv.

**Implementation:**
```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

```json
// apps/api/package.json
{
  "name": "@repo/api",
  "private": true,
  "scripts": {
    "dev": "uv run python manage.py runserver 0.0.0.0:8000",
    "lint": "ruff check .",
    "test": "uv run pytest",
    "type-check": "uv run mypy .",
    "export-schema": "uv run python manage.py export_openapi_schema > ../../packages/api-client/openapi.json"
  }
}
```

**Rationale:** Single `turbo dev` starts Django, Next.js, and Expo simultaneously. Best DX for the "5 minutes to running" goal.

**Spec update needed:** Update `architecture.md` — change "apps/api is NOT a pnpm workspace" to "apps/api is a pnpm workspace for task orchestration only; it has no JS/TS dependencies."

### Decision 2: Fully Functional Config Packages from Phase 1

**Context:** `packages/config-eslint` and `packages/config-ts` could be scaffolded as stubs or delivered with real configurations.

**Decision:** Ship fully functional config packages in Phase 1. `config-eslint` will have ESLint 9 flat configs (base, next, react-native) and `config-ts` will have TypeScript configs (base, nextjs, react-native, library) as defined in `conventions.md`.

**Rationale:** Apps created in Phase 1 (Next.js, Expo) will extend these configs immediately. No config drift. No rework in Phase 7.

### Decision 3: pnpm `node-linker=hoisted` for Metro Compatibility

**Context:** Expo's Metro bundler has issues with pnpm's default `node-linker=isolated` (symlink-based node_modules). Expo SDK 52+ has built-in monorepo support but requires hoisted dependencies.

**Decision:** Add `.npmrc` to the monorepo root with `node-linker=hoisted`. This gives a flat node_modules structure that Metro can resolve without additional plugins.

**Implementation:**
```ini
# .npmrc
node-linker=hoisted
```

```javascript
// apps/mobile/metro.config.js — minimal, SDK 52+ built-in monorepo support
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
module.exports = config;
```

**Rationale:** Standard approach for Expo + pnpm monorepos. `expo-yarn-workspaces` is deprecated (replaced by SDK 52+ built-in support). No need for `watchFolders`, `nodeModulesPaths`, or resolver hacks.

## Key Constraints (from Specs)

1. **Custom user model before first migration.** `apps/api/apps/accounts/models.py` must define `CustomUser(AbstractUser)` and `AUTH_USER_MODEL` must be set BEFORE `manage.py migrate` is ever run. (architecture.md constraint 3)
2. **PGVector extension before vector models.** `core.0001_enable_pgvector` migration must run before any `VectorField` migration. (orm.md)
3. **Expo never in Docker.** Metro bundler runs on host always. (architecture.md constraint 5)
4. **ESLint 9 flat config only.** No `.eslintrc` files anywhere. (conventions.md constraint 2)
5. **All internal packages use `@repo/` scope.** (conventions.md)
6. **Docker images:** `pgvector/pgvector:pg16`, `redis:7-alpine`. (deployment.md)
7. **Split Django settings:** `base.py`, `development.py`, `production.py`. (conventions.md)
8. **ruff for Python linting/formatting.** No black, flake8, or isort. (stack.md)

## Spec References

| Spec | Relevance to Phase 1 |
|------|----------------------|
| `foundation/architecture.md` | Directory structure, workspace config, build order |
| `foundation/stack.md` | Technology versions, rejected technologies |
| `foundation/deployment.md` | Docker Compose config, env var strategy, Dockerfiles |
| `foundation/conventions.md` | ESLint config, tsconfig, ruff config, file naming |
| `foundation/data-models.md` | BaseModel mixin, CustomUser model |

## Success Criteria (from Roadmap)

1. `pnpm install` at repo root installs all JS/TS dependencies and Turborepo orchestrates workspace tasks
2. `docker compose up` starts Postgres 16 with PGVector and Redis; Django can connect and run migrations
3. `turbo dev` starts Django (with hot reload), Next.js (with hot reload), and Expo (with hot reload) simultaneously
4. Shared config packages (tsconfig, eslint) are consumed by all JS/TS apps without errors
5. `.env.example` files exist for all apps; missing required env vars produce clear error messages
