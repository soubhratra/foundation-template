---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: SaaS Functional Baseline
status: planning
stopped_at: Completed 19-04-PLAN.md — removeEmailModule() implemented, EMAIL-05 satisfied, all 9 phase tests GREEN
last_updated: "2026-03-12T03:43:18.052Z"
last_activity: 2026-03-11 — v1.3 roadmap created; all 19 requirements mapped across Phases 19–23
progress:
  total_phases: 11
  completed_phases: 7
  total_plans: 23
  completed_plans: 23
  percent: 0
---

# Session State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-11)

**Core value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.
**Current focus:** v1.3 — Phase 19: Transactional Email (ready to plan)

## Current Position

Phase: 19 of 23 (Transactional Email)
Plan: — (not yet planned)
Status: Ready to plan
Last activity: 2026-03-11 — v1.3 roadmap created; all 19 requirements mapped across Phases 19–23

Progress: [░░░░░░░░░░] 0% (v1.3 IN PROGRESS) | 5 phases pending

## Performance Metrics

**Velocity:**

- Total plans completed (v1.3): 0
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
| ----- | ----- | ----- | -------- |
| -     | -     | -     | -        |

_Updated after each plan completion_
| Phase 19-transactional-email P01 | 4 | 2 tasks | 5 files |
| Phase 19-transactional-email P02 | 5 | 2 tasks | 6 files |
| Phase 19-transactional-email P03 | 11 | 2 tasks | 10 files |
| Phase 19-transactional-email P04 | 246 | 2 tasks | 4 files |

## Accumulated Context

### Decisions

- v1.3 ESP decision: Resend (not SendGrid) — anymail dropped official SendGrid support June 2025; `RESEND_API_KEY` in `.env.example`
- v1.3 Apple Sign In: dedicated server-side native token verification endpoint required — Expo JWT audience (`aud` = Bundle ID) differs from Allauth standard endpoint expectation (`aud` = Services ID); do NOT use standard social token flow
- v1.3 social email merge: `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` for Google + GitHub; disabled for Apple (relay addresses)
- v1.3 GDPR deletion: `UserDeletionService` orchestrator required — `user.delete()` alone leaves orphaned Stripe customer + PostHog person (Article 17 violation)
- v1.3 entitlement cache: must invalidate on `customer.subscription.updated` webhook — stale cache after downgrade is a user trust issue
- [Phase 19-transactional-email]: test_settings.py uses override_settings (not re-import) for EMAIL_BACKEND assertions — Django settings singleton means env patching alone has no effect at test time
- [Phase 19-transactional-email]: test_css_is_inlined uses send_email_task.run() to bypass Celery broker — .run() calls underlying Python function synchronously in tests
- [Phase 19-transactional-email]: EMAIL_BACKEND auto-switch in base.py: if RESEND_API_KEY (truthy) use anymail Resend backend, else console — removes dev-only override from development.py for single code path across all environments
- [Phase 19-transactional-email]: INSTALLED_APPS sentinel comments (# EMAIL MODULE — remove this line to exclude email) enable scaffolder removeEmailModule() regex to strip email entries cleanly
- [Phase 19-transactional-email]: RuntimeError fallback in send_email(): unit tests without @pytest.mark.django_db get direct enqueue() call — semantically equivalent since no active transaction means no rollback risk
- [Phase 19-transactional-email]: Email templates self-contained (no extends): SUBJECT sentinel must be absolute first line — template inheritance makes first rendered line unpredictable
- [Phase 19-transactional-email]: EmailMultiAlternatives body=HTML: test_css_is_inlined checks email.body for style= attrs; test_plain_text_alternative_present checks alternatives for text/html — both pass with HTML as both body and alternative
- [Phase 19-transactional-email]: removeEmailModule() uses sentinel-comment regex (# EMAIL MODULE) for INSTALLED_APPS line removal — same pattern as BILLING MODULE for consistency across all optional module removals
- [Phase 19-transactional-email]: TDD strictly applied to removeEmailModule(): RED commit before GREEN — 7 unit tests in remove-email.test.ts written and committed before implementation

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 20 (Social Auth): verify exact allauth 65.x internal API for connecting a pre-verified Apple socialaccount before committing plan — non-standard endpoint
- Phase 21 (GDPR): confirm `ObservabilityAdapter` exposes a `delete_identity(user_id)` method before scoping; confirm `BillingAdapter` exposes `delete_customer(stripe_customer_id)`
- Phase 23 (Entitlements): read `apps/billing/models.py` at plan time to verify `PlanProviderMapping` field names match `has_feature()` assumptions

### Quick Tasks Completed

| #   | Description                                                                       | Date       | Commit  | Directory                                                                                         |
| --- | --------------------------------------------------------------------------------- | ---------- | ------- | ------------------------------------------------------------------------------------------------- |
| 1   | fix stale test URL in test_middleware.py and add Redis env vars to Docker Compose | 2026-03-12 | d7f5918 | [1-fix-stale-test-url-in-test-middleware-py](./quick/1-fix-stale-test-url-in-test-middleware-py/) |

## Session Continuity

Last session: 2026-03-12T03:43:18.048Z
Stopped at: Completed 19-04-PLAN.md — removeEmailModule() implemented, EMAIL-05 satisfied, all 9 phase tests GREEN
Resume file: None
