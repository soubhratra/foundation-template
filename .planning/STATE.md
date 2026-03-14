---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: B2B Module
status: planning
stopped_at: Completed 34-02-PLAN.md
last_updated: "2026-03-14T01:31:52.502Z"
last_activity: 2026-03-13 — v1.4 roadmap created; all 19 requirements mapped across Phases 26–31
progress:
  total_phases: 15
  completed_phases: 15
  total_plans: 48
  completed_plans: 48
  percent: 0
---

# Session State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.
**Current focus:** v1.4 B2B Module — Phase 26 ready to plan

## Current Position

Phase: 26 of 31 (Organization Model + Per-Org Billing)
Plan: — (not yet planned)
Status: Ready to plan
Last activity: 2026-03-13 — v1.4 roadmap created; all 19 requirements mapped across Phases 26–31

Progress: [░░░░░░░░░░] 0% (v1.4 IN PROGRESS) | 6 phases pending

## Performance Metrics

**Velocity:**

- Total plans completed (v1.4): 0
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
| ----- | ----- | ----- | -------- |
| -     | -     | -     | -        |

_Updated after each plan completion_
| Phase 26-organization-model-per-org-billing P01 | 277 | 3 tasks | 8 files |
| Phase 26-organization-model-per-org-billing P02 | 4 | 2 tasks | 7 files |
| Phase 26-organization-model-per-org-billing P03 | 8 | 1 tasks | 1 files |
| Phase 26-organization-model-per-org-billing P04 | 13 | 2 tasks | 6 files |
| Phase 26-organization-model-per-org-billing P05 | 4 | 2 tasks | 2 files |
| Phase 26-organization-model-per-org-billing P06 | 7 | 2 tasks | 4 files |
| Phase 27-outbound-webhooks P01 | 2 | 1 tasks | 7 files |
| Phase 27-outbound-webhooks P02 | 8 | 2 tasks | 12 files |
| Phase 27-outbound-webhooks P03 | 10 | 1 tasks | 7 files |
| Phase 27-outbound-webhooks P04 | 11 | 2 tasks | 3 files |
| Phase 28-api-key-authentication P01 | 2 | 2 tasks | 7 files |
| Phase 28-api-key-authentication P02 | 10 | 2 tasks | 7 files |
| Phase 28-api-key-authentication P03 | 18 | 2 tasks | 4 files |
| Phase 28-api-key-authentication P04 | 7 | 1 tasks | 3 files |
| Phase 29-audit-logging P01 | 3 | 2 tasks | 8 files |
| Phase 29-audit-logging P02 | 844 | 2 tasks | 14 files |
| Phase 29-audit-logging P03 | 848 | 2 tasks | 5 files |
| Phase 30-admin-backoffice P01 | 3 | 3 tasks | 5 files |
| Phase 30-admin-backoffice P02 | 7 | 2 tasks | 10 files |
| Phase 30-admin-backoffice P03 | 7 | 2 tasks | 6 files |
| Phase 31-cli-scaffolder-integration P01 | 2 | 1 tasks | 2 files |
| Phase 31-cli-scaffolder-integration P02 | 2 | 2 tasks | 5 files |
| Phase 31-cli-scaffolder-integration P03 | 5 | 2 tasks | 1 files |
| Phase 32-webhook-wiring-invite-url P01 | 4 | 2 tasks | 2 files |
| Phase 32-webhook-wiring-invite-url P02 | 8 | 2 tasks | 2 files |
| Phase 33-apikey-auth-example-endpoint P01 | 5 | 1 tasks | 1 files |
| Phase 33-apikey-auth-example-endpoint P02 | 10 | 2 tasks | 4 files |
| Phase 34-admin-audit-context-fixes P01 | 12 | 2 tasks | 4 files |
| Phase 34-admin-audit-context-fixes P02 | 25 | 2 tasks | 8 files |

## Accumulated Context

### Decisions

- v1.4 audit library: `django-pghistory` (not `django-pgaudit` — confirmed 404 on PyPI; not signal-based `django-auditlog` — triggers capture bulk ORM + raw SQL that signals miss)
- v1.4 admin theme: `django-unfold` (officially recommended by Django project April 2025; wraps standard admin, no model migrations)
- v1.4 impersonation: `django-hijack` 3.7.6 (not `django-impersonate` — lower adoption); verify Django version compat (3.7.6 lists 5.2 as supported)
- v1.4 org library: custom (not `django-organizations` — binary is_admin model incompatible with owner/admin/member; ships unused view layer)
- v1.4 api key library: custom (not `djangorestframework-api-key` — DRF-specific BasePermission, incompatible with Django Ninja Extra)
- v1.4 webhook library: custom (not `django-webhook` — pre-release 0.0.x, stale since Aug 2024)
- v1.4 billing atomicity: `OrgCustomer` + `_resolve_plan_id` update ships in Phase 26 (same phase as org model) — intermediate state where org model exists but entitlement resolution is still user-only is a correctness bug
- v1.4 API key security: SHA-256 hash only; `hmac.compare_digest` not `==`; raw key shown once at creation; no migration path from plaintext — must be correct from first commit (Phase 28)
- v1.4 Phase 30 risk: unfold + hijack compatibility is MEDIUM confidence — no single joint integration guide; run smoke test early before building out full admin registrations
- [Phase 26-organization-model-per-org-billing]: 26-01: Module-top-level imports in tests/orgs/ ensure immediate ImportError at collection time (clean RED state before orgs app exists)
- [Phase 26-organization-model-per-org-billing]: 26-01: Lazy imports in BILL-02 test stubs appended to existing files prevent breaking 10 passing tests while still defining RED stubs
- [Phase 26-organization-model-per-org-billing]: 26-02: Invitation field name is 'email' (not 'invited_email') — adapted to match 26-01 RED test contract; tests are authoritative
- [Phase 26-organization-model-per-org-billing]: 26-02: Organization.owner FK (SET_NULL) added as denormalized convenience field — 26-01 test stubs required it; Membership remains authoritative role source
- [Phase 26-organization-model-per-org-billing]: 26-03: IsOrgAdmin falls back to org_slug kwargs lookup when request.org is not a real Organization instance — required by test contract
- [Phase 26-organization-model-per-org-billing]: 26-03: Http404 used for both org-not-found and non-member in IsOrgMember to prevent org existence leakage
- [Phase 26-organization-model-per-org-billing]: 26-04: Service classes use @classmethod — callers invoke OrgService.create_org() without instantiation
- [Phase 26-organization-model-per-org-billing]: 26-04: \_resolve_org_plan_id returns None when no org-level Subscription exists — correct until Phase 27+ adds per-org billing
- [Phase 26-organization-model-per-org-billing]: 26-04: on_commit_immediately is non-autouse conftest fixture to avoid breaking rollback behavior tests
- [Phase 26-organization-model-per-org-billing]: 26-05: MemberOut.joined_at maps from membership.created_at; InviteOut.invited_email maps from invitation.email — field renaming done in controller return statement for API clarity
- [Phase 26-organization-model-per-org-billing]: 26-05: accept_invite endpoint has no IsAuthenticated gate — unauthenticated users receive session token + redirect URL matching InvitationService.accept() contract
- [Phase 26-organization-model-per-org-billing]: 26-05: No explicit orgs import in urls.py — auto_discover_controllers() imports apps.orgs.controllers because apps.orgs is in INSTALLED_APPS
- [Phase 26-organization-model-per-org-billing]: 26-06: OrgCustomer auto-created by post_save signal — tests must update existing OrgCustomer stripe_customer_id, not create a second one
- [Phase 26-organization-model-per-org-billing]: 26-06: Lazy imports inside \_try_invalidate_org_member_caches() body prevent circular imports between orgs models and billing tasks at Django startup
- [Phase 27-outbound-webhooks]: Module-level import in **init**.py causes ImportError at collection time — ensures all test files fail RED before any implementation exists
- [Phase 27-outbound-webhooks]: conftest.py uses lazy imports inside fixture bodies for WebhookEndpoint/WebhookDelivery to prevent double-import errors while keeping **init**.py as the RED trigger
- [Phase 27-outbound-webhooks]: WebhookDeliveryAttempt truncates response_body at save() so direct objects.create() test assertions work
- [Phase 27-outbound-webhooks]: fire_webhook_event() tests use transaction=True — default atomic() wrapper defers on_commit indefinitely
- [Phase 27-outbound-webhooks]: ruff.toml migration exclusion: auto-generated migration files have long lines that cannot be shortened
- [Phase 27-outbound-webhooks]: select_related('endpoint') not endpoint\_\_org in deliver_webhook — org accessed lazily only in circuit breaker path to avoid NPlusOneError on common success path
- [Phase 27-outbound-webhooks]: \_handle_terminal_failure is module-level (not task-internal) to enable direct testing without mocking full Celery retry chain
- [Phase 27-outbound-webhooks]: Email template at email/webhooks/endpoint_disabled.html (send_email_task resolves email/{template_name})
- [Phase 27-outbound-webhooks]: 27-04: No from **future** import annotations in ninja_extra controllers/schemas — deferred type eval breaks Pydantic QueryParams.model_rebuild() at runtime
- [Phase 27-outbound-webhooks]: 27-04: @paginate decorator incompatible with ninja_extra controller methods — use manual page/page_size query params + dict response instead
- [Phase 28-api-key-authentication]: Phase 28 RED trigger: **init**.py imports from apps.api_keys.models at module level — collection fails with ModuleNotFoundError until Wave 1 ships
- [Phase 28-api-key-authentication]: conftest.py fixtures use lazy imports inside fixture bodies — same pattern as tests/webhooks/conftest.py to avoid double-import conflicts
- [Phase 28-api-key-authentication]: @override_settings(RATELIMIT_ENABLE=True) required on all rate limit tests — global autouse fixture sets RATELIMIT_ENABLE=False which silences rate limit behavior
- [Phase 28-api-key-authentication]: checks.py created in Task 1 (not Task 2) — AppConfig.ready() imports checks at Django startup, blocking migration generation until checks.py exists
- [Phase 28-api-key-authentication]: Route paths use trailing slash ('/' not '') in APIKeyController — test contract URLs all have trailing slashes
- [Phase 28-api-key-authentication]: RequireScope raises PermissionDenied (not returns False) — forces 403 immediately without fallthrough
- [Phase 28-api-key-authentication]: Management controller (APIKeyController) uses session auth only; ApiKeyAuth is for product endpoints only
- [Phase 28-api-key-authentication]: get_usage(increment=True) is single enforcement+header counter — no header/enforcement drift possible
- [Phase 28-api-key-authentication]: ApiKeyRateLimitMiddleware wired inside B2B_START/B2B_END block, consistent with template B2B marker convention
- [Phase 29-audit-logging]: raise AssertionError() used for all RED stubs — ruff B011 flags assert False as removed by Python -O flag
- [Phase 29-audit-logging]: apps/audit/**init**.py intentionally empty — directory must exist for tests/**init**.py to produce ModuleNotFoundError (not FileNotFoundError)
- [Phase 29-audit-logging]: Lazy imports inside conftest.py fixture bodies follow same pattern as tests/webhooks/conftest.py — prevents double-import conflicts while **init**.py remains the RED trigger
- [Phase 29-audit-logging]: django-pghistory 3.9.2 installs django-pgtrigger 4.17.0 as transitive dep — no separate pgtrigger install needed
- [Phase 29-audit-logging]: pgtrigger hash= fields in migrations are SHA-1 checksums of trigger SQL — use pragma allowlist secret inline (not secrets.baseline) since migrations are excluded from ruff
- [Phase 29-audit-logging]: OrganizationEvent/MembershipEvent live in orgs app_label; APIKeyEvent in api_keys; WebhookEndpointEvent in webhooks — across() strings verified: orgs.OrganizationEvent, orgs.MembershipEvent, api_keys.APIKeyEvent, webhooks.WebhookEndpointEvent
- [Phase 29-audit-logging]: ninja_extra.QueryParams does not exist — AuditLogQueryParams uses ninja.Schema as base class, bound via Query(...) with # noqa: B008 in controller
- [Phase 29-audit-logging]: OrgAuditEvents proxy uses across() with positional string args for cross-model union across 4 event tables; encode_cursor operates on raw pgh_created_at/pgh_id (not schema fields)
- [Phase 29-audit-logging]: DB index on pghistory_context (metadata->>'org_id', created_at DESC, id DESC) deferred — recommend adding as RunSQL migration post-Wave 3
- [Phase 30-admin-backoffice]: 30-01: No **init**.py RED trigger for tests/admin/ — RED state achieved via lazy imports inside test bodies referencing not-yet-existing modules (unfold, apps.accounts.permissions, apps.audit.models.ImpersonationEvent, hijack)
- [Phase 30-admin-backoffice]: 30-01: AuditContextMiddleware.get_context() tested directly in hijack middleware test — avoids full request/response cycle, tests context logic in isolation
- [Phase 30-admin-backoffice]: 30-02: Migration numbered 0001 (not 0002) — audit app had no prior migrations directory; Django auto-numbered it correctly
- [Phase 30-admin-backoffice]: 30-02: AuditConfig.ready() uses try/except ImportError for hijack import — allows non-B2B scaffolds to remove hijack without breaking audit app startup
- [Phase 30-admin-backoffice]: 30-02: HijackUserMiddleware positioned after AuthenticationMiddleware and before allauth AccountMiddleware — required by django-hijack (needs auth user populated)
- [Phase 30-admin-backoffice]: 30-03: webhooks/admin.py readonly_fields uses signing_key + secret_hash (actual model field names), not 'secret' as plan specified — plan had wrong field name
- [Phase 30-admin-backoffice]: 30-03: audit/admin.py ImpersonationEventAdmin list_display uses hijacker_email/hijacked_email computed columns (not actor_email/model_name/object_id) — ImpersonationEvent has hijacker/hijacked FKs, not general audit log fields
- [Phase 31-cli-scaffolder-integration]: sys.executable used instead of 'python' literal in test_scaffold_with_b2b subprocess call — cross-env portability (avoids FileNotFoundError when 'python' not on PATH)
- [Phase 31-cli-scaffolder-integration]: test_scaffold_with_b2b runs manage.py check against real template source not tmp_path — full Django project tree required for system check
- [Phase 31-cli-scaffolder-integration]: parents[4] for PROJECT_ROOT in tests/scaffolder/ (not parents[3]) — test file is one directory deeper than root-level tests/
- [Phase 31-cli-scaffolder-integration]: B2B is opt-in via --with b2b flag (not opt-out); default scaffold excludes B2B — enterprise feature not needed in every project
- [Phase 31-cli-scaffolder-integration]: django-unfold NOT removed by removeB2BModule — admin theme is unconditional, not B2B-only
- [Phase 31-cli-scaffolder-integration]: stripMarkerBlocks uses dynamic globby import inside function body to avoid ESM circular dep issues in remove.ts
- [Phase Phase 31-cli-scaffolder-integration]: debug console.error removed from catch block — catch block uses only Clack p.log.error for clean styled output
- [Phase 32-webhook-wiring-invite-url]: Customer.objects.get_or_create(user=user) in billing webhook test — post_save signal auto-creates Customer for every User; Customer.objects.create() raises UniqueViolation
- [Phase 32-webhook-wiring-invite-url]: RED failures for billing test are AttributeError (fire_webhook_event not yet imported in tasks module) — valid RED state; patch target becomes valid after Plan 32-02 adds lazy import
- [Phase 32-webhook-wiring-invite-url]: fire_webhook_event imported at module level (not lazy) in services.py and tasks.py — required for patch('apps.orgs.services.fire_webhook_event') and patch('apps.billing.tasks.fire_webhook_event') test patterns
- [Phase 32-webhook-wiring-invite-url]: Module-level fire_webhook_event import placed inside B2B block in tasks.py — scaffolder strips whole blocks atomically, removing both import and helper function in non-B2B scaffolds
- [Phase 33-apikey-auth-example-endpoint]: 8 test methods (not 6 as stated in objective): includes test_invalid_key_returns_401 and test_no_auth_returns_401 as auth-failure sanity cases per done criteria
- [Phase 33-apikey-auth-example-endpoint]: ping route must be declared before /{key_id}/ in APIKeyController (static before parametric to avoid route shadowing)
- [Phase 33-apikey-auth-example-endpoint]: ApiKeyRateLimitMiddleware post-auth path: request.api_key set by Ninja inside view dispatch, middleware must check after get_response() for integration tests
- [Phase 34-admin-audit-context-fixes]: 34-01: OrgCustomerAdmin registered in apps/orgs/admin.py inside B2B markers with list_display=(org, stripe_customer_id, created_at); stripe_customer_id editable for staff corrections; Org Billing sidebar entry uses receipt icon (Material Symbols)
- [Phase 34-admin-audit-context-fixes]: APIKey.org FK is nullable (SET_NULL) — personal keys (org=None) are a valid use case, not an error state
- [Phase 34-admin-audit-context-fixes]: Service-layer audit_context() wrapping for /me/api-keys/ routes follows Phase 29 Celery task pattern — controllers own HTTP auth, services own domain mutations with audit context injection
- [Phase 34-admin-audit-context-fixes]: nplusone Profiler whitelist for APIKey.org: select_related is correct for production paths with org keys; false positive only fires in tests using personal-key fixtures (org_id=NULL, field never touched)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 30 (Admin Backoffice): Verify Django version in `apps/api/pyproject.toml` at plan time — `django-hijack` 3.7.6 lists Django 5.2 as supported; if on 5.0/5.1 plan a Django 5.2 upgrade as Phase 30 prerequisite
- Phase 30 (Admin Backoffice): Run unfold + hijack smoke test early — impersonate a user, verify banner renders inside unfold-themed admin and AuditLog.impersonator is populated; fall back to standalone hijack banner if incompatibility found
- Phase 28 (API Keys): Decide WebhookEndpoint.secret storage approach at plan time — plaintext write-only serializer (acceptable for MVP) vs. HMAC-hashed secret (more secure but prevents future UI display)

## Session Continuity

Last session: 2026-03-14T01:31:52.497Z
Stopped at: Completed 34-02-PLAN.md
Resume file: None
