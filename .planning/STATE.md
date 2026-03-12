---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: SaaS Functional Baseline
status: in_progress
stopped_at: Roadmap created — Phase 19 ready to plan
last_updated: "2026-03-11T00:00:00.000Z"
last_activity: "2026-03-11 — v1.3 roadmap written, Phase 19 ready to plan"
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
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

## Accumulated Context

### Decisions

- v1.3 ESP decision: Resend (not SendGrid) — anymail dropped official SendGrid support June 2025; `RESEND_API_KEY` in `.env.example`
- v1.3 Apple Sign In: dedicated server-side native token verification endpoint required — Expo JWT audience (`aud` = Bundle ID) differs from Allauth standard endpoint expectation (`aud` = Services ID); do NOT use standard social token flow
- v1.3 social email merge: `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT=True` for Google + GitHub; disabled for Apple (relay addresses)
- v1.3 GDPR deletion: `UserDeletionService` orchestrator required — `user.delete()` alone leaves orphaned Stripe customer + PostHog person (Article 17 violation)
- v1.3 entitlement cache: must invalidate on `customer.subscription.updated` webhook — stale cache after downgrade is a user trust issue

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

Last session: 2026-03-11T00:00:00.000Z
Stopped at: v1.3 roadmap written — ready to run `/gsd:plan-phase 19`
Resume file: None
