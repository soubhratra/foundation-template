## ADDED Requirements

### Requirement: User model billing fields

The `accounts.User` model SHALL include two new fields:

- `stripe_customer_id`: `CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)` — the Stripe Customer ID (`cus_...`). `null` until the user initiates their first checkout.
- `subscription_status`: `CharField(max_length=50, default="none")` — denormalized subscription state. Valid values: `"none"`, `"trialing"`, `"active"`, `"past_due"`, `"canceled"`. Updated by the Stripe webhook handler; NOT written directly by user-facing endpoints.

Both fields MUST be added via a Django migration (`accounts/migrations/0002_user_billing_fields.py` or next in sequence).

#### Scenario: New user has default billing state

- **WHEN** a new user account is created
- **THEN** `stripe_customer_id` is `null` and `subscription_status` is `"none"`

#### Scenario: stripe_customer_id uniqueness is enforced

- **WHEN** two users are assigned the same `stripe_customer_id`
- **THEN** a database integrity error is raised

---

### Requirement: subscription_status included in auth responses

The authenticated user response schema SHALL include `subscription_status`. This applies to:

- The session/token response after login
- The `GET /api/auth/me/` (or equivalent current-user) endpoint

The field MUST be read from `User.subscription_status` (the local denormalized value) — no live Stripe API call is made during auth responses.

#### Scenario: Login response includes subscription status

- **WHEN** a user authenticates successfully
- **THEN** the response body includes `"subscription_status": "<value>"` alongside other user fields

#### Scenario: Current-user endpoint includes subscription status

- **WHEN** an authenticated user calls `GET /api/auth/me/`
- **THEN** the response includes `"subscription_status": "<current value>"`
