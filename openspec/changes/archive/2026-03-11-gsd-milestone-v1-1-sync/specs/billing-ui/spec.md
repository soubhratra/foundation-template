## ADDED Requirements

### Requirement: billing.config.ts lives at the web app root and uses a baseUrl-relative import path

`billing.config.ts` SHALL be placed at `apps/web/billing.config.ts` (the web app root, not inside `src/`). It SHALL be imported as `'billing.config'` (baseUrl-relative), not `'@/billing.config'`.

**Rationale:** The `@/` alias in `tsconfig.json` maps to `./src/`. `billing.config.ts` lives at the app root, outside `src/`, so the alias does not resolve it. The baseUrl-relative import path works because `tsconfig.baseUrl` points to the app root.

_(Decision: Phase 11)_

#### Scenario: Import resolves correctly in Next.js

- **WHEN** a server component imports `from 'billing.config'`
- **THEN** TypeScript resolves it to `apps/web/billing.config.ts` without a path alias error

---

### Requirement: BillingPage delegates server actions to BillingClient via props

`BillingPage` (Server Component) SHALL import server action functions and pass them as props to `BillingClient` (Client Component). `BillingClient` SHALL accept server actions as typed function props rather than importing them directly.

**Rationale:** Next.js App Router prevents direct server action imports in Client Components. Passing actions as props is the stable, TypeScript-safe pattern for server-to-client action delegation without workarounds.

_(Decision: Phase 11)_

#### Scenario: Server actions available in client component

- **WHEN** `BillingPage` renders `BillingClient`
- **THEN** all billing server actions (subscribe, change plan, cancel, reactivate) are passed as props and callable from the client

---

### Requirement: AnyApiClient cast used for billing POST mutations until type regeneration

Billing server actions that call POST mutation endpoints SHALL cast the API client to `AnyApiClient` (an `any`-typed client variant) at the call site, with a `// TODO: regenerate types` comment.

**Rationale:** The OpenAPI type generation pipeline may lag behind newly added endpoints. Rather than silencing TypeScript globally or blocking implementation, the `AnyApiClient` cast is a scoped, visible workaround that signals where type regeneration is needed.

_(Decision: Phase 11)_

#### Scenario: Billing mutation compiles without type error

- **WHEN** a billing server action calls a POST endpoint not yet in the generated types
- **THEN** the `AnyApiClient` cast allows the call to compile while preserving type safety elsewhere

---

### Requirement: get_status() returns all-None sentinel for users with no subscription

`BillingService.get_status()` SHALL return an object with all fields set to `None` (a sentinel value) when the user has no active subscription record. It SHALL NOT raise a `ServiceError` for this case.

**Rationale:** The billing dashboard renders for all authenticated users, including free-tier users with no subscription. A `ServiceError` would require the page to handle an error state just to show "no subscription." The all-None sentinel lets the page render a free-tier view without error handling.

_(Decision: Phase 11)_

#### Scenario: Free-tier user sees billing dashboard

- **WHEN** an authenticated user with no subscription navigates to the billing dashboard
- **THEN** the page renders a free-tier view (no error, no crash) using the all-None sentinel

#### Scenario: Subscribed user sees plan details

- **WHEN** an authenticated user with an active subscription navigates to the billing dashboard
- **THEN** the page renders subscription details with non-None values from `get_status()`

---

### Requirement: createCheckoutSessionAction derives origin from next/headers

`createCheckoutSessionAction` SHALL derive the `success_url` and `cancel_url` origin by reading the `host` header from `next/headers`, not from a `NEXT_PUBLIC_APP_URL` environment variable.

**Rationale:** Next.js server actions have access to request headers via `next/headers`. Reading `host` directly eliminates the need for a `NEXT_PUBLIC_APP_URL` environment variable, reducing configuration surface and making the action portable across environments.

_(Decision: Phase 11)_

#### Scenario: Checkout session uses correct redirect URLs

- **WHEN** `createCheckoutSessionAction` is called from any environment
- **THEN** the `success_url` and `cancel_url` use the origin derived from the current request's `host` header

---

### Requirement: no_subscription action type enables free-tier plan card buttons

`billingConfig.actions["no_subscription"]` SHALL include `"subscribe"` as an allowed action. Plan cards that are not the free plan SHALL display a "Select" button when the user has no active subscription.

**Rationale:** Free-tier users (no subscription record) previously saw plan cards with no buttons because `no_subscription: []` left `canUpgrade` and `canDowngrade` both false. The `"subscribe"` action type signals that free-tier users can initiate a checkout flow, rendering "Select" buttons on paid plan cards.

_(Decision: Phase 11)_

#### Scenario: Free-tier user sees Select buttons on paid plans

- **WHEN** a user with no subscription views the billing page
- **THEN** each paid plan card shows a "Select" button (not blank)

#### Scenario: Free plan card has no Select button

- **WHEN** a user with no subscription views the billing page
- **THEN** the free plan card shows "Current plan" (not "Select") because it is the user's effective current plan

---

### Requirement: Free-tier isCurrent fallback marks free plan as current

When a user has no active subscription, the plan card whose `id === "free"` SHALL be considered the current plan (`isCurrent = true`). Plan cards derive `isCurrent` as: `!subscription && plan.id === "free"` OR `subscription?.plan_id === plan.id`.

**Rationale:** Without this fallback, `isCurrent` is false for all cards when `subscription` is `undefined`, so no plan is highlighted as current. The fallback ensures the free plan is visually designated as the user's current plan without requiring a subscription record.

_(Decision: Phase 11)_

#### Scenario: Free plan marked current for users with no subscription

- **WHEN** a user with no subscription views the billing page
- **THEN** the free plan card displays a "Current plan" disabled button

#### Scenario: Subscribed user sees their plan marked current

- **WHEN** a user with an active subscription whose `plan_id` matches a plan card views the billing page
- **THEN** only that plan card shows "Current plan"

---

### Requirement: Migration 0002 seeded values are canonical price_id source for tests

Test fixtures and `conftest.py` price_id defaults SHALL match the `price_id` values seeded by data migration `0002` in `PlanProviderMapping`. The migration data is the single source of truth; test configuration MUST stay in sync with it.

**Rationale:** Tests that create `Subscription` records with price_ids not present in `PlanProviderMapping` will fail to resolve `plan_id`, silently producing wrong behavior. Anchoring test data to migration data eliminates this class of mismatch.

_(Decision: Phase 11)_

#### Scenario: Test subscription resolves plan_id correctly

- **WHEN** a test creates a `Subscription` using the canonical `price_id` from `conftest.py`
- **THEN** `PlanProviderMapping` lookup resolves `plan_id` to the expected plan

---

### Requirement: reactivate_subscription takes no plan payload

The `POST /api/billing/subscription/reactivate/` endpoint SHALL accept no request body. Reactivation SHALL undo `cancel_at_period_end` via the adapter's `reactivate_subscription()` method; it SHALL NOT call `modify_subscription()`.

**Rationale:** Reactivation restores the subscription as-is — same plan, same price. There is no plan selection involved. Accepting a `plan_id` payload would imply plan-change semantics, which is wrong. The adapter call is a separate, simpler operation.

_(Decision: Phase 11)_

#### Scenario: Reactivation restores subscription without plan change

- **WHEN** a user with `cancel_at_period_end=True` calls `POST /api/billing/subscription/reactivate/`
- **THEN** `cancel_at_period_end` is set to `False` and the subscription continues on the same plan with no plan modification
