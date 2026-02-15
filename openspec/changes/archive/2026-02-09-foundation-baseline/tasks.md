## 1. Monorepo Foundation

- [ ] 1.1 Initialize pnpm workspace with `pnpm-workspace.yaml` listing `apps/*` and `packages/*`
- [ ] 1.2 Create root `package.json` with Turborepo dev dependency and workspace scripts (dev, build, lint, test, type-check)
- [ ] 1.3 Create `turbo.json` with task pipeline configuration (build, lint, test, type-check, dev tasks with dependsOn)
- [ ] 1.4 Create `packages/config-ts/` with base.json, nextjs.json, react-native.json, library.json TypeScript configs
- [ ] 1.5 Create `packages/config-eslint/` with ESLint 9 flat config presets (base, next, react-native)
- [ ] 1.6 Create root `.prettierrc` and `.editorconfig` for consistent formatting
- [ ] 1.7 Create root `.gitignore` covering node_modules, .env, __pycache__, .venv, .turbo, dist
- [ ] 1.8 Create root `.env.example` with shared environment variables (DATABASE_URL, REDIS_URL, etc.)

## 2. Docker Infrastructure

- [ ] 2.1 Create `docker-compose.yml` with Postgres 16 + PGVector service, health check, named volume
- [ ] 2.2 Add Redis 7 service to Docker Compose with health check and persistence volume
- [ ] 2.3 Configure Docker Compose environment variables loading from `.env` with defaults
- [ ] 2.4 Verify `docker compose up` starts both services and they pass health checks

## 3. Django API Project

- [ ] 3.1 Create `apps/api/` directory with uv-managed Python project (`pyproject.toml` with Django, Ninja Extra, Allauth, psycopg[binary], Celery dependencies)
- [ ] 3.2 Create `config/` directory with `settings/base.py`, `settings/development.py`, `settings/production.py`, `urls.py`, `wsgi.py`, `asgi.py`
- [ ] 3.3 Create `apps/accounts/` Django app with custom User model (AbstractUser, email as USERNAME_FIELD, no username field)
- [ ] 3.4 Create `apps/core/` Django app with BaseModel mixin (created_at, updated_at, soft delete with deleted_at)
- [ ] 3.5 Create initial migrations: core 0001 (PGVector extension), accounts 0001 (custom User model)
- [ ] 3.6 Configure Django Ninja Extra API in `config/urls.py` with auto_discover_controllers at `/api/v1/`
- [ ] 3.7 Create `apps/core/controllers.py` with health check endpoint at `/api/v1/health` (checks DB connectivity)
- [ ] 3.8 Register User model in Django Admin (`apps/accounts/admin.py`)
- [ ] 3.9 Create `manage.py` and verify `python manage.py migrate` + `python manage.py runserver` work
- [ ] 3.10 Add `apps/api/package.json` (minimal, for Turborepo integration) with dev/lint/test scripts
- [ ] 3.11 Create `ruff.toml` with lint rules (E, F, I, N, W, UP, B, A, C4, SIM, TCH) and format config
- [ ] 3.12 Create `apps/api/.env.example` with Django-specific variables (SECRET_KEY, DATABASE_URL, DJANGO_SETTINGS_MODULE)

## 4. Authentication (Django Allauth Headless)

- [ ] 4.1 Add django-allauth to dependencies and configure in base.py (headless mode, email verification, account adapter)
- [ ] 4.2 Configure session cookie auth settings (SESSION_COOKIE_HTTPONLY, CSRF settings, SameSite=Lax)
- [ ] 4.3 Configure django-allauth-headless JWT settings for mobile auth (token lifetime, refresh rotation)
- [ ] 4.4 Add Allauth headless URLs to `config/urls.py`
- [ ] 4.5 Create `apps/accounts/controllers.py` with user profile endpoint (GET /api/v1/users/me, PATCH /api/v1/users/me)
- [ ] 4.6 Create `apps/accounts/schemas.py` with Pydantic schemas (UserOut, UserUpdateIn, LoginIn, SignupIn)
- [ ] 4.7 Create `apps/accounts/services.py` with user service (get_user, update_profile)
- [ ] 4.8 Configure CORS with django-cors-headers (CORS_ALLOWED_ORIGINS for localhost:3000 and :8081, CORS_ALLOW_CREDENTIALS=True)

## 5. OpenAPI Spec Export and Type Generation Pipeline

- [ ] 5.1 Create management command `export_openapi_schema` that outputs JSON to stdout
- [ ] 5.2 Add OpenAPI schema endpoint at `/api/v1/openapi.json` (no auth required)
- [ ] 5.3 Create `packages/api-client/` package with package.json (@repo/api-client, private, workspace dependencies)
- [ ] 5.4 Add `openapi-typescript` devDependency and `generate:types` script to api-client package
- [ ] 5.5 Export initial `openapi.json` from Django and commit to `packages/api-client/`
- [ ] 5.6 Run `openapi-typescript` to generate `src/types.d.ts` from openapi.json
- [ ] 5.7 Create `src/client.ts` with openapi-fetch typed client wrapper (WebAuthProvider and MobileAuthProvider)
- [ ] 5.8 Create `src/index.ts` barrel export

## 6. Shared Packages

- [ ] 6.1 Create `packages/validation/` with Zod schemas (loginSchema, signupSchema, profileUpdateSchema, passwordResetSchema)
- [ ] 6.2 Create `packages/validation/src/index.ts` barrel export with z.infer type exports
- [ ] 6.3 Create `packages/ui/` package with React Native Web primitives (Button, Text, Input, Card components)
- [ ] 6.4 Create `packages/ui/src/index.ts` barrel export (zero monorepo dependencies, only react/react-native peers)
- [ ] 6.5 Create `packages/business-logic/` with useAuth hook (login, logout, register, isAuthenticated, user state)
- [ ] 6.6 Create `packages/business-logic/` with useUser hook (fetch profile, update profile)
- [ ] 6.7 Create `packages/business-logic/src/index.ts` barrel export (depends on @repo/api-client and @repo/validation)

## 7. Next.js Web Application

- [ ] 7.1 Create `apps/web/` with Next.js 15 App Router, Tailwind CSS, and package.json (depends on @repo/api-client, @repo/validation, @repo/ui, @repo/business-logic)
- [ ] 7.2 Initialize Shadcn/ui with `npx shadcn@latest init` and add core components (Button, Input, Card, Form, Label, etc.)
- [ ] 7.3 Create root layout (`app/layout.tsx`) with ThemeProvider, font loading, metadata
- [ ] 7.4 Create auth layout (`app/(auth)/layout.tsx`) for login/signup/reset pages (centered card layout)
- [ ] 7.5 Create dashboard layout (`app/(dashboard)/layout.tsx`) with sidebar navigation and header
- [ ] 7.6 Create login page (`app/(auth)/login/page.tsx`) with form validation using @repo/validation loginSchema
- [ ] 7.7 Create signup page (`app/(auth)/signup/page.tsx`) with form validation using @repo/validation signupSchema
- [ ] 7.8 Create password reset page (`app/(auth)/reset-password/page.tsx`)
- [ ] 7.9 Create email verification page (`app/(auth)/verify-email/page.tsx`)
- [ ] 7.10 Create dashboard page (`app/(dashboard)/page.tsx`) — placeholder shell with welcome message
- [ ] 7.11 Create settings page (`app/(dashboard)/settings/page.tsx`) with profile update form using @repo/validation
- [ ] 7.12 Create Next.js middleware (`middleware.ts`) for auth guards (redirect unauthenticated to /login, authenticated from /login to /)
- [ ] 7.13 Implement dark mode toggle with system preference detection (ThemeProvider + localStorage)
- [ ] 7.14 Configure `next.config.ts` with API proxy rewrites and React Native Web webpack alias
- [ ] 7.15 Create `apps/web/.env.example` with NEXT_PUBLIC_API_URL

## 8. Expo Mobile Application

- [ ] 8.1 Create `apps/mobile/` with Expo managed workflow, Expo Router, and package.json (depends on @repo/api-client, @repo/validation, @repo/ui, @repo/business-logic)
- [ ] 8.2 Configure Metro bundler for monorepo (`metro.config.js` with watchFolders for packages/)
- [ ] 8.3 Create root layout (`app/_layout.tsx`) with AuthProvider and navigation container
- [ ] 8.4 Create auth group layout (`app/(auth)/_layout.tsx`) for login/signup screens
- [ ] 8.5 Create tabs group layout (`app/(tabs)/_layout.tsx`) with tab-based navigation (Home, Settings)
- [ ] 8.6 Create login screen (`app/(auth)/login.tsx`) with form validation using @repo/validation
- [ ] 8.7 Create signup screen (`app/(auth)/signup.tsx`) with form validation using @repo/validation
- [ ] 8.8 Create home screen (`app/(tabs)/index.tsx`) — placeholder dashboard
- [ ] 8.9 Create settings screen (`app/(tabs)/settings.tsx`) with profile update form
- [ ] 8.10 Implement JWT token management with expo-secure-store (store, retrieve, refresh, clear tokens)
- [ ] 8.11 Create AuthProvider context that checks token on app start and routes to auth/tabs
- [ ] 8.12 Create `apps/mobile/.env.example` with EXPO_PUBLIC_API_URL

## 9. AI Module (Optional)

- [ ] 9.1 Create `apps/api/apps/ai/` Django app with models.py, controllers.py, services.py, schemas.py, tasks.py
- [ ] 9.2 Create Document model with EmbeddingMixin (VectorField(1536), embedding_model, embedded_at, content_hash)
- [ ] 9.3 Create HNSW index migration on embedding field (vector_cosine_ops, m=16, ef_construction=64)
- [ ] 9.4 Create LangGraph RAG agent scaffold with state definition, retrieve node, generate node, compiled graph
- [ ] 9.5 Create Celery `generate_embedding` task with content hash check, retry logic (3 retries, 60s delay)
- [ ] 9.6 Create vector search controller at `/api/v1/ai/search` (POST, authenticated, returns ranked results by cosine distance)
- [ ] 9.7 Create AI document CRUD controller at `/api/v1/ai/documents` (CRUD endpoints, dispatch embedding task on create)
- [ ] 9.8 Conditionally add `apps.ai` to INSTALLED_APPS based on environment variable
- [ ] 9.9 Verify AI module removal: delete apps/ai/, remove from INSTALLED_APPS, confirm app starts without errors

## 10. Background Tasks (Celery)

- [ ] 10.1 Create `config/celery.py` with Redis broker configuration and task autodiscovery
- [ ] 10.2 Add Celery Beat schedule configuration in settings
- [ ] 10.3 Create `send_email_task` in core app (console backend in dev, SMTP in prod, retry logic)
- [ ] 10.4 Add optional Celery worker service to Docker Compose with `--profile with-worker`
- [ ] 10.5 Verify tasks queue in Redis when no worker is running, and process when worker starts

## 11. DevEx and CI/CD

- [ ] 11.1 Create `.pre-commit-config.yaml` with ruff hooks for Python and lint-staged for JS/TS
- [ ] 11.2 Add `prepare` script to root package.json to install pre-commit hooks on `pnpm install`
- [ ] 11.3 Create `apps/api/conftest.py` with pytest fixtures (db, api_client, authenticated_user)
- [ ] 11.4 Create example pytest tests (health check endpoint, user model, auth flow)
- [ ] 11.5 Create example vitest tests in `apps/web/` (component render, hook behavior)
- [ ] 11.6 Create `.detoxrc.js` config and example Detox test in `apps/mobile/`
- [ ] 11.7 Create `.github/workflows/ci.yml` with 3 parallel jobs (api, web, mobile) and type staleness gate
- [ ] 11.8 Create `apps/api/Dockerfile` (production multi-stage: uv install → gunicorn)
- [ ] 11.9 Create `apps/web/Dockerfile` (production multi-stage: pnpm install → next build → next start)
- [ ] 11.10 Configure mypy in `pyproject.toml` and verify `mypy .` passes
- [ ] 11.11 Verify `turbo test` runs pytest + vitest across all workspaces

## 12. CLI Scaffolder

- [ ] 12.1 Create CLI tool (Node.js or Python) with interactive prompts (project name, include AI module?)
- [ ] 12.2 Implement file copying engine (exclude .git, node_modules, .venv, cache dirs)
- [ ] 12.3 Implement package name replacement across all package.json, pyproject.toml, Docker Compose, and config files
- [ ] 12.4 Implement SECRET_KEY and secrets generation (cryptographically random)
- [ ] 12.5 Implement AI module exclusion logic (remove apps/ai, PGVector deps, AI routes, AI types)
- [ ] 12.6 Add post-generation validation (pnpm install, uv sync, turbo lint, turbo type-check)
- [ ] 12.7 Display success message with next steps (cd, docker compose up, pnpm dev)
