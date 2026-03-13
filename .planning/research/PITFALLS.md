# Pitfalls Research: v1.4 B2B Module

**Domain:** Adding B2B infrastructure (organizations, outbound webhooks, API keys, audit logging, admin backoffice) to an existing Django + Next.js SaaS system
**Researched:** 2026-03-12
**Confidence:** MEDIUM-HIGH (GitHub issues, official docs, and community post-mortems corroborate most claims. django-pgaudit-specific claims drawn from pgaudit upstream GitHub issues. Webhook anti-patterns drawn from webhookantipatterns.com and hookdeck guides. Django Ninja multi-auth behavior drawn from official docs.)

> **Note:** This file supersedes the v1.3 pitfalls document for v1.4 work. The v1.3 pitfalls (Apple Sign In token mismatch, GDPR cascade gaps, etc.) remain valid for those features. This file focuses exclusively on the five B2B features in v1.4.

---

## Critical Pitfalls

Mistakes that cause security holes, data loss, broken auth flows, or mandatory rewrites.

---

### Pitfall 1: Billing Attachment Point — User vs. Organization

**What goes wrong:**
The existing `Customer` model has a `OneToOneField` on `User`. When adding `Organization`-level billing, naive approaches either duplicate billing logic (one Customer per user, one per org) or silently continue billing the individual user while the org feature is active. This means the entitlement system (`has_feature(user, key)`) still reads from `user.billing_customer` — which is the _personal_ subscription, not the org subscription. Org admins who cancel their personal plan lose org-level entitlements even when the org has an active subscription.

**Why it happens:**
The billing system was deliberately designed as user-centric (v1.1). The entitlement cache key is `entitlements:{user.pk}`. When org billing is added later, developers add an `OrgCustomer` model without updating `_resolve_plan_id`, leaving it reading the wrong subscription.

**How to avoid:**
Make `_resolve_plan_id` org-aware. For users who belong to an organization with an active subscription, resolve entitlements from the org's plan, not the user's personal plan. Introduce a single resolution path:

1. If user belongs to an active org → use org's `plan_id`.
2. Otherwise → fall back to user's personal `Customer` subscription.

Update the `customer.subscription.updated` webhook handler to invalidate `entitlements:{user.pk}` for **all org members** when the org subscription changes, not just the user who owns the Customer record.

**Warning signs:**

- `has_feature(user, "api_access")` returns `False` for an org member whose org plan includes it.
- Entitlement cache invalidation on Stripe webhook only affects one user per org.
- `_resolve_plan_id` still resolves via `user.billing_customer` unconditionally.

**Phase to address:**
Organization model phase (first B2B phase). Do not ship the `Organization` model without updating the entitlement resolution path in the same phase.

---

### Pitfall 2: API Key Auth — Plaintext Storage or Naive Hash Comparison

**What goes wrong:**
API keys stored as plaintext in the database are fully exposed in any SQL dump, backup file, or DB read access incident. Keys stored with a reversible hash (MD5, SHA-1, SHA-256 without prefix/salt) are brute-forceable offline. String comparison with `==` instead of `hmac.compare_digest` is vulnerable to timing attacks — an attacker can distinguish "wrong key prefix" from "wrong key suffix" based on response time, enabling incremental key reconstruction.

**Why it happens:**
Developers reach for `models.CharField` + `uuid.uuid4()` as a quick API key implementation. The temptation to do `APIKey.objects.get(key=request_key)` is natural — it matches how session tokens work — but a database lookup on plaintext or unhashed values is a direct data exposure path.

**How to avoid:**
Use the `djangorestframework-api-key` pattern as reference, even if not using DRF:

- Generate a key in two parts: `{prefix}.{secret}` where prefix is 8 chars and secret is 32 chars.
- Store only `PBKDF2(secret)` (or `hashlib.scrypt` with a per-key salt) in the database. Never store the raw secret.
- At authentication time: look up by prefix (fast index scan), then compare using `hmac.compare_digest(stored_hash, hash(incoming_secret))`.
- Return the full raw key to the user only once at creation time. Never return it again.

**Warning signs:**

- `APIKey.objects.filter(key=raw_key)` anywhere in the codebase.
- API key stored in a single CharField without a separate `prefix` column.
- Comparison using `==` or Python's `str.__eq__` against key material.

**Phase to address:**
API key phase. This is a security invariant — the hashing scheme must be correct from the first commit. No migration path exists from plaintext to hashed keys without invalidating all existing keys.

---

### Pitfall 3: Outbound Webhooks — Fire-and-Forget Celery Task

**What goes wrong:**
The most common implementation sends the HTTP request directly inside the Celery task, with a single attempt. If the recipient's endpoint is down, times out, or returns a 5xx, the event is silently lost. There is no retry state, no delivery log, no circuit breaker. Dead endpoints continue to receive retries indefinitely, consuming worker threads and filling the queue. At scale this starves queue workers for live customers.

**Why it happens:**
The existing Stripe webhook implementation (inbound) is a simple `process_stripe_event.delay()` pattern. Developers mirror this for outbound: `deliver_webhook.delay(endpoint_url, payload)`. The inbound case is idempotent and handled by Stripe's retry logic. The outbound case has no external retry mechanism — the system must provide it.

**How to avoid:**
Model delivery state explicitly:

- `WebhookDelivery` table with columns: `attempt_number`, `status` (`pending`/`success`/`failed`/`exhausted`), `response_status_code`, `response_body`, `next_retry_at`, `delivered_at`.
- Use Celery's `countdown` or `eta` for exponential backoff with jitter: `min(2 ** attempt * base_delay + random.uniform(0, 1), max_delay)`.
- After N consecutive failures (recommend 10, configurable), set endpoint `is_active=False` and send an email notification to the org admin.
- A separate Celery Beat task sweeps for `pending` deliveries whose `next_retry_at` has passed and re-enqueues them (DLQ pattern using the DB as the queue).

**Warning signs:**

- No `WebhookDelivery` or equivalent delivery-log model.
- Celery task for outbound webhook has no `max_retries` and no `retry` call.
- `WebhookEndpoint.is_active` does not exist or is never set to `False` automatically.

**Phase to address:**
Outbound webhook phase. The delivery log model must be in the initial migration — retrofitting it requires backfilling historical delivery status which is impossible.

---

### Pitfall 4: Outbound Webhooks — Unversioned Payload Schema

**What goes wrong:**
Payload structure is shipped to all registered endpoints. When the payload schema changes (field renamed, nested object added), all existing integrations break simultaneously with no warning. Recipients who built parsers against `payload.user.id` get `undefined` when it's refactored to `payload.actor.user_id`. This is the outbound webhook equivalent of a breaking API change, but with no versioning header and no deprecation window.

**Why it happens:**
Internal schema changes feel like implementation details. Developers rename a model field, run `makemigrations`, regenerate TypeScript types — and forget that the webhook payload is a public API contract for external integrations.

**How to avoid:**

- Include a `webhook_version` field in every payload (e.g. `"v1"`).
- Include a `Content-Type: application/json` header and an `X-Webhook-Version: 1` header on every delivery.
- Treat the payload schema as a versioned public API contract from day one, even if there's only one consumer at launch.
- Document the payload schema in `openspec/specs/` as part of shipping the feature.

**Warning signs:**

- Webhook payload constructed by serializing a Django model instance directly (`model_to_dict(instance)`).
- No `version` field in the payload.
- Payload schema not documented in any spec file.

**Phase to address:**
Outbound webhook phase. Cannot be bolted on later without breaking existing integrations.

---

### Pitfall 5: API Key Auth — Auth Bypass via Ninja's Auth Resolution Order

**What goes wrong:**
Django Ninja evaluates the `auth=[]` list in order and succeeds on the first match. If `APIKeyAuth` is placed before `SessionAuth` in the list on a shared endpoint, a user with a valid session cookie and an invalid or expired API key may get rejected — Ninja tries `APIKeyAuth` first, it fails, and depending on implementation may short-circuit rather than fall through to `SessionAuth`. Conversely, if you intend API-key-only endpoints (programmatic access, no browser sessions), placing `SessionAuth` first allows a logged-in browser tab to hit those endpoints without any key, bypassing scope enforcement.

**Why it happens:**
The Ninja multi-auth pattern is documented as "first authenticator in the list to return a non-`None` user wins," but the failure path is not: if an authenticator returns `None` (unauthenticated), Ninja tries the next one. If it raises an exception, it stops. Custom `APIKeyAuth` implementations often `raise AuthenticationError` on a malformed key header instead of returning `None`, which prevents the fallback to session auth.

**How to avoid:**

- `APIKeyAuth.authenticate()` must return `None` (not raise) when the `Authorization: Bearer` header is absent, so the fallback to session auth fires.
- `APIKeyAuth.authenticate()` must raise `HttpError(401)` only when a key is present but invalid.
- API-key-only endpoints (e.g. programmatic data access) must list only `APIKeyAuth`, not `[APIKeyAuth, SessionAuth]`.
- Write an explicit integration test: authenticated session user hitting an API-key-only endpoint without a key must get 401, not 200.

**Warning signs:**

- `APIKeyAuth.authenticate()` raises `AuthenticationError` unconditionally when header is missing.
- Endpoints that should require API keys also list `SessionAuth` in their `auth=` parameter.
- No test covering "session-authenticated user hitting API-key-only endpoint."

**Phase to address:**
API key phase. Auth behavior must be tested exhaustively before the Ninja auth backend is wired up globally.

---

### Pitfall 6: Organization Membership — Tenant Isolation Not Applied to Existing Models

**What goes wrong:**
A new `Organization` model is added. Membership is added. Per-org roles are added. But existing models — `Customer`, `Subscription`, `AuditLog`, `WebhookEndpoint`, `APIKey` — are not scoped to the org. A user who belongs to two orgs can query billing history across both orgs. An `APIKey` created in Org A is visible to users in Org B if they know the key prefix. This is not a theoretical risk: it is the default behavior when org-aware filtering is not applied at the ORM query level.

**Why it happens:**
The "add org FK" migration is done, but queryset-level org filtering is considered "something to do in permissions." Permissions check membership at the HTTP layer but the underlying service methods (`BillingService`, `WebhookService`) do not filter by org. Any service method that can be called with `user` and `org_id` as separate arguments is vulnerable if the caller does not validate that the user belongs to the org.

**How to avoid:**

- Every service method that operates on org-scoped resources must accept `org` as a required parameter and validate `Membership.objects.filter(user=user, org=org).exists()` before any ORM query.
- Never accept `org_id` as a raw integer from request input and pass it directly to a filter. Resolve the org object through the membership check first.
- Add a custom `OrgQuerySet` manager that requires `.for_org(org)` to be called before any filter, raising `AssertionError` if skipped — enforces correct usage at development time.

**Warning signs:**

- Service methods that take `user` and `org_id` as separate parameters and do `Model.objects.filter(org_id=org_id)` without verifying membership.
- `APIKey.objects.filter(user=request.user)` — no org scope.
- Integration tests that create two orgs and verify cross-org data isolation are missing.

**Phase to address:**
Organization model phase. This is the foundational invariant — all subsequent B2B features inherit the org isolation pattern. Getting it wrong here requires auditing and patching every model that was added after the fact.

---

### Pitfall 7: django-hijack — Impersonation Sessions Leak into Production Data

**What goes wrong:**
When a support agent impersonates a user via django-hijack, all actions taken in that session are attributed to the impersonated user. If the agent accidentally submits a form, triggers a webhook, modifies billing, or creates an audit log entry, those actions appear indistinguishable from actions taken by the real user — unless impersonation context is explicitly propagated.

This has two failure modes:

1. Support agents cause unintended data mutations they cannot undo.
2. Audit logs show the impersonated user as the actor, making it impossible to retrospectively distinguish impersonation-driven actions from real user actions.

**Why it happens:**
django-hijack replaces `request.user` with the impersonated user. The Django session is now fully authenticated as that user. The audit log middleware captures `request.user.pk` as the actor. Nothing flags the request as an impersonation session unless additional middleware tracks it.

**How to avoid:**

- Store the impersonator's user ID in the session (`HIJACK_PERMISSION_CHECK` is not enough — you need it in the audit trail too).
- Add a middleware that reads `session["hijack_history"]` (django-hijack's session key) and injects `is_impersonation=True` + `impersonator_id=...` into the request for the audit log middleware to consume.
- `AuditLog` model must have a nullable `impersonator` FK in addition to `actor` FK.
- Block impersonation of superusers or staff from non-superuser support agents (django-hijack's `HIJACK_PERMISSION_CHECK` must enforce this).
- Never enable hijack in production without an `is_impersonating` banner visible in every page of the admin — django-hijack inserts this by default; do not disable it.

**Warning signs:**

- `AuditLog` has only one `actor` field with no `impersonator` field.
- `HIJACK_INSERT_BEFORE` is set to `None` (disables the impersonation banner).
- Hijack-initiated actions appear in the user-facing activity log that end users can see.

**Phase to address:**
Admin backoffice phase. The `AuditLog` model schema must include `impersonator` before django-hijack is enabled. Schema changes after the fact require a migration that cannot backfill historical impersonation sessions.

---

## Technical Debt Patterns

Shortcuts that seem reasonable now but create long-term problems.

| Shortcut                                                                 | Immediate Benefit             | Long-term Cost                                                                                         | When Acceptable                                                                             |
| ------------------------------------------------------------------------ | ----------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Attach billing `Customer` to `User` for orgs too (per-user billing only) | Avoids org billing complexity | Entire B2B billing model needs rewrite when orgs need shared invoices                                  | Never — commit to org-level billing from the start if B2B is in scope                       |
| Store API keys in plaintext CharField                                    | Trivially implementable       | All existing keys must be invalidated and reissued when hashing is added; no migration path            | Never                                                                                       |
| Deliver outbound webhooks synchronously in the request cycle             | Simpler code path             | Slow endpoints block API responses; timeouts cause data inconsistency                                  | Never for production; acceptable in dev/test only                                           |
| Skip delivery log — just retry on Celery task failure                    | No extra model needed         | Zero visibility into delivery failures; can't replay; dead endpoints discovered only by user complaint | Never                                                                                       |
| Use `pgaudit` at `log` level only, no Django-side `AuditLog` model       | Zero app-layer overhead       | Audit data locked in Postgres server logs, unqueryable, not exportable in GDPR requests                | Acceptable only for compliance-only auditing, not user-facing activity logs                 |
| Single `actor` FK on `AuditLog` without `impersonator`                   | Simpler model                 | Impersonation actions indistinguishable from real user actions in audit trail                          | Never if django-hijack is used                                                              |
| `WebhookEndpoint.secret` stored in plaintext                             | Easy to display in UI         | Key rotation requires invalidating all deliveries; exposed in DB dumps                                 | Acceptable in MVP with `secret` marked as write-only in API responses — never return in GET |

---

## Integration Gotchas

Common mistakes when integrating the B2B features with the existing system.

| Integration                          | Common Mistake                                                                   | Correct Approach                                                                                                                                            |
| ------------------------------------ | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Billing → Organization               | Keep `Customer.user` OneToOne, add separate `OrgCustomer`                        | Add `org` nullable FK to `Customer` or create `OrgBillingProfile`; update `_resolve_plan_id` to check org first                                             |
| Entitlements → Organization          | Cache key remains `entitlements:{user.pk}`                                       | Invalidate entitlement cache for all org members on `customer.subscription.updated`; resolve org plan first                                                 |
| API key auth → Ninja Extra           | Place `APIKeyAuth` in NinjaExtraAPI `auth=` globally                             | Register as a per-router or per-endpoint auth; global registration applies to all routes including allauth headless routes                                  |
| django-hijack → allauth sessions     | Hijack replaces `request.user` but allauth session data may conflict             | Test allauth's `_get_user_from_session` path under hijack to ensure no session corruption                                                                   |
| pgaudit → existing migrations        | Enable `pgaudit` extension after existing tables exist                           | `pgaudit` operates at the Postgres log level; no Django migration needed, but `shared_preload_libraries = 'pgaudit'` must be set before `docker compose up` |
| AuditLog model → Celery tasks        | Async tasks have no `request.user` — actor is `None` in audit log                | Pass `actor_id` explicitly to all async tasks; never rely on thread-local request context inside Celery                                                     |
| django-unfold → existing ModelAdmin  | Install `unfold` and add to `INSTALLED_APPS` before existing admin registrations | `unfold` must appear before `django.contrib.admin` in `INSTALLED_APPS` — wrong order causes `AttributeError` on `AdminSite`                                 |
| Outbound webhook HMAC → key rotation | Same secret used for all deliveries forever                                      | Store secret per endpoint, support rotation by keeping old secret valid for a 5-minute overlap window                                                       |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap                                      | Symptoms                                                                                               | Prevention                                                                                                                            | When It Breaks                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `AuditLog` table without partitioning     | `SELECT * FROM auditlog WHERE actor_id=X ORDER BY created_at DESC` takes seconds                       | Partition by month from the start using `django-postgres-extra` or Postgres native range partitioning                                 | ~500K rows; sooner with full-row auditing enabled |
| pgaudit DDL + DML audit at database level | Postgres log files fill disk in minutes under load                                                     | Scope pgaudit to `log = write` only; exclude `READ` class unless compliance requires it; never enable in dev without log rotation     | Any write-heavy load test                         |
| Outbound webhook delivery queue unbounded | Celery queue depth grows without bound for dead endpoints; workers starved                             | Implement circuit-breaker: auto-disable endpoint after 10 consecutive failures                                                        | ~100 dead endpoints each with a pending backlog   |
| API key lookup by full key value          | `SELECT * FROM apikey WHERE key='...'` full-table scan                                                 | Store `prefix` (first 8 chars) in a separate indexed column; look up by prefix, compare hash                                          | ~10K API keys                                     |
| Org membership check on every request     | N+1 membership queries; `Membership.objects.filter(user=user, org=org).exists()` on every service call | Cache membership status in Redis with TTL tied to membership model's `post_save` signal                                               | High-frequency API clients (programmatic access)  |
| AuditLog write on every model `.save()`   | Writes double for every object update; high-write models (e.g. `WebhookDelivery`) generate noise       | Use `pgaudit` or application-level audit selectively — only `Organization`, `Membership`, `APIKey`, `BillingProfile` are audit-worthy | Any model with frequent background updates        |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake                                                      | Risk                                                                                          | Prevention                                                                                                                                                           |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API key returned in GET responses after creation             | Key exposure in browser history, server logs, CDN logs                                        | Return raw key only once (POST /api-keys response body); all subsequent reads return only prefix + masked key                                                        |
| Webhook delivery logs store full request body                | Sensitive customer data exposed in DB for every delivery attempt                              | Store only response status code + truncated response body (first 512 bytes); hash the payload if full body is needed for replay                                      |
| Org-level impersonation via API key                          | An API key created in Org A could be used to impersonate Org B if scope validation is missing | Validate `APIKey.org == request_org` at every endpoint; key scopes must include org FK                                                                               |
| `django-hijack` hijack of superuser accounts                 | Support agent gains full system access including other agents' accounts                       | `HIJACK_PERMISSION_CHECK` must forbid hijacking `is_staff=True` or `is_superuser=True` users; enforce in a pytest test                                               |
| Org admin role escalation                                    | An `org:member` role member modifies their own membership to `org:admin`                      | Membership role changes must be restricted to current `org:admin` members; the API endpoint for membership update must validate the requester's role in the same org |
| HMAC secret for outbound webhooks exposed in admin list view | Attacker with Django admin read access forges webhook payloads                                | `WebhookEndpoint.secret` must be write-only in all serializers; use `PasswordInput` widget in django-unfold admin                                                    |
| Audit log not immutable                                      | Malicious actor with DB write access modifies audit trail                                     | Use Postgres-level `REVOKE UPDATE, DELETE ON auditlog TO app_user`; application DB role should not have UPDATE/DELETE on audit tables                                |

---

## UX Pitfalls

Common user experience mistakes in the B2B domain.

| Pitfall                                                | User Impact                                                                                   | Better Approach                                                                                                       |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| No webhook delivery status UI                          | Developers can't tell if their endpoint is receiving events; they file support tickets        | Show last 10 delivery attempts with status code and timestamp in the settings UI                                      |
| API key created but not copyable                       | User creates key, navigates away, can never retrieve it — must delete and recreate            | Show key in a dismissable modal at creation time with an explicit "I've copied this" acknowledgement before dismissal |
| Org invitation via email but no invitation link expiry | Invitation links work forever; stale invitations sent to former employees grant access        | Expire invitation tokens after 72 hours; show expiry time in the invitation email                                     |
| Webhook endpoint URL not validated at save time        | User enters a typo; first delivery attempt fails; user discovers it only after missing events | Send a test ping (POST with `event_type: "webhook.test"`) immediately after endpoint creation and surface the result  |
| Audit log shows internal IDs not human-readable names  | Log entry reads `actor=42, target=17` — meaningless to support agents                         | Join actor and target FKs at query time; return `actor.email` and `target.__str__()` in API responses                 |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but have missing critical pieces.

- [ ] **Organization model:** FK on `Customer`/`Subscription` updated — verify `_resolve_plan_id` reads org plan, not personal plan, for org members.
- [ ] **Organization model:** Cross-org isolation test exists — create two orgs, verify user from Org A cannot read Org B's resources via the API.
- [ ] **API key auth:** Key stored as hash — verify `SELECT key FROM apikeys` returns only hash prefixes, never raw key material.
- [ ] **API key auth:** Timing-safe comparison in use — verify `hmac.compare_digest` is used, not `==`.
- [ ] **API key auth:** Key returned only at creation — verify `GET /api-keys/{id}` returns prefix only, never full key.
- [ ] **Outbound webhooks:** Delivery log model exists — verify `WebhookDelivery` table is in first migration.
- [ ] **Outbound webhooks:** Dead endpoint circuit breaker — verify endpoint is auto-disabled after N consecutive failures and org admin is notified.
- [ ] **Outbound webhooks:** Payload includes `webhook_version` field — verify in delivery log's stored payload.
- [ ] **Outbound webhooks:** HMAC signature on every delivery — verify `X-Webhook-Signature` header present in delivery log.
- [ ] **Audit log:** `impersonator` FK on `AuditLog` — verify column exists before enabling django-hijack.
- [ ] **Audit log:** Async task actor attribution — verify Celery tasks pass `actor_id` explicitly; no `request.user` references inside tasks.
- [ ] **django-hijack:** Impersonation of staff/superuser is forbidden — verify pytest test for this invariant exists.
- [ ] **django-unfold:** Appears before `django.contrib.admin` in `INSTALLED_APPS` — verify `manage.py check` passes with both installed.
- [ ] **pgaudit:** `shared_preload_libraries = 'pgaudit'` set in `postgresql.conf` / Docker Compose env — verify `CREATE EXTENSION pgaudit` does not raise at startup.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall                                    | Recovery Cost | Recovery Steps                                                                                                                                                              |
| ------------------------------------------ | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Billing attached to user instead of org    | HIGH          | Add org FK to Customer; write data migration to move existing Customers to a "personal org" for each user; update `_resolve_plan_id`; invalidate all entitlement cache keys |
| API keys stored in plaintext               | HIGH          | Force-invalidate all existing keys; send "you must regenerate your API key" email to all key holders; re-implement with hashing in new migration                            |
| Missing delivery log for outbound webhooks | MEDIUM        | Add `WebhookDelivery` model; future deliveries are logged; historical data is unrecoverable — document as known gap                                                         |
| AuditLog missing impersonator column       | MEDIUM        | Add nullable `impersonator` FK migration; all historical records have `impersonator=NULL` (indistinguishable from "no impersonation"); inform support team                  |
| Cross-org data leak discovered post-ship   | HIGH          | Audit all API endpoints for missing org scope filter; add missing filters; notify affected customers per GDPR Article 33 if personal data was exposed                       |
| pgaudit performance degradation            | LOW           | `SET pgaudit.log = 'none'` at session level for batch jobs; or narrow `pgaudit.log_relation` to specific tables only; change takes effect without restart                   |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall                                     | Prevention Phase          | Verification                                                                                                        |
| ------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Billing attachment to user not org          | Phase: Organization model | `_resolve_plan_id` test covers org member; entitlement cache invalidated for all org members on subscription update |
| Tenant isolation gaps                       | Phase: Organization model | Integration test: two orgs, cross-org resource access returns 403                                                   |
| API key plaintext storage                   | Phase: API key auth       | `SELECT key FROM apikeys` returns only prefix + hash; no raw key in DB                                              |
| Timing attack on key comparison             | Phase: API key auth       | Code review: `hmac.compare_digest` present in authenticate path                                                     |
| Auth bypass via Ninja auth resolution order | Phase: API key auth       | Integration test: session user without key hitting key-only endpoint returns 401                                    |
| Outbound webhook fire-and-forget            | Phase: Outbound webhooks  | `WebhookDelivery` table populated with every attempt; dead endpoint auto-disabled test                              |
| Unversioned webhook payload                 | Phase: Outbound webhooks  | `webhook_version` field present in all delivery log payloads; spec document exists                                  |
| Impersonation session leaks to audit log    | Phase: Admin backoffice   | AuditLog has `impersonator` column; impersonation-driven actions tagged correctly in test                           |
| django-unfold INSTALLED_APPS order          | Phase: Admin backoffice   | `manage.py check` passes in CI                                                                                      |
| pgaudit DDL log volume                      | Phase: Audit logging      | pgaudit scoped to `write` only; no `read` class in `pgaudit.log` setting                                            |
| AuditLog table bloat                        | Phase: Audit logging      | AuditLog has a `created_at` index; partitioning strategy documented even if not implemented in v1.4                 |

---

## Sources

- [webhook anti-patterns catalog](https://webhookantipatterns.com/)
- [pgaudit performance degradation under high insert load — GitHub issue #300](https://github.com/pgaudit/pgaudit/issues/300)
- [pgaudit extension removal issues — GitHub issue #246](https://github.com/pgaudit/pgaudit/issues/246)
- [Django Ninja authentication — multiple auth backends](https://django-ninja.dev/guides/authentication/)
- [Django Ninja Extra authentication](https://eadwincode.github.io/django-ninja-extra/tutorial/authentication/)
- [django-hijack security documentation](https://django-hijack.readthedocs.io/en/latest/security/)
- [Hookdeck — outbound webhook retry best practices](https://hookdeck.com/outpost/guides/outbound-webhook-retry-best-practices)
- [audit logging with postgres partitioning](https://elephas.io/audit-logging-with-postgres-partitioning/)
- [Django multi-tenancy isolation failure modes — TestDriven.io](https://testdriven.io/blog/django-multi-tenant/)
- [API security in Django — timing attack patterns](https://dev.to/topunix/api-security-in-django-approaches-trade-offs-and-best-practices-nk4)
- [CVE-2025-13473 — Django timing standardization in check_password](https://github.com/django/django/commit/6dc23508f3395e1254c315084c7334ef81c4c09a)
- [Django Ninja rate limiting — Redis cache backend requirement](https://eadwincode.github.io/django-ninja-extra/tutorial/throttling/)
- [Stripe billing for multi-entity business](https://docs.stripe.com/billing/multi-entity-business)

---

_Pitfalls research for: v1.4 B2B Module (organizations, outbound webhooks, API keys, audit logging, django-unfold + django-hijack admin)_
_Researched: 2026-03-12_
