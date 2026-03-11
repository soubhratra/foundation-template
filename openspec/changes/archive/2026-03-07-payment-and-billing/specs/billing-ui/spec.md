## ADDED Requirements

### Requirement: Public pricing page

The system SHALL include a publicly accessible pricing page at `/pricing` within the marketing section of `apps/web/` (`app/(marketing)/pricing/page.tsx`). The page SHALL display available subscription plans sourced from a static configuration (plan name, price, billing interval, feature list). The page SHALL render as a Server Component. A call-to-action button on each plan SHALL initiate the checkout flow.

#### Scenario: Unauthenticated user views pricing

- **WHEN** an unauthenticated user navigates to `/pricing`
- **THEN** the page renders with plan cards, prices, and feature lists without requiring login

#### Scenario: Authenticated user clicks upgrade on pricing page

- **WHEN** an authenticated user clicks a plan CTA on `/pricing`
- **THEN** the browser calls `POST /api/billing/checkout/` and redirects to the returned Stripe Checkout URL

#### Scenario: Unauthenticated user clicks a plan CTA

- **WHEN** an unauthenticated user clicks a plan CTA on `/pricing`
- **THEN** the user is redirected to the login page with a `?next=/pricing` query parameter

---

### Requirement: Billing settings page

The system SHALL include a billing management page at `/settings/billing` within the authenticated app section (`app/(app)/settings/billing/page.tsx`). The page SHALL display the user's current subscription status (sourced from `GET /api/billing/subscription/`) and a button to open the Stripe Customer Portal.

#### Scenario: Active subscriber views billing settings

- **WHEN** an authenticated user with `subscription_status = "active"` navigates to `/settings/billing`
- **THEN** the page shows plan name, billing period end date, and a "Manage Billing" button

#### Scenario: User with no subscription views billing settings

- **WHEN** an authenticated user with `subscription_status = "none"` navigates to `/settings/billing`
- **THEN** the page shows "No active subscription" and a link to `/pricing`

#### Scenario: User clicks Manage Billing

- **WHEN** an authenticated user clicks "Manage Billing" on `/settings/billing`
- **THEN** the browser calls `POST /api/billing/portal/` and redirects to the returned Stripe Customer Portal URL

---

### Requirement: Subscription status in auth context

The frontend auth context (React Query cache or Zustand store) SHALL expose `subscriptionStatus` derived from the user session response. Components MAY read `subscriptionStatus` for feature gating without additional API calls.

#### Scenario: Subscription status is available after login

- **WHEN** a user logs in successfully
- **THEN** the auth response includes `subscription_status` and it is available in the frontend auth context

#### Scenario: Feature gate renders based on subscription status

- **WHEN** a component reads `subscriptionStatus === "active"` from auth context
- **THEN** the gated feature is rendered without an additional network request to `/api/billing/subscription/`

---

### Requirement: Post-checkout redirect handling

After a successful Stripe Checkout, Stripe redirects the user to `STRIPE_SUCCESS_URL`. The success page SHALL display a confirmation message and trigger a refresh of the user's subscription status in the frontend auth context.

#### Scenario: Success page refreshes subscription state

- **WHEN** a user lands on the checkout success page
- **THEN** the frontend invalidates the auth/subscription cache and re-fetches the current user, reflecting the new `subscription_status`

#### Scenario: Cancelled checkout returns user to pricing

- **WHEN** a user cancels out of Stripe Checkout
- **THEN** the user is returned to the `STRIPE_CANCEL_URL` (defaults to `/pricing`) with no subscription created
