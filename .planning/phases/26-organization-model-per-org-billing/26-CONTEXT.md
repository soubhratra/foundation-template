# Phase 26: Organization Model + Per-Org Billing - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Products can model teams — users belong to organizations with explicit roles, invite teammates by email, and billing entitlements resolve at the org level before falling back to personal plans.

Scope: Organization + Membership models, role enforcement, invitation flow (token delivery + accept), ownership transfer, OrgCustomer model, per-org Stripe billing, `has_org_feature()` entitlement utility.

Not in scope: Outbound webhooks (Phase 27), API keys (Phase 28), audit logging (Phase 29), admin backoffice (Phase 30).

</domain>

<decisions>
## Implementation Decisions

### Module structure

- All org code lives in a new Django app: `apps/api/apps/orgs/`
  - `models.py` — Organization, Membership, Invitation, OrgCustomer
  - `schemas.py` — Request/response schemas
  - `controllers.py` — OrgController, MembershipController, InvitationController
  - `services.py` — OrgService, MembershipService, InvitationService
  - `permissions.py` — IsOrgAdmin, IsOrgMember permission classes
  - `migrations/` — Django migrations
- B2B_START/B2B_END markers isolate the entire `apps/orgs/` app for `--with b2b` scaffolder flag
- **Reason for new app:** Mirrors existing billing/accounts/core separation; makes --without b2b removal clean; accounts/ stays user-identity-only

### OrgCustomer model

- `OrgCustomer` is a **separate model in `apps/orgs/`** with a `OneToOne` to `Organization` and its own `stripe_customer_id`
- Mirrors the existing `Customer(user=OneToOne)` shape exactly — parallel structure for org billing
- `billing/` references `OrgCustomer` via FK only; no circular imports
- **Not:** adding an org FK to the existing `Customer` model — that would blur user billing vs org billing semantics

### Invitation flow

- **Token delivery:** URL token in email — link format `/accept-invite?token=xxx`
  - Token sent via existing `EmailAdapter` (Resend default, ConsoleAdapter in dev)
  - Token stored in `Invitation` model with 72-hour expiry
  - Token bound to invited email — validated on accept

- **Existing user accepting invite:** If user is already logged in with matching email, invite is accepted immediately on link click — no confirmation screen. Redirect to org dashboard.

- **New user accepting invite:** Token survives signup — token stored in session before redirect to signup. After signup completes, token is consumed and user is added to org automatically. One action for the user.

- **Email mismatch:** Token is bound to invited email. If logged-in user's email does not match → reject with HTTP 400 `{"detail": "This invitation was sent to a different email address."}`. No invite forwarding allowed.

- **Default role on accept:** Member role always. Admin access granted separately via role assignment endpoint. Principle of least privilege.

### Org permission class design

- `IsOrgAdmin` and `IsOrgMember` are **Ninja Extra permission classes** (`BasePermission`) — same pattern as `RequireRole("admin")` from Phase 22
- **Org resolution:** Permission class extracts `org_slug` from `request.resolver_match.kwargs` — endpoints are at `/api/v1/org/{org_slug}/...`
- **Attaching org to request:** After resolving and validating membership, the permission class sets `request.org = organization` — available to all downstream controllers and services without re-querying (same pattern as `request.user`)
- **Response codes:**
  - User not a member of the org at all → **404** (org doesn't exist from their perspective — avoids leaking org existence)
  - User is a member but lacks the required role → **403**
- Compose as: `permissions=[IsAuthenticated, IsOrgMember]` or `permissions=[IsAuthenticated, IsOrgAdmin]` at controller or route level

### has_org_feature() API shape

- **Signature:** `has_org_feature(user, org, key: str) -> bool`
  - Checks org subscription first; falls back to personal plan (`has_feature(user, key)`) if no active org subscription
  - Returns `True` if billing is not installed (same billing-absent fallback as `has_feature`)
- **Location:** `apps/core/entitlements.py` — same file as `has_feature()`, one stable import path for all entitlement checks
- **Org plan resolution:** Separate `_resolve_org_plan_id(org)` function in `apps/orgs/` (not in billing/); `has_org_feature()` calls it first; falls back to `_resolve_plan_id(user)` from `billing/`. No circular import: orgs/ → billing/ (one direction only)

### Entitlement cache design for org entitlements

- **Cache key:** `entitlements:org:{org_pk}:{user_pk}` — per-membership key
  - Separate from personal entitlement cache (`entitlements:{user_pk}`)
  - Org plan change doesn't blow personal caches; personal plan change doesn't affect org caches
- **Cache TTL:** 300 seconds (consistent with personal entitlement TTL)
- **Invalidation on org subscription update:** Iterate `Membership.objects.filter(org=org)` and call `cache.delete(f"entitlements:org:{org.pk}:{m.user_id}")` for each member
  - Triggered in the same `_handle_subscription_updated` webhook handler path (extended for OrgCustomer's stripe_customer_id)
  - Acceptable N-deletes for typical team sizes

### Claude's Discretion

- Exact slug uniqueness validation (globally unique vs case-insensitive unique)
- Invitation resend logic (whether resending re-uses same token or issues new one)
- Pagination style for member listings (follow existing pagination patterns in codebase)
- Whether `OrgController` and `MembershipController` are separate classes or one controller
- Exact ownership transfer: whether previous owner's role becomes admin or member

</decisions>

<specifics>
## Specific Ideas

- Permission class sets `request.org` after resolving — controllers never need to call `Organization.objects.get(slug=...)` themselves. Same philosophy as `request.user` — resolved once at the boundary, used everywhere inside.
- The `has_org_feature(user, org, key)` signature is intentional: even though org subscription is checked first, the user is needed for the personal plan fallback path. Caller always has both (request.user and request.org).
- `OrgCustomer` mirrors `Customer` in structure — this makes per-org Stripe billing feel identical to per-user billing from the billing module's perspective.

</specifics>

<code_context>

## Existing Code Insights

### Reusable Assets

- `apps/accounts/permissions.py` (`RequireRole`): Direct template for `IsOrgAdmin`/`IsOrgMember` — same `BasePermission` shape, same `PermissionDenied` → 403 error flow
- `apps/core/entitlements.py` (`has_feature`): Template for `has_org_feature()` — ImportError fallback, same TTL, same `cache.get/set` pattern
- `apps/billing/entitlements.py` (`_resolve_plan_id`, `_flags_for_plan`): Called by `has_org_feature()` for personal plan fallback — do not modify, just call
- `apps/billing/tasks.py` (`_handle_subscription_updated`): Extend to handle `OrgCustomer.stripe_customer_id` lookups + trigger org-level cache invalidation
- `apps/billing/models.py` (`Customer`, `Subscription`): Structural template for `OrgCustomer` and potential `OrgSubscription`
- `EmailAdapter` (notifications app): Send invitation emails via existing adapter — ConsoleAdapter in dev, Resend in prod

### Established Patterns

- Django app per domain: accounts/, billing/, core/, notifications/ — orgs/ follows same structure
- Permission classes: `permissions=[IsAuthenticated, RequireRole("admin")]` — org permissions compose the same way
- Webhook handlers: private `_handle_*` functions called from `process_stripe_event` Celery task — extend this for org subscription events
- Cache-aside pattern: `cache.get → cache.set` with `ENTITLEMENT_CACHE_TTL = 300` — org entitlements follow same pattern
- Services thin controllers: all business logic in `services.py`, controllers stay thin

### Integration Points

- `apps/api/config/settings/base.py`: Register `apps.orgs` in `INSTALLED_APPS` (inside B2B_START/B2B_END markers)
- `apps/api/config/urls.py`: Register OrgController (and related controllers) alongside existing controllers
- `apps/core/entitlements.py`: Add `has_org_feature()` function
- `apps/billing/tasks.py`: Extend `_handle_subscription_updated` to detect OrgCustomer and invalidate org member caches
- `create-foundation-app` CLI: Add `--with b2b` flag; B2B_START/B2B_END markers throughout `apps/orgs/` registration points

</code_context>

<deferred>
## Deferred Ideas

- Per-org SSO enforcement — requires SSO infrastructure; out of scope for v1.4
- Sub-organizations / org hierarchy — future phase; ORG-F02
- Custom roles beyond owner/admin/member — future phase; ORG-F01
- Org-level audit log — Phase 29 (requires all B2B models to exist first)
- Org admin backoffice views — Phase 30

</deferred>

---

_Phase: 26-organization-model-per-org-billing_
_Context gathered: 2026-03-12_
