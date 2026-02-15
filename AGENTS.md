# AGENTS

This repo is a specs-first foundation template. The source of truth is
`openspec/specs/` and the root `CLAUDE.md` except instead of using claudecode as mentioned in CLAUDE.md we will be using opencode.

## Quick Context
- Monorepo: Turborepo with apps in `apps/` and shared packages in `packages/`.
- Backend: Django Ninja Extra (Python 3.12+), PostgreSQL 16+, PGVector.
- Web: Next.js 15 App Router, Tailwind CSS 4, shadcn/ui.
- Mobile: Expo (managed workflow), Expo Router.
- Do not propose alternative stacks.

## Commands (Build / Lint / Test)
Canonical commands live in `openspec/specs/foundation/deployment.md`.
The commands below match the template expectations.

### Root (Turborepo)
- Dev: `pnpm dev` (expects `turbo dev`)
- Build: `pnpm build` (expects `turbo build`)
- Lint: `pnpm lint` (expects `turbo lint`)
- Type check: `pnpm type-check` (expects `turbo type-check`)
- Test: `pnpm test` (expects `turbo test`)
- Generate shared types: `pnpm generate:types` (expects `turbo generate:api-types`)

### Backend (apps/api)
- Install deps: `cd apps/api && uv sync`
- Lint: `cd apps/api && uv run ruff check .`
- Format (apply): `cd apps/api && uv run ruff format .`
- Format (check): `cd apps/api && uv run ruff format --check .`
- Type check: `cd apps/api && uv run mypy .`
- All tests: `cd apps/api && uv run pytest`
- Single test file: `cd apps/api && uv run pytest apps/<app>/tests/test_file.py`
- Single test case: `cd apps/api && uv run pytest apps/<app>/tests/test_file.py::TestClass::test_name`
- Single test by keyword: `cd apps/api && uv run pytest -k "keyword"`

### Web + Packages (Vitest)
- Lint all: `pnpm turbo lint`
- Type check all: `pnpm turbo type-check`
- Test all: `pnpm turbo test`
- Single workspace tests: `pnpm --filter web test`
- Single test file: `pnpm --filter web test -- path/to/file.test.tsx`
- Single test name: `pnpm --filter web test -- -t "test name"`

### Mobile (Expo)
- Lint: `pnpm turbo lint --filter=mobile`
- Type check: `pnpm turbo type-check --filter=mobile`
- Unit tests: `pnpm --filter mobile test`
- E2E (Detox, main branch only): `detox test -c ios.sim.debug`

### Infra (Docker Compose)
- Start infra: `docker compose up -d db redis`
- Full dev stack: `docker compose -f docker-compose.full.yml up`

## Code Style and Conventions
These rules are mandatory; linters enforce most of them.

### Python (apps/api)
- Use `django-ninja-extra` `APIController` + router pattern.
- Type all function signatures; avoid `Any` unless unavoidable.
- Domain layout: `models.py`, `schemas.py`, `api.py`, `services.py`, `selectors.py`.
- Keep endpoints thin; business logic goes in services/selectors.
- Import order: stdlib -> third-party -> django -> project.
- Formatting: `ruff format` (double quotes, consistent line length).
- Naming: snake_case for files/functions, PascalCase for classes, UPPER_SNAKE for constants.
- Schema suffixes: `In`, `Out`, `Update`, `Filter`.
- Migrations are generated with `python manage.py makemigrations` only.

### TypeScript / React (apps/web, apps/mobile, packages)
- Next.js server components by default; add "use client" only when required.
- Use function declarations for components (no `const Component = () =>`).
- File names: kebab-case. Components: PascalCase. Hooks: camelCase with `use` prefix.
- Shared types come from `@repo/shared-types`; do not duplicate.
- Forms: React Hook Form + Zod; align with backend schemas.
- State: React Query for server state, Zustand for client-only state.
- ESLint 9 flat config only; no legacy `.eslintrc` files.

### React Native (apps/mobile)
- Expo managed workflow only.
- Use Expo Router for navigation.
- Prefer shared logic in `packages/` when feasible.
- Platform-specific files: `Component.ios.tsx` / `Component.android.tsx`.

### Monorepo Boundaries
- `apps/api/` is the only backend; other apps call it via REST.
- Cross-app code lives in `packages/`.
- Apps never import from each other.
- Internal packages use `@repo/*` and `workspace:*` versions.

## API Contracts and Types
- Every endpoint must have typed request and response schemas.
- Schemas live in `apps/api/<domain>/schemas.py` (Ninja schemas or Pydantic).
- After adding or modifying endpoints, regenerate `packages/shared-types/`.
- Shared TS types are generated; do not hand-edit them.

## Database Rules
- All DB access goes through Django ORM; no raw SQL without a comment.
- Migrations are created via `python manage.py makemigrations` only.
- Use PGVector with cosine similarity unless a spec states otherwise.
- Prefer HNSW indexes for vector search in production.

## AI / LangGraph
- Graphs live in `apps/api/agents/`.
- Each graph defines explicit state schema (TypedDict or Pydantic).
- Tools are standalone functions; avoid inline lambdas.
- Check `openspec/specs/backend/ai.md` before modifying agents.

## Error Handling
- API errors use a normalized envelope: `{ error: { code, message, details } }`.
- Validation errors include `details.field_errors` keyed by field name.
- Use Django Ninja Extra exception handlers to normalize errors.
- Clients show field errors inline; non-field errors via toast/alert.
- Do not expose stack traces in production responses.

## Testing Conventions
- Python tests: `test_<what>_<when>_<expected>` naming style.
- pytest-django uses Postgres + PGVector for integration tests.
- Web tests: Testing Library + Vitest, co-located with components.
- Use MSW for API mocking in frontend tests.
- Mobile unit tests with Jest; E2E with Detox only for critical flows.

## OpenSpec + GSD Workflow
- Specs in `openspec/specs/` are the source of truth (see `CLAUDE.md`).
- Default execution path for phases is GSD (discuss -> plan -> execute -> verify).
- Use OpenSpec only when requirements change or specs are missing/incorrect.
- Any change touching API contracts, auth, or data models requires `/opsx:new` first.
- Always sync specs (`/opsx:sync`) before GSD planning when requirements change.
- After implementation, update specs to reflect shipped behavior.
- Before starting a phase, read `ACTIVITY_LOG.md` and relevant `openspec/specs/<domain>/`.
- When working in an app, read its `apps/<app>/CLAUDE.md` if present.

## OpenSpec vs GSD Command Sequences
- OpenSpec is the governance layer for requirements changes.
- GSD is the implementation layer for plans and execution.

### Flow A: No Requirement Change
```
/gsd-discuss-phase <phase-number>
/gsd-plan-phase <phase-number>
/gsd-execute-phase <phase-number>
/gsd-verify-work <phase-number>
```

### Flow B: Requirement Change Discovered
```
/opsx:new <change-name>
/opsx:explore <change-name>
/opsx:continue <change-name>
/opsx:sync <change-name>

/gsd-discuss-phase <phase-number>
/gsd-plan-phase <phase-number>
/gsd-execute-phase <phase-number>
/gsd-verify-work <phase-number>

/opsx:archive <change-name>
```

Notes:
- Use `/opsx:sync` before GSD planning so plans follow updated specs.
- Archive only after implementation is verified.

## Spec Coordination
- Before modifying specs, read `.planning/foundation/STACK.md` and peers.
- Before planning phases, read relevant `openspec/specs/<domain>/` files.
- If a delta spec exists in `openspec/changes/`, use it as the active change set.

## Project Status
- For current state and next steps, read `ACTIVITY_LOG.md`.

## Cursor/Copilot Rules
- No `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` found.

## Git Hygiene
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- One logical change per commit.
- Feature branches: `feat/<short-description>`.
- Squash merge to main at milestone completion.
