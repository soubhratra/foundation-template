# Pitfalls Research

**Domain:** Full-stack SaaS foundation template (Django Ninja Extra + Next.js 15 + Expo + Turborepo)
**Researched:** 2026-02-08
**Confidence:** MEDIUM (WebSearch/WebFetch unavailable; findings based on training data verified against known documentation patterns. All items flagged where validation is recommended.)

---

## Critical Pitfalls

Mistakes that cause rewrites, architectural dead-ends, or multi-day debugging sessions.

### Pitfall 1: Turborepo Cannot Orchestrate Python -- Treating It Like a JS Workspace

**What goes wrong:**
Turborepo is built around npm/pnpm workspaces. Developers try to put the Django app as a Turborepo "package" with a `package.json` that wraps Python commands (`"dev": "python manage.py runserver"`). This breaks Turborepo's dependency graph because Python packages do not declare dependencies through `package.json`. Turborepo cannot hash Python files for cache invalidation, cannot resolve Python import graphs, and cannot determine when the Django app's outputs are stale. Cache hits become unreliable -- either always stale (wasting CI time) or incorrectly cached (serving old builds).

**Why it happens:**
Turborepo docs focus entirely on JS/TS. Developers assume "just add a package.json wrapper" is sufficient. It works for `turbo run dev` but silently breaks caching and dependency tracking.

**How to avoid:**
- Keep Django as a **sibling directory** (`apps/api/`) with its own `pyproject.toml` managed by `uv`, NOT as a Turborepo workspace package
- Create a thin `package.json` in `apps/api/` ONLY for Turborepo task registration (scripts that delegate to Python tooling), with explicit `inputs` globs in `turbo.json` that cover `**/*.py`, `requirements*.txt`, `pyproject.toml`
- In `turbo.json`, configure the Django app's tasks with explicit `inputs` and `outputs` rather than relying on Turborepo's automatic file hashing:
  ```json
  {
    "tasks": {
      "api#lint": {
        "inputs": ["apps/api/**/*.py", "apps/api/pyproject.toml"],
        "outputs": [],
        "cache": true
      },
      "api#test": {
        "inputs": ["apps/api/**/*.py", "apps/api/pyproject.toml"],
        "outputs": ["apps/api/coverage/**"],
        "cache": true
      }
    }
  }
  ```
- Use Turborepo ONLY for orchestration (parallel `dev`, CI task graph). Use `uv` for Python dependency resolution independently
- Do NOT put Python virtualenvs inside Turborepo-tracked directories

**Warning signs:**
- CI caches never hit for Python tasks despite no changes
- Turborepo reports "cache MISS" for Django tasks every run
- `turbo run test` re-runs Python tests that haven't changed
- Developers manually clearing Turborepo cache "because it gets confused"

**Phase to address:** Phase 1 (Monorepo Foundation). Getting this wrong means reworking the entire CI pipeline later.

**Recovery cost:** MEDIUM -- requires restructuring `turbo.json` task configuration and CI, but not code changes.

**Confidence:** MEDIUM -- based on Turborepo documentation patterns and community reports. Verify `inputs`/`outputs` syntax against current Turborepo docs.

---

### Pitfall 2: Django Allauth Auth Misconfiguration for Cross-Platform SPA + Mobile

**What goes wrong:**
Django Allauth has a "headless" mode designed for SPA/API usage, but developers make three interrelated mistakes:

1. **Mixing session and token auth without a strategy.** Next.js (same-origin or subdomain) works best with session cookies. Expo (mobile) needs token auth (JWT or session token in headers). Developers either force tokens everywhere (losing CSRF protection on web) or force sessions everywhere (breaking mobile).

2. **CSRF token mishandling.** Django's CSRF protection uses cookies. When Next.js is on a different origin than Django, the CSRF cookie isn't sent. Developers disable CSRF entirely ("it works now!") instead of properly configuring trusted origins and ensuring the CSRF token is forwarded.

3. **Cookie domain misconfiguration.** For session auth to work across `api.example.com` and `app.example.com`, cookies need `Domain=.example.com`, `SameSite=Lax` (not `Strict`), and `Secure=True`. In development with `localhost:3000` (Next.js) and `localhost:8000` (Django), cookies don't share because they're different ports. Developers "fix" this with `SameSite=None` + `Secure=False` in dev, then forget to change it in production.

**Why it happens:**
Django Allauth's headless mode is relatively new. Documentation assumes familiarity with Django's auth internals. The three-platform auth requirement (Next.js SSR, Next.js client, Expo) means three different auth flows that must coexist.

**How to avoid:**
- **Dual auth strategy:** Use session cookies for Next.js (same-origin proxy or subdomain) and token-based auth (via Allauth headless tokens) for Expo mobile
- **Next.js API proxy:** Route `/api/auth/*` through Next.js rewrites to Django. This makes auth same-origin, eliminating CORS/CSRF issues for web:
  ```javascript
  // next.config.js
  async rewrites() {
    return [
      { source: '/api/:path*', destination: 'http://django:8000/api/:path*' }
    ]
  }
  ```
- **Django Allauth headless config:**
  ```python
  HEADLESS_ONLY = True  # Disable Django's HTML auth views
  HEADLESS_FRONTEND_URLS = {
      "account_confirm_email": "https://app.example.com/auth/verify-email/{key}",
      "account_reset_password_from_key": "https://app.example.com/auth/reset-password/{key}",
  }
  ```
- **Separate auth clients:** Build the shared API client package with a `WebAuthProvider` (cookie-based) and `MobileAuthProvider` (token-based) that handle transport differences transparently
- Configure `CSRF_TRUSTED_ORIGINS` explicitly for both dev and prod
- Use a `.env`-driven `SESSION_COOKIE_DOMAIN` that changes between dev (not set / localhost) and prod (`.example.com`)

**Warning signs:**
- 403 Forbidden errors on POST requests from Next.js (CSRF failure)
- Auth works on web but not mobile, or vice versa
- `CSRF_EXEMPT` decorators scattered across views
- `SameSite=None` in production configuration
- Login works in dev but breaks in staging/production

**Phase to address:** Phase 2 (Auth Foundation). This is the single most complex integration in the entire template.

**Recovery cost:** HIGH -- auth touches every API endpoint, every frontend page, every mobile screen. Getting it wrong means rewriting auth providers, API client interceptors, and potentially cookie/session configuration across environments.

**Confidence:** MEDIUM -- Django Allauth headless mode specifics should be validated against current docs (especially `HEADLESS_FRONTEND_URLS` config keys).

---

### Pitfall 3: React Native Web Component Sharing -- Overestimating What Works

**What goes wrong:**
Developers assume React Native Web means "write once, run on web and mobile." In reality, about 60-70% of RN core components render on web, but:

1. **Navigation is completely different.** React Navigation (mobile) vs Next.js App Router (web) are incompatible paradigms. You cannot share navigation logic.

2. **Platform-specific APIs don't exist on web.** `Animated`, `PanResponder`, gesture handlers, `StatusBar`, `SafeAreaView`, camera, biometrics -- none of these have web equivalents through RN Web. Developers build a "shared" component using these APIs, then discover it crashes on web.

3. **Styling edge cases.** RN Web translates `StyleSheet` to CSS, but not perfectly. `position: 'absolute'` behaves differently. `overflow: 'hidden'` doesn't clip the same way. Shadow properties map to `box-shadow` imperfectly. `zIndex` stacking contexts differ.

4. **Third-party RN library web support is inconsistent.** Libraries like `react-native-reanimated`, `react-native-gesture-handler`, and `react-native-svg` have web support that ranges from "good" to "partially broken" to "nonexistent."

**Why it happens:**
React Native Web's marketing suggests universal components. It works for simple cases (Text, View, Pressable, Image, ScrollView). Developers extrapolate from simple cases to complex ones.

**How to avoid:**
- **Shared package contains ONLY primitives:** `Text`, `View`, `Pressable`, `Image`, `TextInput`, `ScrollView`, `FlatList`, `ActivityIndicator`. Nothing else in the shared UI package.
- **Use `.web.tsx` / `.native.tsx` file extensions** for platform-specific implementations. Metro and webpack both resolve these correctly.
- **Never share navigation code.** Navigation is app-specific, not package-specific.
- **Create a "compatibility matrix" doc** listing which components are shared vs. platform-specific. Update it as you add components.
- **For animations:** Use `react-native-reanimated` for mobile and CSS transitions/Framer Motion for web. Do not try to share animation code.
- **Use Shadcn/ui for web, build separate mobile components** that share the same design tokens (colors, spacing, typography) through a shared theme package, NOT shared component implementations.

**Warning signs:**
- A "shared" component file that imports from `react-native-reanimated` or `react-native-gesture-handler`
- Platform-specific crashes: "X is not a function" on web for RN APIs
- CSS rendering glitches on web that don't appear on mobile
- Increasing use of `Platform.OS === 'web'` conditionals inside shared components (if > 2 conditionals, the component should be split)

**Phase to address:** Phase 3 (Shared Packages). Must establish the sharing boundary BEFORE building UI components.

**Recovery cost:** HIGH -- if you build 50 "shared" components that don't actually work cross-platform, you're rewriting 50 components. Easier to be restrictive upfront and promote components to shared only when proven.

**Confidence:** HIGH -- React Native Web limitations are well-documented and stable.

---

### Pitfall 4: OpenAPI-to-TypeScript Pipeline Becoming a Fragile Single Point of Failure

**What goes wrong:**
The pipeline is: Django Ninja schemas -> OpenAPI JSON -> codegen tool -> TypeScript types/client. This breaks in several ways:

1. **Schema drift:** Developer changes a Django Ninja schema but forgets to regenerate TypeScript. Frontend uses stale types. No error until runtime (or worse, silent data loss from missing fields).

2. **Breaking changes in generated code:** The codegen tool (openapi-typescript, orval, etc.) updates its output format between versions. Generated code changes even though the API didn't. This breaks the frontend build.

3. **Nullable/optional field confusion:** Django Ninja's `Optional[str]` can generate `string | null` or `string | undefined` depending on the codegen tool and OpenAPI version. Inconsistency causes TypeScript errors or silent null handling bugs.

4. **Enum handling inconsistencies:** Python enums serialize differently than TypeScript expects. String enums work; integer enums cause type narrowing issues in generated code.

5. **Circular reference handling:** Django Ninja models with self-referential relationships or deep nesting can generate OpenAPI specs that some codegen tools choke on.

**Why it happens:**
The pipeline has three moving parts (Django schema definition, OpenAPI spec generation, TypeScript codegen) maintained by three different open-source projects with independent release cycles. Changes in any one can ripple.

**How to avoid:**
- **CI gate:** Add a CI step that generates the OpenAPI spec from Django, runs codegen, and fails the build if the generated output differs from what's committed. This catches schema drift immediately.
- **Pin codegen tool version** in `package.json` -- never use `latest`
- **Use `openapi-typescript` for types-only generation** (not a full client). It's the most stable, least opinionated tool. Build the API client wrapper manually using the generated types.
- **Snapshot the OpenAPI spec in CI:** Compare `python manage.py export_openapi_schema` output against `openapi.json` in the repo. Fail if different. This forces deliberate spec updates.
- **Write a thin validation layer** that compares a sample of API responses against generated TypeScript types at test time (using Zod schemas generated from the same OpenAPI spec)
- **Handle nullable explicitly in Django Ninja:** Use `Field(None, nullable=True)` vs `Optional` with clear conventions documented in the project

**Warning signs:**
- Frontend devs saying "the types don't match the API response"
- `any` type casts appearing in frontend code to "fix" type errors
- CI passing but runtime 500 errors from schema mismatches
- Generated file diffs showing up in PRs that didn't touch the API

**Phase to address:** Phase 2 (API Foundation) for pipeline setup, ongoing enforcement in CI from Phase 4 (CI/CD).

**Recovery cost:** MEDIUM -- fixing the pipeline is straightforward; tracking down all the places where stale types caused bugs is the expensive part.

**Confidence:** HIGH -- OpenAPI codegen pipelines are well-understood, and these failure modes are widely documented.

---

### Pitfall 5: PGVector Wrong Index Type Causing 10-100x Performance Degradation

**What goes wrong:**
PGVector supports two index types for approximate nearest neighbor search:

1. **IVFFlat** -- older, simpler. Requires training on existing data. If you build an IVFFlat index on an empty or small table and then bulk-insert data, the index is trained on unrepresentative data and recall drops catastrophically (returning wrong results, not just slow results).

2. **HNSW** -- newer, recommended. No training needed, works with inserts. But wrong parameters (`m` and `ef_construction`) cause either massive memory usage (too high) or terrible recall (too low). Default parameters are often fine for < 100K vectors but need tuning beyond that.

Developers also make these mistakes:

3. **No index at all.** PGVector does exact nearest neighbor without an index. This is O(n) and works fine for 1,000 vectors. At 100,000 vectors, queries take seconds. At 1M, they time out.

4. **Wrong distance function.** Using L2 distance index (`vector_l2_ops`) when the application uses cosine similarity (`vector_cosine_ops`), or vice versa. The index doesn't accelerate queries using a different operator.

5. **Forgetting `SET ivfflat.probes` or `SET hnsw.ef_search`.** These runtime parameters control the speed/recall tradeoff at query time. Defaults are conservative (low recall for IVFFlat, reasonable for HNSW).

**Why it happens:**
Vector databases are relatively new to most web developers. The PGVector README is concise and doesn't emphasize production tuning. Developers copy a `CREATE INDEX` from a tutorial without understanding the implications.

**How to avoid:**
- **Use HNSW exclusively** in the template. It's strictly better than IVFFlat for this use case (incremental inserts, moderate scale, no pre-training needed)
- **Default HNSW parameters:** `m=16, ef_construction=64` for tables under 1M vectors. Document when to change.
- **Match the operator class to the distance function:**
  ```sql
  -- For cosine similarity (most common with OpenAI/Anthropic embeddings):
  CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);

  -- For L2 distance:
  CREATE INDEX ON items USING hnsw (embedding vector_l2_ops);

  -- For inner product:
  CREATE INDEX ON items USING hnsw (embedding vector_ip_ops);
  ```
- **Set `hnsw.ef_search` at query time** for the right recall/speed tradeoff:
  ```sql
  SET hnsw.ef_search = 100;  -- Higher = better recall, slower
  ```
- **Use cosine distance by default** in the template since OpenAI, Anthropic, and most embedding models are trained for cosine similarity
- **Add a Django migration** that creates the HNSW index with correct operator class. Don't leave index creation as a manual step.
- **Document the vector dimension** in the model: `embedding = VectorField(dimensions=1536)` -- mismatched dimensions cause cryptic errors

**Warning signs:**
- Vector search queries taking > 100ms for < 100K vectors (likely no index)
- Vector search returning irrelevant results despite good embeddings (wrong index type, wrong operator, or IVFFlat trained on bad data)
- Memory usage spiking when building HNSW index (m too high)
- `EXPLAIN ANALYZE` showing sequential scan instead of index scan

**Phase to address:** Phase 5 (AI Module). Must get this right on first implementation -- changing index types on large tables requires full reindex which can take hours.

**Recovery cost:** MEDIUM for index type change (reindex is slow but automated), HIGH if wrong distance function caused silent bad results that went undetected.

**Confidence:** HIGH -- PGVector's behavior is well-documented in its README and the PostgreSQL community.

---

### Pitfall 6: Expo Monorepo Metro Bundler Misconfiguration

**What goes wrong:**
Expo in a monorepo requires specific Metro bundler configuration to resolve packages from workspace root `node_modules` and sibling packages. Without it:

1. **"Unable to resolve module" errors** for shared packages. Metro's default resolver doesn't follow pnpm's symlinked `node_modules` structure.

2. **Duplicate React instances.** Metro resolves a different copy of React from the mobile app's `node_modules` than what shared packages use. This causes "Invalid hook call" errors -- the most confusing React error because the code looks correct.

3. **Cannot resolve `.web.tsx` extensions.** Metro needs explicit configuration to resolve platform-specific file extensions from workspace packages.

4. **Watchman file watching breaks** with pnpm's symlinked structure. File changes in shared packages don't trigger Metro hot reload.

**Why it happens:**
Metro bundler was designed for single-package React Native projects. Monorepo support requires explicit configuration that Expo's default setup doesn't provide. pnpm's symlink-based `node_modules` adds another layer of complexity vs npm/yarn's hoisted structure.

**How to avoid:**
- **Use Expo's monorepo guide explicitly.** Create `metro.config.js` that:
  ```javascript
  const { getDefaultConfig } = require('expo/metro-config');
  const path = require('path');

  const projectRoot = __dirname;
  const monorepoRoot = path.resolve(projectRoot, '../..');

  const config = getDefaultConfig(projectRoot);

  // Watch all files in the monorepo
  config.watchFolders = [monorepoRoot];

  // Let Metro know where to resolve packages from
  config.resolver.nodeModulesPaths = [
    path.resolve(projectRoot, 'node_modules'),
    path.resolve(monorepoRoot, 'node_modules'),
  ];

  // Force shared packages to use the app's React
  config.resolver.disableHierarchicalLookup = true;

  module.exports = config;
  ```
- **Set `"main"` field in shared package `package.json`** to point to the source (not built output) for development:
  ```json
  { "main": "src/index.ts" }
  ```
  Or use Expo's `expo-module-scripts` if shared packages need building.
- **Add shared packages to `app.json` or `expo` config** under `experiments.tsconfigPaths` or configure `resolver.extraNodeModules` in Metro
- **Verify single React instance:** In the Expo app, add a startup check: `console.log(require('react').version, require('react-native').version)` and verify shared packages log the same versions
- **Use `.pnpmfile.cjs`** or pnpm's `shamefully-hoist=true` for the mobile app workspace if symlink resolution issues persist (this is a pragmatic workaround, not ideal but widely used)

**Warning signs:**
- "Invalid hook call" errors that appear only when importing from shared packages
- Metro bundler errors mentioning "Unable to resolve" for `@repo/*` packages
- Hot reload not working for changes in shared packages
- Build succeeds on CI but fails locally (or vice versa) due to different `node_modules` structures

**Phase to address:** Phase 1 (Monorepo Foundation). Metro config must be correct before ANY shared package work begins.

**Recovery cost:** LOW-MEDIUM -- Metro config changes are localized, but debugging "Invalid hook call" without knowing the cause can waste days.

**Confidence:** MEDIUM -- Expo monorepo configuration evolves with each SDK release. The patterns above are based on Expo SDK 50-52 documentation. Validate against Expo SDK 53+ docs, as `expo/metro-config` API may have changed.

---

### Pitfall 7: Docker Compose Hot Reload Silently Not Working

**What goes wrong:**
The template promises "one-command local dev" with `docker compose up` and hot reload. In practice:

1. **File watching doesn't propagate into containers.** On macOS, Docker Desktop uses a Linux VM. The VM's filesystem notifications don't always propagate to the container. Django's `runserver` auto-reload works (it polls), but webpack/Next.js/Metro file watchers (which use `inotify`/`fsevents`) miss changes.

2. **Volume mount performance on macOS.** Bind-mounting the entire monorepo into containers causes severe I/O performance degradation. `node_modules` inside containers gets overlaid with the host's `node_modules` (or vice versa), causing platform-specific binary mismatches (`esbuild-linux` vs `esbuild-darwin`).

3. **pnpm store inside Docker.** If the pnpm store is on a volume mount, installs are extremely slow. If it's inside the container, it's lost on rebuild.

4. **Port conflicts.** Next.js (3000), Django (8000), Expo DevTools (19000-19002), Metro (8081), Postgres (5432) -- five+ ports. Developers with other projects running hit conflicts.

**Why it happens:**
Docker is great for deployment but has fundamental friction with development workflows that need fast filesystem access. Every monorepo template hits this.

**How to avoid:**
- **For Next.js in Docker:** Set `WATCHPACK_POLLING=true` environment variable to enable filesystem polling (slower but reliable). Or better: run Next.js OUTSIDE Docker on the host and only containerize Django + Postgres.
- **Hybrid dev approach (recommended for the template):**
  - Docker Compose for infrastructure: Postgres, Redis (if needed), any other services
  - Host machine for application code: Django (via `uv run`), Next.js (via `pnpm dev`), Expo (via `npx expo start`)
  - Turborepo orchestrates all dev servers via `turbo run dev`
  - Provide a `docker-compose.dev.yml` for infrastructure-only AND a `docker-compose.full.yml` for the "everything in Docker" purists
- **If keeping everything in Docker:**
  - Use named volumes for `node_modules` to avoid platform binary conflicts:
    ```yaml
    volumes:
      - ./apps/web:/app/apps/web
      - web_node_modules:/app/apps/web/node_modules  # Don't mount host node_modules
    ```
  - Use Docker Compose `develop.watch` (Compose Watch) for file sync instead of bind mounts -- this was introduced in Docker Compose v2.22+ and is purpose-built for dev hot reload
  - Set `CHOKIDAR_USEPOLLING=1` for webpack-based watchers
- **Configure non-conflicting ports** in `.env` with sensible defaults and document all ports in README

**Warning signs:**
- Developers saying "I have to restart the container to see changes"
- `docker compose up` taking > 60 seconds for initial start
- IDE autocomplete not working because `node_modules` are inside Docker
- "File not found" errors after saving a file (stale cache)
- `npm install` taking 5+ minutes inside Docker on macOS

**Phase to address:** Phase 1 (Monorepo Foundation). The dev experience decision (hybrid vs full Docker) must be made upfront.

**Recovery cost:** LOW -- switching from full-Docker to hybrid dev requires rewriting `docker-compose.yml` and updating dev scripts, but no application code changes.

**Confidence:** HIGH -- Docker dev experience issues on macOS are extremely well-documented and consistent across projects.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Disabling CSRF for API endpoints | Fixes 403 errors quickly | Security vulnerability; must re-enable and fix all clients later | Never -- use proxy or proper CSRF token forwarding |
| Using `any` types for generated API responses | Unblocks frontend dev when codegen is broken | Spreads through codebase; loses type safety benefit entirely | Only in initial prototype, must be resolved within same sprint |
| Skipping OpenAPI spec snapshot in CI | Faster CI pipeline | Schema drift goes undetected; frontend/backend desync | Never -- this is a 5-minute CI setup |
| `shamefully-hoist=true` in root `.npmrc` | Fixes "module not found" errors | Defeats pnpm's strict dependency isolation; hides missing `dependencies` declarations | Only as targeted override for specific Expo/RN compatibility, with a TODO to remove |
| Hardcoding environment URLs | Works for single deployment | Breaks when adding staging, preview deployments | Never -- use env vars from day one |
| Putting all shared code in one `@repo/shared` package | Simple, one package to maintain | Becomes a junk drawer; mobile app bundles web-only code and vice versa | Never -- split into `@repo/api-client`, `@repo/ui`, `@repo/schemas`, `@repo/utils` from the start |
| Using Django's `User` model directly | Avoids custom user model complexity | Cannot add fields to User later without painful migration; Django docs explicitly warn against this | Never -- always create a custom user model inheriting `AbstractUser`, even if identical at first |
| Committing `.env` to the repo | Easier onboarding | Secrets leak; different envs get wrong values | Never -- use `.env.example` with dummy values |

## Integration Gotchas

Common mistakes when connecting the stack's components.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Django Ninja + Next.js SSR | Calling Django API from Next.js server components without auth context (no cookies in server-side fetch) | Pass cookies explicitly from the request: `fetch(url, { headers: { cookie: request.headers.get('cookie') } })`. Or use Next.js middleware to inject auth. |
| Django Allauth + Expo | Using session cookies on mobile (don't persist across app restarts reliably) | Use Allauth's token-based headless auth for mobile; store tokens in `expo-secure-store` |
| PGVector + Django ORM | Using Django's ORM `filter()` for vector similarity search (no ORM support for `<->` operator) | Use `pgvector-django` package which adds `CosineDistance`, `L2Distance` lookups, or raw SQL for complex queries |
| Turborepo + GitHub Actions | Caching `node_modules` instead of Turborepo's cache | Cache `~/.turbo` directory and use `turbo run --filter` for affected packages. Don't cache `node_modules` -- cache pnpm store instead |
| Next.js App Router + Django API | Fetching user data in every server component (N+1 to the API) | Use React `cache()` function to deduplicate fetch calls within a single request, or fetch in layout and pass down |
| LangGraph + Postgres persistence | Using LangGraph's in-memory checkpointer in production | Use `langgraph-checkpoint-postgres` for durable state. Set up connection pooling (PgBouncer or Django's `CONN_MAX_AGE`) to avoid exhausting connections |
| Zod schemas + Django Ninja schemas | Manually keeping Zod schemas in sync with Django Ninja (they drift) | Generate Zod schemas from the same OpenAPI spec used for TypeScript types. Use a tool like `openapi-zod-client` or derive Zod schemas from the generated TypeScript types |
| Expo + React Native Web | Importing `expo-*` packages in shared code | `expo-*` packages are mobile-only. Shared UI primitives must use only `react-native` core components. Use `.native.tsx`/`.web.tsx` splits for any platform-specific code |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| PGVector without index | Queries < 50ms at 1K vectors | Add HNSW index at table creation, not "when it gets slow" | > 10K vectors: queries > 500ms; > 100K: queries > 5s |
| Django `DEBUG=True` in staging | Works fine, nice error pages | Never deploy with `DEBUG=True`; it leaks settings, accumulates SQL queries in memory, serves static files through Django | Any sustained traffic -- memory grows unbounded |
| Next.js fetching Django API without caching | Works at low traffic | Use Next.js `fetch` cache options and ISR/SSG where possible; configure proper `Cache-Control` headers from Django | > 100 concurrent users: Django becomes bottleneck for static-ish data |
| Embedding generation in request cycle | User waits 200-500ms for embedding | Generate embeddings async (Celery task, background job) or batch on write | Any endpoint that embeds text: adds 200-500ms latency per request |
| Unbounded `FlatList` in Expo | Smooth with 50 items | Use `FlatList` (not `ScrollView`) with `getItemLayout`, `windowSize`, and `maxToRenderPerBatch` props | > 500 items: jank, memory pressure, crashes on low-end devices |
| Django N+1 queries from Ninja serializers | Fast with 10 records | Use `select_related` / `prefetch_related` in querysets backing Ninja endpoints; add `django-silk` or `django-debug-toolbar` to catch N+1s in dev | > 50 records per page: response time scales linearly with count |

## Security Mistakes

Domain-specific security issues beyond generic web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Disabling CSRF for "API convenience" | Cross-site request forgery attacks on web app | Use Next.js API proxy (same-origin) or properly forward CSRF tokens; keep CSRF enabled |
| Storing auth tokens in AsyncStorage (Expo) | Tokens readable by any app with root/jailbreak access | Use `expo-secure-store` for token storage on mobile; it uses Keychain (iOS) / Keystore (Android) |
| OpenAPI spec publicly accessible in production | Attackers get full API documentation including internal endpoints | Conditionally serve OpenAPI spec: only in dev/staging, or behind authentication in production |
| Django `SECRET_KEY` shared across template instances | If one project is compromised, all projects using the same key are compromised | CLI scaffolder MUST generate a unique `SECRET_KEY` for each new project. Template should never have a real key committed |
| Not validating vector search input dimensions | Crafted inputs could cause Postgres errors or unexpected results | Validate that embedding vectors match the expected dimension before querying PGVector |
| CORS `allow_all_origins` in production | Any website can make authenticated requests to the API | Explicitly list allowed origins; use environment variable for origin configuration |

## UX Pitfalls

Common user experience mistakes in this domain (for template consumers, not end users).

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Template requires 15+ manual configuration steps after clone | Developer abandons template; faster to start from scratch | CLI scaffolder handles all configuration; `docker compose up` works immediately after scaffold |
| No clear documentation of what each shared package does | Developer puts code in wrong package, or duplicates code | Each package has a one-line description in root README and a `README.md` inside with scope + examples |
| Template includes AI module by default with no way to remove | Non-AI projects carry unnecessary dependencies and complexity | CLI scaffolder asks "Include AI module?" and excludes LangGraph, PGVector, embedding pipeline if "no" |
| Auth flow requires reading Django + Allauth + Ninja docs to understand | Developer wastes hours understanding auth plumbing | Template includes an `AUTH.md` that documents the exact auth flow with sequence diagrams for web and mobile |
| Error messages from misconfigured monorepo are cryptic | "Module not found" could be Metro, pnpm, Turborepo, or Expo | Add a `troubleshooting.md` covering top 10 errors and their fixes |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Authentication:** Often missing email verification flow -- signup works but emails don't send, verify link goes nowhere
- [ ] **Authentication:** Often missing password reset flow -- login page has "Forgot password?" link that 404s
- [ ] **Authentication:** Often missing auth state persistence on mobile -- works until app is killed, then user is logged out
- [ ] **OpenAPI codegen:** Often missing CI enforcement -- types generate locally but CI doesn't verify they're up to date
- [ ] **Docker dev setup:** Often missing volume mount for Python hot reload -- Django restarts but code changes inside container don't reflect
- [ ] **Shared packages:** Often missing proper TypeScript `exports` field in `package.json` -- works in dev (bundler resolves `src/`) but fails in production build
- [ ] **PGVector:** Often missing migration for index creation -- `CREATE EXTENSION vector` is there but `CREATE INDEX` on the embedding column is not
- [ ] **Expo app:** Often missing deep linking configuration -- push notifications or email links can't open the app to a specific screen
- [ ] **CI pipeline:** Often missing Python linting/testing -- Turborepo runs JS tasks but Python tasks need separate `uv run` commands
- [ ] **Template scaffolder:** Often missing file content replacement -- project name in `package.json` but not in `docker-compose.yml`, Django `settings.py`, or `app.json`

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Turborepo Python caching broken | LOW | Rewrite `turbo.json` task inputs/outputs for Python tasks; no code changes needed |
| Auth strategy wrong (sessions everywhere or tokens everywhere) | HIGH | Implement dual auth strategy; rewrite API client auth interceptors; update all authenticated endpoints; re-test every auth-dependent screen |
| React Native Web shared component overreach | HIGH | Audit all shared components; split into `.web.tsx`/`.native.tsx` variants; update imports in both apps; extensive manual testing |
| OpenAPI pipeline drift | MEDIUM | Regenerate types; fix TypeScript errors across frontend; add CI gate to prevent recurrence |
| PGVector wrong index type | MEDIUM | Drop old index; create new HNSW index with correct operator class; reindex (takes minutes to hours depending on data size) |
| Expo Metro bundler misconfigured | LOW-MEDIUM | Update `metro.config.js`; clear Metro cache (`npx expo start --clear`); verify shared package resolution |
| Docker hot reload not working | LOW | Switch to hybrid dev approach or add polling-based file watchers; update `docker-compose.yml` |
| Custom user model not created initially | HIGH | Extremely painful migration if existing data exists; requires faking migrations and potentially dumping/reloading data. Django docs explicitly say "do this at the start of the project" |
| LangGraph checkpointer data loss | MEDIUM-HIGH | Switch from memory to Postgres checkpointer; existing conversation state is lost; users must restart conversations |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Turborepo Python integration | Phase 1: Monorepo Foundation | `turbo run lint test` caches correctly for Python changes; cache hit on re-run with no changes |
| Auth cross-platform misconfiguration | Phase 2: Auth Foundation | Login/logout works on web (cookie) AND mobile (token) in same test run; CSRF enabled |
| React Native Web overreach | Phase 3: Shared Packages | Shared UI package imports ONLY from `react-native` core; no `expo-*` imports; renders on web without errors |
| OpenAPI pipeline fragility | Phase 2: API Foundation + Phase 4: CI/CD | CI fails if OpenAPI spec is stale; generated types match API responses in integration tests |
| PGVector wrong index | Phase 5: AI Module | `EXPLAIN ANALYZE` on vector search shows HNSW index scan; query < 50ms for 10K vectors |
| Expo Metro bundler | Phase 1: Monorepo Foundation | Expo app starts, imports from `@repo/*` packages, hot reload works for shared package changes |
| Docker hot reload broken | Phase 1: Monorepo Foundation | File change in any app triggers reload within 2 seconds; documented dev workflow |
| Custom user model missing | Phase 2: Auth Foundation | `AUTH_USER_MODEL` points to custom model; migration 0001 creates custom User table |
| Template hard to customize | Phase 6: CLI Scaffolder | Scaffolder replaces all project-name references; removable modules (AI) fully excisable without errors |
| LangGraph checkpointer | Phase 5: AI Module | Conversation state persists across server restarts; checkpointer uses `langgraph-checkpoint-postgres` |
| Monorepo CI/CD caching | Phase 4: CI/CD | CI completes < 5 min for no-change re-run; Python and JS tasks both cache correctly |
| Schema sync (Zod + Django Ninja) | Phase 3: Shared Packages | Zod schemas generated from OpenAPI spec; validation test compares Zod output to Django Ninja output for sample data |

## Sources

- Training data knowledge of Turborepo, Django, Next.js, Expo, PGVector, LangGraph, Docker (confidence: MEDIUM -- training data up to May 2025)
- PGVector README patterns for indexing strategies (confidence: HIGH -- stable documentation)
- React Native Web component compatibility (confidence: HIGH -- well-documented limitations)
- Django documentation on custom user models (confidence: HIGH -- stable, longstanding recommendation)
- Expo monorepo guide patterns (confidence: MEDIUM -- evolves with SDK releases; validate against Expo SDK 53+ docs)
- Django Allauth headless mode (confidence: MEDIUM -- feature is relatively new; validate config keys against current docs)
- LangGraph checkpoint persistence (confidence: MEDIUM -- verify `langgraph-checkpoint-postgres` package name and API against current docs)
- Docker Compose Watch / `develop.watch` (confidence: MEDIUM -- introduced in Compose v2.22+; verify current syntax)

**Note:** WebSearch and WebFetch were unavailable during this research session. All findings are based on training data (cutoff: May 2025). Items marked MEDIUM confidence should be validated against current official documentation before implementation, particularly:
1. Expo SDK 53+ monorepo configuration (may have simplified since SDK 52)
2. Django Allauth headless mode configuration keys
3. LangGraph checkpoint-postgres package API
4. Turborepo `inputs`/`outputs` syntax for the current version
5. Docker Compose `develop.watch` configuration syntax

---
*Pitfalls research for: Foundation Template (Django Ninja Extra + Next.js 15 + Expo + Turborepo)*
*Researched: 2026-02-08*
