## Context

Foundation Template has 34 shipped phases and ~150 OpenSpec requirements with no browser-level E2E tests and no structured automation loop. Existing test coverage lives entirely in pytest (API) and vitest (web unit), with Detox scaffolded for mobile E2E but not yet populated.

The core problem is feedback latency: Claude agents can run tests but cannot self-correct because failure output is unstructured, not linked to requirement IDs, and not written to a predictable location. The goal is to close that loop without adding a complex framework — just shell scripts, Playwright, and a convention for traceability markers.

## Goals / Non-Goals

**Goals:**

- Single-command entrypoints for every test tier (API, E2E, all)
- Structured `test-results/FAILURES.md` parseable by Claude with requirement IDs on every failure
- `check-req-coverage.py` producing a per-requirement coverage table for all v1.1–v1.4 requirements
- Playwright tests covering every UI-facing feature shipped through v1.4
- Nightly CI that auto-opens a GitHub issue on failure
- PR CI smoke job blocking merge on auth/health regressions

**Non-Goals:**

- Detox mobile E2E — scaffolded in Phase 7, populated in a future milestone
- Visual regression testing (screenshot diffing)
- Load/performance testing
- Contract testing (schemathesis already handles this in Phase 18)
- 100% code coverage — spec traceability markers, not line coverage thresholds, are the metric here

## Decisions

### Decision 1: Playwright over Cypress for web E2E

**Chosen:** Playwright (`@playwright/test`)

**Why Playwright:**

- Native multi-browser (Chromium, Firefox, WebKit) with a single config
- Built-in `request` context for API calls within tests — needed for seeding fixtures without a separate HTTP client
- `playwright.config.ts` can point at `$BASE_URL` making the same test suite work locally and in CI without branching logic
- First-class TypeScript support matching the rest of the monorepo
- No paid tier; runs fully headless in GitHub Actions without extra setup

**Alternatives rejected:**

- **Cypress**: Component testing strength, but weaker multi-browser support; requires `cypress.env.json` for CI env vars rather than standard env vars; network interception API is more verbose for API-only assertions
- **Selenium/WebDriver**: Too verbose; no native TypeScript; slow CI startup

### Decision 2: Playwright lives in `apps/web/tests/e2e/`

**Chosen:** `apps/web/tests/e2e/` with `apps/web/playwright.config.ts`

**Why co-located with web app:**

- E2E tests are consumers of the web app's routes — co-location makes it obvious which app they test
- `pnpm --filter web test:e2e` works naturally within Turborepo
- Playwright's `baseURL` can resolve relative paths from the web app's known URL

**Alternatives rejected:**

- **Root-level `tests/e2e/`**: Cross-app E2E would warrant this but all tests here target the Next.js frontend
- **Separate `apps/e2e/` workspace**: Overkill for a single target app; creates another pnpm workspace to maintain

### Decision 3: Fixture seeding via Playwright `request` (API calls, not DB)

**Chosen:** Playwright's built-in `request` fixture makes authenticated API calls in `beforeEach`/`beforeAll` to create test data

**Why API-level seeding:**

- Tests remain black-box — they test the same surface as real users
- No Django ORM dependency in the Playwright process; no shared DB connection
- Seeded users/orgs are cleaned up via `afterAll` DELETE API calls — no persistent state leaks between runs

**Alternatives rejected:**

- **factory_boy fixtures over DB connection**: Couples Playwright to Django internals; breaks when running E2E against a deployed URL
- **Pre-seeded SQL dump**: Brittle (schema drift), non-isolated (tests share state), cannot run concurrently

### Decision 4: FAILURES.md format for Claude parseability

**Chosen:** Markdown table with columns: `Test`, `File:Line`, `Assertion`, `Requirements`, `Status`

```markdown
## Failed Tests — 2026-03-17T02:00:00Z

| Test                          | File                 | Assertion                          | Requirements | Status |
| ----------------------------- | -------------------- | ---------------------------------- | ------------ | ------ |
| test_create_org_requires_auth | tests/test_org.py:42 | assert response.status_code == 401 | ORG-01       | FAILED |
```

**Why this format:**

- Claude can parse a markdown table reliably — fixed column positions
- Requirement IDs in the table let Claude cross-reference against OpenSpec specs without grepping test files
- Timestamp allows Claude to distinguish stale reports from fresh ones
- Same format from both `run-api-tests.sh` and `run-e2e-tests.sh` — single parser handles both

**Alternatives rejected:**

- **JUnit XML**: Machine-readable but verbose; Claude parses markdown better than XML
- **JSON**: Parseable but not human-scannable; FAILURES.md is meant to be reviewed by humans too
- **Plain text**: No structure; requirement IDs would need regex extraction

### Decision 5: Spec traceability marker convention

**Chosen:**

- pytest: `@pytest.mark.req("REQ-01", "REQ-02")` — supports multiple IDs
- Playwright: `// @spec: REQ-01, REQ-02` comment at test start

**Why these formats:**

- `@pytest.mark.req()` integrates with pytest's marker API — `check-req-coverage.py` uses `pytest --collect-only -q` output plus marker introspection
- Playwright comments are simpler than custom test annotations; `grep -r "@spec:"` is enough to extract all coverage
- Both formats are trivially searchable with a single grep pattern

**Alternatives rejected:**

- **Custom pytest plugin**: More power but unnecessary complexity for a grep-based coverage checker
- **Test name conventions** (e.g., `test_ORG01_create_org`): Harder to see multiple req IDs; breaks tab completion

### Decision 6: `check-req-coverage.py` sources requirements from the roadmap

**Chosen:** Script reads requirement IDs from the ROADMAP.md phase sections (`Requirements: X, Y`) and cross-references against collected markers

**Why roadmap as source of truth:**

- ROADMAP.md already enumerates every requirement ID per phase — no separate requirements registry to maintain
- Simple regex parse (`Requirements: (.+)` per phase block) extracts the full list

**Alternatives rejected:**

- **Parse OpenSpec spec files for IDs**: Spec files use freeform sections, not structured ID fields — fragile to parse
- **Hardcoded requirements list**: Maintenance burden; drifts from actual phases

### Decision 7: CI E2E environment uses Docker Compose (not separate test images)

**Chosen:** GitHub Actions workflow starts `docker compose up -d`, runs migrations + seed script, then runs Playwright against `http://localhost:3000`

**Why reuse docker-compose.yml:**

- Same environment Claude uses locally — no environment drift between local and CI
- `docker compose --profile ci` variant can omit Flower and Jaeger to reduce startup time
- Nightly workflow teardown: `docker compose down -v` ensures clean state for the next run

**Alternatives rejected:**

- **Pre-built test Docker image**: Faster startup but diverges from local dev environment; adds image build/push overhead
- **SQLite in-memory for E2E**: Cannot use PGVector; misses Postgres-specific behavior

## Risks / Trade-offs

**[Risk] Playwright tests are slow in CI (60-120s per suite)** → Mitigation: PR smoke job runs only auth + health probe tests (~10 tests, <30s); full suite is nightly only

**[Risk] `beforeEach` API seeding adds 200-500ms per test** → Mitigation: Move expensive setup to `beforeAll` at describe-block level; parallelise Playwright workers to 2 in CI

**[Risk] GDPR export test triggers real file download — browser sandbox may block it** → Mitigation: Use Playwright's `page.waitForEvent("download")` with a 10s timeout; fall back to asserting the download API endpoint returns 200 via `request` context if browser download is unreliable

**[Risk] OAuth redirect tests require real provider URLs** → Mitigation: Tests only assert button presence + redirect initiation URL starts with `https://accounts.google.com` / `https://github.com/login/oauth` — no live credentials needed

**[Risk] Retroactively adding `@pytest.mark.req()` to ~50 existing test functions may introduce merge conflicts** → Mitigation: This is a pure-additive change (decorator only); no logic changes; conflicts resolve trivially

**[Risk] `check-req-coverage.py` ROADMAP parsing breaks if heading format changes** → Mitigation: Regex is liberal (`Requirements:` anywhere in a phase block); add a CI step that fails if the script exits non-zero

## Migration Plan

1. **Phase 35 (scripts + traceability):** Add `scripts/` directory and retrofit `@pytest.mark.req()` markers — no production code changes; zero risk
2. **Phase 36 (core E2E):** Add `apps/web/playwright.config.ts` and `tests/e2e/` — additive only; existing `pnpm test` vitest run is unchanged
3. **Phase 37 (B2B E2E):** Extend `tests/e2e/` — additive only
4. **Phase 38 (CI):** Add `e2e-nightly.yml`, extend `ci.yml` smoke job — existing CI jobs unchanged; new job only adds to the matrix

**Rollback:** All changes are additive (new files, new CI jobs, new markers). Rollback = delete the new files. No schema migrations, no production code changes.

## Open Questions

- **Seed user credentials in CI**: Should the E2E seed script create a fixed test user (`e2e@example.com / Password123!`) via Django management command, or use the signup API flow? → Leaning toward management command to avoid testing the signup flow as a prerequisite for every other test.
- **Playwright browser matrix**: Chromium-only for speed, or Chromium + Firefox? → Chromium-only in PR smoke; Chromium + Firefox in nightly.
- **`test-results/` gitignore scope**: Gitignore at root or per-app? → Root `.gitignore` entry covers both `apps/api/test-results/` and `apps/web/test-results/`.
