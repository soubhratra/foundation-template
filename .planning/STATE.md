---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: B2B Module
status: planning
stopped_at: Completed 27-03-PLAN.md (deliver_webhook task, circuit breaker, cleanup, email templates)
last_updated: "2026-03-13T11:39:53.091Z"
last_activity: 2026-03-13 — v1.4 roadmap created; all 19 requirements mapped across Phases 26–31
progress:
  total_phases: 12
  completed_phases: 7
  total_plans: 29
  completed_plans: 28
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

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 30 (Admin Backoffice): Verify Django version in `apps/api/pyproject.toml` at plan time — `django-hijack` 3.7.6 lists Django 5.2 as supported; if on 5.0/5.1 plan a Django 5.2 upgrade as Phase 30 prerequisite
- Phase 30 (Admin Backoffice): Run unfold + hijack smoke test early — impersonate a user, verify banner renders inside unfold-themed admin and AuditLog.impersonator is populated; fall back to standalone hijack banner if incompatibility found
- Phase 28 (API Keys): Decide WebhookEndpoint.secret storage approach at plan time — plaintext write-only serializer (acceptable for MVP) vs. HMAC-hashed secret (more secure but prevents future UI display)

## Session Continuity

Last session: 2026-03-13T11:39:53.087Z
Stopped at: Completed 27-03-PLAN.md (deliver_webhook task, circuit breaker, cleanup, email templates)
Resume file: None
