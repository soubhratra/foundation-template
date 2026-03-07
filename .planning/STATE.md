---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Billing & Payments Module
current_phase: 9 of 12 (v1.1 phases 9–12)
current_plan: —
status: executing
stopped_at: Completed 09-billing-scaffold/09-01-PLAN.md
last_updated: "2026-03-07T22:09:33.841Z"
last_activity: 2026-03-07
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 3
  completed_plans: 2
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-07)

**Core value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.
**Current focus:** Phase 9 — Billing Scaffold (v1.1 start)

## Current Position

**Current Phase:** 9 of 12 (v1.1 phases 9–12)
**Current Plan:** —
**Status:** Ready to execute
**Last Activity:** 2026-03-07
**Last Activity Description:** Phase 9 planning complete — 3 plans written (09-01, 09-02, 09-03)

**Progress (v1.1):** [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity (v1.1):**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase (v1.1):**

| Phase | Plans | Total | Avg/Plan |
| ----- | ----- | ----- | -------- |
| -     | -     | -     | -        |

_Updated after each plan completion_
| Phase 09-billing-scaffold P02 | 18 | 3 tasks | 8 files |
| Phase 09-billing-scaffold P01 | 5min | 2 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting v1.1 work:

- [Roadmap v1.1]: No dj-stripe — breaks adapter pattern, adds ~40 User-coupled migrations, forces Django 5+ floor
- [Roadmap v1.1]: Webhook endpoint is a plain Django view (not Ninja controller) — raw body required for HMAC verification
- [Roadmap v1.1]: `PlanProviderMapping` table instead of `stripe_price_id` on Plan model — prevents provider coupling
- [Roadmap v1.1]: PDF generation always async via Celery task — WeasyPrint RSS leak requires task isolation
- [Phase 9]: PaymentAdapter is ABC (not Protocol) — explicit inheritance enforces contract at class definition
- [Phase 9]: Full adapter method set defined upfront (8 methods) — no stub-and-expand pattern
- [Phase 9]: All 5 models in 0001_initial.py — avoids second migration in Phase 10 for ProcessedWebhookEvent
- [Phase 9]: StripeAdapter uses stripe.StripeClient(api_key=...) — NOT stripe.api_key global (v14 pattern)
- [Phase 9]: Signal handler uses `if created:` guard — load-bearing, prevents duplicate Customer on User re-save
- [Phase 9]: Test stubs use pytest.importorskip — skip cleanly in Wave 0, run in Wave 1+
- [Phase 9]: pyproject.toml uses [dependency-groups] table (not [project.optional-dependencies])
- [Phase 9]: Test directory is apps/api/tests/billing/ (confirmed via codebase scan)
- [Phase 09-billing-scaffold]: Abstract record_usage parameter renamed from stripe_customer_id to customer_id — enforces zero provider coupling in PaymentAdapter interface
- [Phase 09-billing-scaffold]: signals.py created before makemigrations (Task 2 not Task 3) — BillingConfig.ready() triggers during django.setup() which runs during makemigrations
- [Phase 09-billing-scaffold]: importorskip + RuntimeError guard: Django RuntimeError (not ImportError) raised when billing model exists but app not registered — wrapped with try/except for correct Wave 0 skip behavior
- [Phase 09-billing-scaffold]: Settings-conditional test skips: BILLING_ADAPTER and STRIPE_SECRET_KEY tests guard with hasattr check rather than assert-only, enabling clean skips before Wave 1 settings are added

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 10]: Task queue (Celery vs Django-Q2 vs Huey) must be confirmed before Phase 10 — dispatch patterns differ
- [Phase 11]: Proration strategy decision needed before implementing upgrade/downgrade endpoints — mixing approaches causes `subscription_already_has_schedule` errors
- [Phase 12]: WeasyPrint version (`>=68.1,<69`) must be re-verified at install time before pinning

## Session Continuity

**Last Session:** 2026-03-07T22:09:33.838Z
**Stopped At:** Completed 09-billing-scaffold/09-01-PLAN.md
**Resume File:** None

**Next Action:** `/gsd:execute-phase 9`
