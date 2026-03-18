## ADDED Requirements

### Requirement: Organization Creation and Ownership

The system SHALL allow authenticated users to create organizations with a unique name and slug, with the creator automatically assigned the `owner` role.

#### Scenario: User creates an organization

- **WHEN** an authenticated user calls `POST /api/v1/orgs/` with a valid name and slug
- **THEN** an `Organization` record SHALL be created
- **AND** a `Membership` record SHALL be created linking the user to the org with `role = "owner"`
- **AND** the response SHALL include the organization's id, name, slug, and the caller's membership role

#### Scenario: Slug uniqueness enforced

- **WHEN** a user attempts to create an organization with a slug that already exists
- **THEN** the system SHALL return `409 Conflict`

### Requirement: Team Membership with Role Enforcement

The system SHALL enforce three membership roles (`owner`, `admin`, `member`) on all org-scoped API endpoints via `IsOrgAdmin` and `IsOrgMember` Ninja Extra permission classes.

#### Scenario: Member can access org-scoped resources

- **WHEN** an authenticated user with any role (`owner`, `admin`, or `member`) in org "acme" calls an endpoint at `/api/v1/org/acme/...`
- **THEN** the endpoint SHALL process the request normally
- **AND** `request.org` SHALL be set to the resolved `Organization` object for downstream use

#### Scenario: Non-member receives 404, not 403

- **WHEN** an authenticated user who is NOT a member of org "acme" calls `/api/v1/org/acme/...`
- **THEN** the system SHALL return `404 Not Found`
- **AND** the response SHALL not confirm or deny the organization's existence

#### Scenario: Member without admin role blocked from admin endpoints

- **WHEN** a user with `role = "member"` calls an endpoint protected by `IsOrgAdmin`
- **THEN** the system SHALL return `403 Forbidden`

#### Scenario: Cross-org resource access blocked

- **WHEN** a member of org "acme" attempts to access a resource belonging to org "globex"
- **THEN** the system SHALL return `403 Forbidden`

### Requirement: Email Invitation Flow

The system SHALL allow org owners and admins to invite users by email, with invitations expiring after 72 hours and bound to the invited email address.

#### Scenario: Org admin sends invitation

- **WHEN** an org admin calls `POST /api/v1/org/{slug}/invitations/` with a valid email
- **THEN** an `Invitation` record SHALL be created with a URL token and a 72-hour expiry
- **AND** an invitation email SHALL be sent to the invited address via the existing `EmailAdapter`
- **AND** the email SHALL contain a link in the format `/accept-invite?token=<token>`

#### Scenario: Existing user accepts invitation

- **WHEN** a logged-in user whose email matches the invitation visits the accept link
- **THEN** the invitation SHALL be consumed immediately
- **AND** a `Membership` record SHALL be created with `role = "member"`
- **AND** the user SHALL be redirected to the org dashboard

#### Scenario: New user accepts invitation

- **WHEN** an unauthenticated user visits the accept link
- **THEN** the token SHALL be stored in the session
- **AND** the user SHALL be redirected to the signup flow
- **AND** after successful signup the token SHALL be consumed automatically
- **AND** the new user SHALL be added to the org with `role = "member"`

#### Scenario: Email mismatch rejected

- **WHEN** a logged-in user whose email does NOT match the invitation visits the accept link
- **THEN** the system SHALL return `400 Bad Request` with `{"detail": "This invitation was sent to a different email address."}`

#### Scenario: Expired invitation rejected

- **WHEN** a user visits an accept link for an invitation older than 72 hours
- **THEN** the system SHALL return `410 Gone`

### Requirement: Ownership Transfer

The system SHALL allow org owners to transfer ownership to another member, demoting themselves to `admin`.

#### Scenario: Owner transfers ownership

- **WHEN** an org owner calls `POST /api/v1/org/{slug}/transfer-ownership/` with a valid member's user id
- **THEN** the target member's role SHALL be updated to `"owner"`
- **AND** the caller's role SHALL be updated to `"admin"`
- **AND** exactly one owner SHALL exist at all times

#### Scenario: Transfer to non-member rejected

- **WHEN** an owner attempts to transfer to a user not in the org
- **THEN** the system SHALL return `400 Bad Request`

### Requirement: Per-Org Stripe Billing via OrgCustomer

The system SHALL support per-org Stripe billing through a separate `OrgCustomer` model, parallel to the existing user `Customer` model.

#### Scenario: OrgCustomer created for org Stripe billing

- **WHEN** an org is connected to a Stripe customer
- **THEN** an `OrgCustomer` record SHALL link the `Organization` to a Stripe customer ID
- **AND** `OrgCustomer` SHALL be separate from the user `Customer` model

#### Scenario: has_org_feature() checks org plan before personal plan

- **WHEN** `has_org_feature(user, org, "feature_key")` is called
- **AND** the org has an active Stripe subscription
- **THEN** the result SHALL be derived from the org's plan entitlements (not the user's personal plan)

#### Scenario: has_org_feature() falls back to personal plan when no org subscription

- **WHEN** `has_org_feature(user, org, "feature_key")` is called
- **AND** the org has no active subscription
- **THEN** the result SHALL fall back to `has_feature(user, "feature_key")`

#### Scenario: Org entitlement cache invalidated for all members on subscription update

- **WHEN** a Stripe `customer.subscription.updated` webhook is received for an OrgCustomer's stripe_customer_id
- **THEN** `cache.delete(f"entitlements:org:{org.pk}:{member.user_id}")` SHALL be called for every current org member
- **AND** this SHALL happen regardless of whether plan resolution succeeded

## Implementation Decisions

### Why a separate `apps/orgs/` Django app (not extending `apps/accounts/`)

All org code lives in `apps/api/apps/orgs/`. Keeping it separate mirrors the existing per-domain app separation (`accounts/`, `billing/`, `core/`) and makes `--with b2b` scaffolder removal clean: deleting `apps/orgs/` removes all org code without touching user identity logic in `accounts/`.

**Alternative rejected:** Adding org fields to the existing `Customer` or user models — this blurs user-identity concerns with team-management concerns and complicates B2B removal.

### Why `IsOrgMember` returns 404 (not 403) for non-members

Returning 403 would confirm to an attacker that the org exists. 404 gives no information about whether the org exists or whether the caller is blocked. This is an intentional security decision (org existence leakage prevention), not a REST purity choice.

**Important for tests:** Test assertions must expect 404 (not 403) when writing negative-path tests for non-members.

### Why `request.org` is set by the permission class

After resolving membership, `IsOrgMember`/`IsOrgAdmin` attaches the resolved `Organization` to `request.org`. Controllers and services downstream can access `request.org` without re-querying the database. This mirrors Django's `request.user` pattern.

### Why invitation default role is always `member`

Principle of least privilege. Invitees start as members; elevation to admin or owner is a separate explicit action. An invitation should not grant admin rights without a deliberate second step.

### Why `OrgCustomer` is a separate model (not an org FK on `Customer`)

`OrgCustomer(org=OneToOne, stripe_customer_id=...)` mirrors the shape of `Customer(user=OneToOne, stripe_customer_id=...)` exactly. Adding an org FK to `Customer` would blur user billing vs org billing and make queries ambiguous. Two parallel models is the cleaner design.

### Why org entitlement cache key is `entitlements:org:{org_pk}:{user_pk}`

The per-membership key (`org_pk` + `user_pk`) means org plan changes only invalidate org-context caches, not personal caches, and vice versa. A user who belongs to two orgs has two independent org entitlement cache entries. Consistent 300-second TTL with personal entitlements.

### Why org plan resolution lives in `apps/orgs/`, not `apps/billing/`

`_resolve_org_plan_id(org)` is in `apps/orgs/` to avoid circular imports. `apps/orgs/` imports from `apps/billing/` (one direction only). `has_org_feature()` calls `_resolve_org_plan_id()` first, then falls back to `_resolve_plan_id(user)` from billing. Both live in `apps/core/entitlements.py` as the stable public import path.
