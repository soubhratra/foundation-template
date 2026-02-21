# Project Instructions

## This Product

<!-- REPLACE THIS SECTION per product. For the foundation template itself, leave as-is. -->

- Name: Foundation Template
- Type: Reusable monorepo template for all products
- Domain: N/A — this is infrastructure, not a product

---

## Identity

Solo technical entrepreneur building multiple SaaS products.
All code is written by AI agents (Claude Code, GSD subagents, Cursor/Antigravity agents)
under human direction. The human reviews specs, approves plans, and verifies output.

---

## Tech Stack (FINAL — Do Not Suggest Alternatives)

These decisions are permanent across all projects unless explicitly overridden
in a product-specific section below.

### Backend

- **Language:** Python 3.12+
- **API Framework:** Django Ninja Extra
- **ORM:** Django ORM
- **Database:** PostgreSQL 16+ (SQLite locally for quick tests only)
- **Vector Store:** PGVector extension
- **AI/Agents:** LangGraph for agent orchestration
- **Task Queue:** [your choice — e.g., Celery, Django-Q2, Huey]

### Frontend — Web

- **Framework:** Next.js 15+ (App Router only — no Pages Router)
- **UI Library:** Shadcn/ui (never install competing component libraries)
- **Styling:** Tailwind CSS 4+
- **State Management:** React Query (TanStack Query) for server state, Zustand for client state
- **Forms:** React Hook Form + Zod validation

### Frontend — Mobile

- **Framework:** React Native with Expo SDK 53+ (managed workflow only)
- **Navigation:** Expo Router
- **UI:** Shared primitives where possible, platform-native where needed

### Shared Infrastructure

- **Monorepo:** Turborepo for JS/TS task orchestration
- **Package Manager:** pnpm (JS/TS), uv or pip (Python)
- **Auth:** [YOUR AUTH SOLUTION — e.g., Supabase Auth, Clerk, Django Allauth]
- **Local Dev:** Docker Compose (Postgres + PGVector + Redis)
- **CI/CD:** [YOUR CI — e.g., GitHub Actions]
- **Hosting:** [YOUR HOSTING — e.g., Vercel (web), Railway (API), EAS (mobile)]

### Testing

- **Backend:** pytest + pytest-django + factory_boy
- **Frontend Web:** Vitest + React Testing Library
- **Mobile:** Jest + React Native Testing Library, Detox for E2E
- **API Integration:** pytest with httpx async client

---

## Architecture Rules

### Monorepo Structure

```
apps/
├── landing/          # Static marketing site (Next.js)
├── web/              # Main web application (Next.js App Router)
├── mobile/           # Mobile application (React Native Expo)
└── api/              # Backend API (Django Ninja Extra)
packages/
├── shared-types/     # TypeScript types generated from Django schemas
├── ui/               # Shared UI components (optional)
└── config/           # Shared ESLint, Tailwind, TypeScript configs
```

### Boundaries

- `apps/api/` is the **single backend**. All other apps consume it via REST.
- `apps/web/` and `apps/mobile/` **share types** from `packages/shared-types/`.
- `apps/landing/` is fully static — no API calls, no auth.
- Cross-app code lives in `packages/`. Apps never import from each other.

### API Contracts

- Every Django Ninja Extra endpoint MUST have typed request/response schemas.
- Schemas are defined in `apps/api/[domain]/schemas.py` using Ninja schemas or Pydantic.
- TypeScript types in `packages/shared-types/` are generated from these schemas.
- After adding or modifying API endpoints, **always regenerate** `packages/shared-types/`.

### Database

- All database access goes through Django ORM. No raw SQL unless justified in a comment.
- Migrations are created via `python manage.py makemigrations` — never hand-written.
- PGVector collections use cosine similarity unless the spec says otherwise.
- Vector indexes use HNSW (not IVFFlat) for production workloads.

### AI / LangGraph

- LangGraph graphs are defined in `apps/api/agents/`.
- Every graph has an explicit state schema (TypedDict or Pydantic model).
- Tools are defined as standalone functions, not inline lambdas.
- Graph persistence uses Postgres (via LangGraph's checkpoint saver).
- Read `openspec/specs/backend/ai.md` before modifying any agent.

---

## Coding Conventions

### Python (apps/api/)

- Use `django-ninja-extra` routers and `APIController` classes.
- Type ALL function signatures. No `Any` unless truly unavoidable.
- File organization per domain:
  - `apps/api/[domain]/models.py` — Django models
  - `apps/api/[domain]/schemas.py` — Request/response schemas
  - `apps/api/[domain]/api.py` — API controller and endpoints
  - `apps/api/[domain]/services.py` — Business logic (keep endpoints thin)
  - `apps/api/[domain]/selectors.py` — Complex queries
- Tests: `apps/api/tests/[domain]/test_*.py`
- Use `ruff` for linting and formatting.
- Imports: stdlib → third-party → django → project (isort compatible).

### TypeScript (apps/web/, apps/mobile/, packages/)

- **Server components by default** in Next.js. Add `"use client"` only when needed.
- Shadcn/ui for ALL UI primitives — do not install alternative component libraries.
- React Query for server state. Zustand for client-only state. No Redux.
- Shared types imported from `@repo/shared-types` — **never duplicate type definitions**.
- File naming: `kebab-case` for files, `PascalCase` for components.
- Use `function` declarations for components, not arrow functions assigned to `const`.
- Zod schemas for form validation (mirrors backend Pydantic schemas where possible).

### React Native (apps/mobile/)

- Expo **managed workflow** only. No bare workflow unless explicitly approved.
- Share business logic with web via `packages/` where feasible.
- Expo Router for navigation (file-based routing).
- Platform-specific files: `Component.ios.tsx` / `Component.android.tsx` when needed.

### Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- One logical change per commit.
- Feature branches: `feat/[short-description]`
- Squash merge to main at milestone completion.

---

## TOOL COORDINATION RULES

These rules ensure OpenSpec and GSD work together through Claude Code.
Both tools are collections of markdown files. Neither reads the other automatically.
**Claude Code is the bridge — these rules tell it when and what to read.**

### The Information Flow

```
GSD research (.planning/)  ──→  OpenSpec specs (openspec/specs/)
                                       │
                                       ▼
                              GSD execution plans (.planning/phases/)
                                       │
                                       ▼
                                 Shipped code (apps/, packages/)
                                       │
                                       ▼
                              OpenSpec spec updates (loop back)
```

### Rule 1: When Creating or Modifying OpenSpec Specs

Before generating or modifying ANY OpenSpec specification, ALWAYS read:

1. `.planning/foundation/STACK.md` — Approved tech stack decisions
2. `.planning/foundation/ARCHITECTURE.md` — Approved architecture patterns
3. `.planning/foundation/CONVENTIONS.md` — Approved coding standards
4. `.planning/foundation/TESTING.md` — Approved test strategy
5. `.planning/research/*` — Latest research findings (if directory exists)
6. `.planning/codebase/*` — Codebase analysis (if directory exists, brownfield projects)

These documents contain human-reviewed decisions. Generated specs MUST be
consistent with them. If a conflict exists, flag it — do not silently override.

### Rule 2: When Planning GSD Phases

Before running `/gsd:plan-phase`, `/gsd:discuss-phase`, or `/gsd:execute-plan`, ALWAYS read:

1. `openspec/specs/foundation/*` — Tech stack, architecture, conventions
2. `openspec/specs/` in the relevant domain — e.g., `openspec/specs/api/` for backend phases
3. `openspec/changes/[active-change]/specs/*` — Delta requirements for the current feature (if a change proposal is active)

These define WHAT to build. GSD plans define HOW to build it.

### Rule 3: When Running /gsd:new-project or /gsd:new-milestone

- Stack decisions are FINALIZED in `openspec/specs/foundation/stack.md`.
- **Do NOT research stack alternatives** (Python, Django, Next.js, etc. are settled).
- Focus research on: product domain, competitive features, UX patterns,
  and product-specific technical challenges only.

### Rule 4: When Running /opsx:new [change-name]

- Read `.planning/codebase/*` to understand the current system state.
- Read `openspec/specs/` to understand existing requirements.
- In proposals, reference specific app paths (`apps/web/`, `apps/api/`, etc.).
- Cross-app changes must list impacts per app explicitly.

### Rule 5: After Completing a GSD Milestone (Sync to OpenSpec)

**When:** After completing all phases in a GSD milestone (or after a major phase).

**What:** Sync implementation decisions from `.planning/STATE.md` to OpenSpec specs.

**How (REQUIRED WORKFLOW):**

1. **Analyze decisions:**

   ```bash
   # Review accumulated decisions
   Read .planning/STATE.md (Decisions section)
   Read .planning/phases/*/CONTEXT.md files
   ```

2. **Create OpenSpec change proposal:**

   ```bash
   /opsx:new gsd-milestone-N-sync
   # Where N is the milestone number (e.g., gsd-milestone-1-sync)
   ```

3. **Create delta specs in changes directory:**

   ```
   openspec/changes/[change-id]/specs/foundation/
     ├── stack.md (document only CHANGES, not entire spec)
     ├── auth.md (document only CHANGES)
     ├── ... (other affected specs)
     └── NEW-SPEC.md (if new spec needed)
   ```

4. **Document what changed:**
   - In each delta spec, list decisions being added
   - Mark with phase number: `(Decision: Phase NN)`
   - Include rationale for non-obvious choices

5. **Archive the change:**
   ```bash
   /opsx:archive gsd-milestone-N-sync
   # This merges delta specs → main specs
   ```

**Why use change proposals (not direct edits):**

- ✅ Clear audit trail of what changed and when
- ✅ Delta specs show ONLY new decisions (easier to review)
- ✅ Archive creates historical record
- ✅ Separation of "proposed sync" from "current truth"

**What to sync:**

- Tool version decisions → `stack.md`
- Auth/security patterns → `auth.md`
- API contract patterns → `api-contracts.md`
- Architecture decisions → `architecture.md`
- Domain-specific patterns → relevant domain specs
- New capabilities → create new spec files

**Exception (Template Repository Only):**
When establishing the INITIAL baseline specs for the template itself
(not a project using the template), you may write directly to
`openspec/specs/foundation/`. After that, use change proposals.

### Rule 6: Monorepo Context Scoping

When working on a specific app, also read that app's local CLAUDE.md:

- `apps/web/CLAUDE.md` — Points to relevant specs for web work
- `apps/api/CLAUDE.md` — Points to relevant specs for backend work
- `apps/mobile/CLAUDE.md` — Points to relevant specs for mobile work

---

## GSD Workflow Rules

- Use GSD for all features: `discuss → plan → execute → verify`
- Plans are stored in `.planning/phases/`
- Subagents commit their own work and create SUMMARY.md
- NEVER write code without a plan for changes spanning more than 2 files
- For quick fixes: `/gsd:quick "description"`
- Each plan has a maximum of 3 tasks — keep plans atomic
- Each task runs in a fresh subagent with clean 200k token context

## OpenSpec Rules

### When to Use Change Proposals vs Direct Edits

**Use Change Proposal Flow (`/opsx:new → /opsx:archive`):**

- ✅ Syncing GSD decisions to existing specs (Rule 5)
- ✅ Modifying API contracts, auth flows, or data models
- ✅ Adding new patterns to existing specs
- ✅ Any update to already-established specs

**Use Direct Edits (No Change Proposal):**

- ✅ Establishing INITIAL baseline specs (first-time only)
- ✅ Capturing existing codebase as specs (brownfield projects)
- ✅ Typo fixes or clarifications that don't change meaning

### Foundation Specs Inheritance

- Foundation specs (`openspec/specs/foundation/`) are inherited from the template.
- In projects using this template, foundation specs should rarely change.
- If a project needs to deviate from foundation specs, create project-specific
  specs in `openspec/specs/[domain]/` instead of modifying foundation specs.

### Self-Contained Specs Rule

Foundation specs (`openspec/specs/`) are copied verbatim to every new product scaffolded using this template. The `.planning/` directory is **not** copied — it is explicitly excluded by the CLI scaffolder.

**Therefore: specs must be fully self-contained.** Every spec must include:

- **What** the decision is (the rule or pattern)
- **Why** it was chosen (rationale, tradeoffs, constraints)
- **What alternatives were rejected** and why they were rejected

Never reference `.planning/` files in spec documents as a source of rationale. Any rationale worth preserving must live in the spec itself, inline with the decision it explains.

This rule applies equally to:

- Foundation specs (`openspec/specs/foundation/`) — inherited by all products
- Product-specific specs (`openspec/specs/[domain]/`) — created per product

**When writing or updating any spec**, ask: _"If a developer on a new product repo read only this spec, would they understand the decision and could they make consistent future decisions without external context?"_ If no, add the missing rationale inline.

### Workflow Commands

**Create a change:**

```bash
/opsx:new [change-name]        # Start a change proposal
/opsx:ff [change-name]         # Fast-forward through artifact creation
```

**Implement a change:**

```bash
/opsx:apply [change-name]      # Implement tasks from change
```

**Finalize a change:**

```bash
/opsx:verify [change-name]     # Verify implementation matches artifacts
/opsx:archive [change-name]    # Merge delta specs → main specs, archive
```

**Sync after GSD milestone (Rule 5):**

```bash
/opsx:new gsd-milestone-N-sync           # Create sync proposal
# ... create delta specs in changes/[id]/specs/
/opsx:archive gsd-milestone-N-sync      # Merge to main specs
```

---

## File Quick Reference

When you need context, read these files:

| Need to understand...        | Read                                             |
| ---------------------------- | ------------------------------------------------ |
| Tech stack decisions         | `openspec/specs/foundation/stack.md`             |
| Architecture patterns        | `openspec/specs/foundation/architecture.md`      |
| Coding conventions           | `openspec/specs/foundation/conventions.md`       |
| API contract patterns        | `openspec/specs/foundation/api-contracts.md`     |
| Current product requirements | `openspec/specs/product/`                        |
| What's being built right now | `.planning/ROADMAP.md` + `.planning/STATE.md`    |
| Current codebase state       | `.planning/codebase/` (if brownfield)            |
| GSD research findings        | `.planning/research/` or `.planning/foundation/` |
