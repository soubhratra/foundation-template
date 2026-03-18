# Web App — Testing Guide

## Running Tests

```bash
# Unit tests (vitest)
pnpm --filter web test

# E2E tests (Playwright)
pnpm --filter web test:e2e

# E2E against specific URL
BASE_URL=https://staging.example.com pnpm --filter web test:e2e

# E2E smoke only (auth + health)
pnpm --filter web exec playwright test tests/e2e/auth.spec.ts tests/e2e/health.spec.ts
```

## Playwright E2E Tests

### Location

```
apps/web/tests/e2e/
├── fixtures/           # Shared test helpers and API seeders
├── global-setup.ts     # Runs once before all tests (seeds test users)
├── auth.spec.ts        # E2E-01: Auth flows
├── settings.spec.ts    # E2E-02: Settings + GDPR export
├── billing.spec.ts     # E2E-03: Billing page
├── health.spec.ts      # E2E-04: Health probes (API assertions)
├── social-auth.spec.ts # E2E-05: OAuth redirect verification
├── rbac.spec.ts        # E2E-06: Role-based access control
├── org-management.spec.ts # E2E-07: Org creation + invites
├── api-keys.spec.ts    # E2E-08: API key lifecycle
└── webhooks-audit.spec.ts # E2E-09, E2E-10: Webhooks + audit log
```

### Self-Seeding Pattern

Tests create their own data via API calls — do NOT rely on pre-existing database state:

```typescript
test.beforeAll(async ({ request }) => {
  // Seed test data via API
  await request.post('/api/v1/some-resource/', { data: { ... } })
})

test.afterAll(async ({ request }) => {
  // Clean up
  await request.delete('/api/v1/some-resource/123/')
})
```

### Spec Traceability — REQUIRED

Every Playwright test that covers a specific OpenSpec requirement MUST include a `// @spec:` comment as the first line of the test body:

```typescript
test('signup redirects to dashboard', async ({ page }) => {
  // @spec: E2E-01
  await page.goto('/auth/signup')
  ...
})
```

Multiple requirements:

```typescript
// @spec: E2E-07, ORG-01
```

Run `scripts/check-req-coverage.py` to verify coverage. A phase cannot be marked complete if any requirement appears as `uncovered`.

### Configuration

`playwright.config.ts` reads `BASE_URL` from environment (default: `http://localhost:3000`).
The same test suite runs locally and in CI without code changes.

## Unit Tests (vitest)

Tests live in `apps/web/__tests__/` or co-located as `*.test.ts` files.

```bash
pnpm --filter web test       # run once
pnpm --filter web test:watch # watch mode
```

Use MSW for API mocking — handlers in `tests/mocks/handlers.ts`.
