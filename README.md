# Foundation Template

> **Zero to Production-Ready SaaS in Under 5 Minutes**

A complete full-stack monorepo starter for building modern SaaS products. Includes Django Ninja Extra backend, Next.js 15 web app, React Native Expo mobile app, shared type-safe packages, optional AI module with PGVector + LangGraph, and production-ready DevEx with CI/CD.

## 🚀 Quick Start

### Using the CLI Scaffolder (Recommended)

**Create a new project from this template:**

```bash
# 1. Clone the foundation-template repository (one-time setup)
git clone https://github.com/soubhratra/foundation-template.git
cd foundation-template

# 2. Install dependencies (one-time setup)
pnpm install

# 3. Build the CLI scaffolder (one-time setup)
cd packages/create-foundation-app
pnpm build

# 4. Run the CLI to generate your project
node bin/cli.js
```

**The CLI will prompt you for:**

1. **Project name** (e.g., `my-saas-app`)
2. **Features to include** (web/mobile/landing/AI - all checked by default)
3. **Output directory** (e.g., `../my-saas-app` - **outside this repo**)

**The CLI will then:**

- ✅ Copy template files to your specified location
- ✅ Transform placeholders (foundation-template → my-saas-app)
- ✅ Generate unique secrets (Django SECRET_KEY, database passwords)
- ✅ Remove excluded platforms (if any unchecked)
- ✅ Run quality gates (lint + type-check + tests)
- ✅ Deliver a **standalone project** ready to run

**After generation:**

```bash
# Navigate to your NEW project (outside foundation-template)
cd ../my-saas-app  # or wherever you specified

# Your new project is ready! Start development:
docker compose up -d
pnpm dev
```

> **Note:** The generated project is completely independent. You can safely delete the `foundation-template` directory after scaffolding.

**📌 Using on a Different Computer:**

On any new machine, simply clone `foundation-template`, run the CLI steps above, and generate your project. The template is a **development tool**, not part of your generated project.

**📦 Future: npm Package (Coming Soon):**

Once published to npm, you'll be able to run this from anywhere without cloning:

```bash
pnpm create foundation-app
# or
npx create-foundation-app
```

This will work the same way, but without requiring the clone step.

---

### Manual Setup (Alternative)

Clone and run this template directly for development/testing:

```bash
# 1. Clone the repository
git clone https://github.com/soubhratra/foundation-template.git
cd foundation-template

# 2. Install dependencies
pnpm install

# 3. Start services
docker compose up -d          # Postgres + PGVector + Redis

# 4. Run migrations
cd apps/api
uv sync
uv run python manage.py migrate
cd ../..

# 5. Start all apps
pnpm dev                      # Django + Next.js + Expo (hot reload)
```

Open:

- 🌐 Web app: http://localhost:3000
- 📱 Mobile app: Expo Go on your device (scan QR code)
- 🔌 API docs: http://localhost:8000/api/docs
- 📊 API admin: http://localhost:8000/admin

## 📦 What's Included

### Apps

| App        | Description                | Tech Stack                                        | Port |
| ---------- | -------------------------- | ------------------------------------------------- | ---- |
| **api**    | Django Ninja Extra backend | Python 3.12, Django 5.1, Ninja Extra, Postgres 16 | 8000 |
| **web**    | Next.js web application    | Next.js 15, React 19, Shadcn/ui, Tailwind CSS     | 3000 |
| **mobile** | Expo mobile application    | Expo SDK 53, React Native, Expo Router            | -    |

### Packages

| Package                   | Description                                                    |
| ------------------------- | -------------------------------------------------------------- |
| **api-client**            | Type-safe API client generated from OpenAPI spec               |
| **validation**            | Shared Zod schemas for forms and data validation               |
| **ui**                    | Shared React Native Web primitives (Button, Text, Input, Card) |
| **business-logic**        | Shared auth hooks (useAuth, useUser) and utilities             |
| **config-eslint**         | Shared ESLint configuration                                    |
| **config-ts**             | Shared TypeScript configuration                                |
| **create-foundation-app** | CLI scaffolder for generating new projects                     |

### Features

- ✅ **Full Authentication Flow** - Signup, login, logout, password reset, email verification
- ✅ **Dual Auth Strategy** - Session cookies (web) + JWT tokens (mobile)
- ✅ **Type-Safe API Client** - OpenAPI → TypeScript code generation
- ✅ **Shared UI Primitives** - React Native Web components work on web + mobile
- ✅ **Dark Mode** - System preference detection + manual toggle
- ✅ **AI Module (Optional)** - PGVector + LangGraph + Celery for embeddings and agents
- ✅ **Production Ready** - Docker, CI/CD, pre-commit hooks, comprehensive tests
- ✅ **DevEx Tooling** - Turborepo, hot reload, type checking, linting

## 🏗️ Architecture

### Monorepo Structure

```
foundation-template/
├── apps/
│   ├── api/              # Django Ninja Extra backend
│   │   ├── apps/
│   │   │   ├── accounts/ # User management + auth
│   │   │   └── ai/       # PGVector + LangGraph (optional)
│   │   ├── config/       # Django settings
│   │   └── pyproject.toml
│   ├── web/              # Next.js 15 App Router
│   │   ├── app/          # Routes (auth, dashboard, profile, settings)
│   │   └── components/   # Shadcn/ui components
│   └── mobile/           # Expo React Native
│       ├── app/          # Expo Router (auth stack, tab navigator)
│       └── components/   # Shared UI components
├── packages/
│   ├── api-client/       # Generated from apps/api/openapi.json
│   ├── validation/       # Zod schemas (auth, profile)
│   ├── ui/               # Button, Text, Input, Card primitives
│   ├── business-logic/   # useAuth, useUser, shared utilities
│   └── create-foundation-app/  # CLI scaffolder
├── .planning/            # GSD project planning artifacts
├── openspec/             # Technical specifications
└── docker-compose.yml    # Postgres + PGVector + Redis
```

### Tech Stack

See **[openspec/specs/foundation/stack.md](openspec/specs/foundation/stack.md)** for the complete, locked-in tech stack.

**Backend:**

- Django 5.1 + Django Ninja Extra + Django Allauth (headless)
- PostgreSQL 16 + PGVector extension
- Celery + Redis (for AI module background tasks)

**Frontend Web:**

- Next.js 15 (App Router) + React 19
- Shadcn/ui + Tailwind CSS 4
- React Query + Zustand
- React Hook Form + Zod

**Frontend Mobile:**

- React Native (Expo SDK 53)
- Expo Router
- Expo SecureStore (JWT persistence)

**Shared:**

- Turborepo (task orchestration)
- pnpm (package manager)
- TypeScript + ESLint + Prettier
- GitHub Actions (CI/CD)

### Data Flow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Web App   │      │  Mobile App │      │  API Docs   │
│  (Next.js)  │      │   (Expo)    │      │  (Swagger)  │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       │  Session Cookies   │  JWT Tokens        │  Manual
       └────────────────────┴────────────────────┘
                            │
                   ┌────────▼────────┐
                   │   Django API    │
                   │  (Ninja Extra)  │
                   └────────┬────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼──────┐           ┌───────▼────────┐
       │  PostgreSQL │           │  Redis Cache   │
       │  (PGVector) │           │  (Celery)      │
       └─────────────┘           └────────────────┘
```

## 📚 Documentation

### Project Documentation

| File                                   | Description                                            |
| -------------------------------------- | ------------------------------------------------------ |
| **[CLAUDE.md](CLAUDE.md)**             | Instructions for AI agents (Claude Code, Cursor, etc.) |
| **[AGENTS.md](AGENTS.md)**             | Agent coordination rules, workflow integration         |
| **[ACTIVITY_LOG.md](ACTIVITY_LOG.md)** | Session activity summaries                             |
| **[DEV_LOGS.md](DEV_LOGS.md)**         | Development notes and decisions                        |

### Planning Artifacts

Located in **`.planning/`** (GSD workflow outputs):

| File                                                       | Description                                           |
| ---------------------------------------------------------- | ----------------------------------------------------- |
| **[.planning/PROJECT.md](.planning/PROJECT.md)**           | Project charter, goals, and key decisions             |
| **[.planning/ROADMAP.md](.planning/ROADMAP.md)**           | 8-phase development roadmap with success criteria     |
| **[.planning/STATE.md](.planning/STATE.md)**               | Current progress, metrics, and accumulated context    |
| **[.planning/REQUIREMENTS.md](.planning/REQUIREMENTS.md)** | 71 requirements across 9 categories with traceability |
| **`.planning/phases/NN-*/`**                               | Phase plans, summaries, context, and verification     |

### Technical Specifications

Located in **`openspec/specs/foundation/`**:

| Spec                                                               | Description                                                 |
| ------------------------------------------------------------------ | ----------------------------------------------------------- |
| **[stack.md](openspec/specs/foundation/stack.md)**                 | Locked tech stack decisions (Python, Django, Next.js, Expo) |
| **[architecture.md](openspec/specs/foundation/architecture.md)**   | Monorepo structure, boundaries, patterns                    |
| **[conventions.md](openspec/specs/foundation/conventions.md)**     | Code style, file organization, naming                       |
| **[auth.md](openspec/specs/foundation/auth.md)**                   | Dual auth strategy (session + JWT), flows                   |
| **[api-contracts.md](openspec/specs/foundation/api-contracts.md)** | OpenAPI schema patterns, type generation                    |
| **[data-models.md](openspec/specs/foundation/data-models.md)**     | Django models, migrations, custom user                      |
| **[deployment.md](openspec/specs/foundation/deployment.md)**       | Docker, CI/CD, production configs                           |
| **[ai-stack.md](openspec/specs/foundation/ai-stack.md)**           | PGVector, LangGraph, Celery patterns                        |

## 🛠️ Development

### Prerequisites

- **Node.js** 20+ and **pnpm** 9+
- **Python** 3.12+ and **uv** (or pip)
- **Docker** and **Docker Compose**
- **PostgreSQL** 16+ (via Docker or local)

### Environment Setup

1. **Copy environment files:**

   ```bash
   cp apps/api/.env.example apps/api/.env
   cp apps/web/.env.example apps/web/.env
   cp apps/mobile/.env.example apps/mobile/.env
   ```

2. **Configure secrets:**
   - Generate unique `SECRET_KEY` for Django (50 chars random)
   - Set database credentials (or use defaults from docker-compose.yml)
   - Configure SMTP for email verification (optional for dev)

3. **Start services:**

   ```bash
   docker compose up -d
   ```

4. **Run migrations:**

   ```bash
   cd apps/api
   uv sync
   uv run python manage.py migrate
   uv run python manage.py createsuperuser  # Optional
   ```

5. **Generate TypeScript types:**
   ```bash
   pnpm generate:types
   ```

### Common Commands

```bash
# Development
pnpm dev                    # Start all apps (hot reload)
pnpm dev --filter=@repo/web # Start only web app
pnpm dev --filter=@repo/api # Start only API

# Type Generation
pnpm generate:types         # Export OpenAPI + generate TS types

# Quality Checks
pnpm lint                   # Lint all packages
pnpm type-check             # Type-check all packages
pnpm test                   # Run all tests

# Database
cd apps/api
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Mobile
cd apps/mobile
pnpm start                  # Start Expo dev server
pnpm ios                    # Run on iOS simulator
pnpm android                # Run on Android emulator
```

### Pre-commit Hooks

Automatically runs on every commit:

- **Python:** ruff (lint + format)
- **JS/TS:** eslint + prettier
- **Files:** trailing whitespace, end-of-file, YAML syntax

Violations block the commit. Fix issues and re-commit.

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):

- Parallel jobs: `api`, `web`, `mobile`
- Each job: install deps → lint → type-check → test
- Type staleness gate: fails if generated types don't match OpenAPI spec
- Runs on every push and PR

## 🧪 Testing

### Backend (pytest)

```bash
cd apps/api
uv run pytest                      # All tests
uv run pytest apps/accounts/tests  # Specific app
uv run pytest -v --cov             # With coverage
```

### Web (Vitest)

```bash
cd apps/web
pnpm test              # All tests
pnpm test:ui           # UI mode (interactive)
pnpm test:coverage     # With coverage
```

### Mobile (Detox)

```bash
cd apps/mobile
pnpm test:e2e          # E2E tests (iOS simulator)
pnpm test:e2e:build    # Build test app
```

## 🤖 AI Module (Optional)

The AI module provides vector search and LangGraph agent scaffolding.

**Features:**

- PGVector extension for embeddings
- Document chunking and embedding pipeline (Celery)
- LangGraph Q&A agent with tool use
- Vector search API endpoints

**Enable/Disable:**

- Included by default when using the CLI scaffolder
- Can be excluded during generation (uncheck "AI Module")
- Can be removed manually using the removal script:
  ```bash
  ./apps/api/apps/ai/scripts/remove_ai_module.sh
  ```

See **[openspec/specs/foundation/ai-stack.md](openspec/specs/foundation/ai-stack.md)** for details.

## 🚢 Deployment

### Production Docker Images

```bash
# Build API
docker build -f apps/api/Dockerfile.prod -t foundation-api:latest .

# Build Web
docker build -f apps/web/Dockerfile.prod -t foundation-web:latest .
```

### Deployment Targets

- **API:** Railway, Render, Fly.io, AWS ECS
- **Web:** Vercel, Netlify, Cloudflare Pages
- **Mobile:** Expo EAS Build → App Store + Google Play

See **[openspec/specs/foundation/deployment.md](openspec/specs/foundation/deployment.md)** for platform-specific guides.

## 📖 Workflows

### GSD Workflow (Get Shit Done)

This project uses the GSD workflow for systematic development:

1. **Discuss Phase** (`/gsd:discuss-phase N`) - Gather context and make decisions
2. **Plan Phase** (`/gsd:plan-phase N`) - Create executable plans
3. **Execute Phase** (`/gsd:execute-phase N`) - Run plans with subagents
4. **Verify Phase** (`/gsd:verify-work N`) - Validate goal achievement

All planning artifacts are in **`.planning/`**. See **[AGENTS.md](AGENTS.md)** for coordination rules.

### OpenSpec Workflow

For changes to specs or architecture:

1. **Create Change** (`/opsx:new [name]`) - Propose modification
2. **Fast-Forward** (`/opsx:ff [name]`) - Generate all artifacts
3. **Apply** (`/opsx:apply [name]`) - Implement changes
4. **Archive** (`/opsx:archive [name]`) - Merge and clean up

All specs are in **`openspec/specs/`**.

## 📊 Project Status

**Current State:** ✅ **Production Ready**

All 8 phases complete:

- ✅ Phase 1: Monorepo Foundation (Turborepo + Docker Compose)
- ✅ Phase 2: API Core + Auth Backend (Django Ninja Extra + Allauth)
- ✅ Phase 3: Shared Packages + Type Generation (API client + validation)
- ✅ Phase 4: Web Application (Next.js + complete auth flow)
- ✅ Phase 5: Mobile Application (Expo + JWT auth)
- ✅ Phase 6: AI Module (PGVector + LangGraph)
- ✅ Phase 7: DevEx + CI/CD (Pre-commit + GitHub Actions + Docker)
- ✅ Phase 8: CLI Scaffolder (Interactive project generator)

See **[.planning/ROADMAP.md](.planning/ROADMAP.md)** for detailed phase breakdown and **[.planning/STATE.md](.planning/STATE.md)** for metrics.

## 🤝 Contributing

This is a template repository. To use it:

1. **Generate a new project:** Run the CLI scaffolder
2. **Customize:** Modify generated project for your product
3. **Build:** Add your business logic and features

**Improvements to the template itself:**

- Fork this repo
- Make changes following the GSD workflow
- Open a PR with clear description

## 📝 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **Repository:** https://github.com/soubhratra/foundation-template
- **Issues:** https://github.com/soubhratra/foundation-template/issues
- **Discussions:** https://github.com/soubhratra/foundation-template/discussions

---

**Built with [GSD](https://github.com/cyanheads/get-shit-done) · [OpenSpec](https://github.com/cyanheads/openspec) · [Claude Code](https://claude.ai/claude-code)**
