---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Observability & DevEx Hardening
status: planning
stopped_at: Completed 15-01-PLAN.md
last_updated: "2026-03-11T19:55:44.465Z"
last_activity: 2026-03-11 — v1.2 roadmap created (phases 13–18)
progress:
  total_phases: 6
  completed_phases: 2
  total_plans: 10
  completed_plans: 8
  percent: 0
---

# Session State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-11)

**Core value:** A new SaaS product goes from zero to running full-stack app (web + mobile + API + auth) in under 5 minutes with one command.
**Current focus:** v1.2 — Observability & DevEx Hardening (Phase 13 of 18)

## Current Position

Phase: 13 of 18 (Structured Logging + Distributed Tracing)
Plan: — of — in current phase
Status: Ready to plan
Last activity: 2026-03-11 — v1.2 roadmap created (phases 13–18)

Progress: [░░░░░░░░░░] 0% (v1.2) | Phases 1–12 complete (v1.0 + v1.1)

## Performance Metrics

**Velocity:**

- Total plans completed (v1.2): 0
- Average duration: — min
- Total execution time: — hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
| ----- | ----- | ----- | -------- |
| -     | -     | -     | -        |

_Updated after each plan completion_
| Phase 13-structured-logging-distributed-tracing P01 | 7 | 2 tasks | 6 files |
| Phase 13-structured-logging-distributed-tracing P02 | 12 | 2 tasks | 5 files |
| Phase 13-structured-logging-distributed-tracing P03 | 9 | 2 tasks | 6 files |
| Phase 14-observability-adapter P01 | 3 | 2 tasks | 2 files |
| Phase 14-observability-adapter P03 | 3 | 2 tasks | 5 files |
| Phase 14-observability-adapter P04 | 11 | 2 tasks | 3 files |
| Phase 14-observability-adapter P02 | 4 | 2 tasks | 6 files |
| Phase 15-health-probes-celery-infrastructure P01 | 92 | 2 tasks | 4 files |

## Accumulated Context

### Decisions

- v1.2 key decision: PostHog over Sentry — single SDK covers errors + analytics + feature flags + session replay; adapter pattern keeps it swappable (see PROJECT.md)
- v1.2 key decision: ObservabilityAdapter ABC mirrors PaymentAdapter pattern — PostHogAdapter default, NoOpAdapter for tests, swappable via one Django setting
- [Phase 13-01]: Install structlog + opentelemetry packages as runtime deps — middleware and logging modules import them in production Django
- [Phase 13-01]: Wave 0 TDD: all test stubs created in RED state before implementation begins — 10 tests across 3 files covering OBS-01 and OBS-02
- [Phase 13-02]: LOGGING dict placed inline in base.py using \_structlog alias; ConsoleRenderer dev / JSONRenderer prod automatic via DEBUG
- [Phase 13-02]: OTel trace_id/span_id fields omitted (not null) when no span active — clean log events for parsers
- [Phase 13-02]: DJANGO_STRUCTLOG_CELERY_ENABLED=True + OTEL_EXPORTER_OTLP_ENDPOINT added now to prepare Plan 13-03 landing zone
- [Phase 13-03]: configure_otel() is a no-op when OTEL_EXPORTER_OTLP_ENDPOINT absent — OTLPSpanExporter imported lazily to avoid ~100ms import overhead in CI/dev without Jaeger
- [Phase 13-03]: CeleryInstrumentor().instrument() called in worker_process_init signal (after prefork) — BatchSpanProcessor threads survive fork boundary; weak=False prevents GC
- [Phase 13-03]: DjangoStructLogInitStep registered in celery.py here (Plan 13-03) — co-located with other Celery startup config as structlog context propagation infrastructure
- [Phase 14-observability-adapter]: Deferred import pattern (import inside test function body) over top-level try/except — produces cleaner per-test failure messages in RED/GREEN TDD cycle
- [Phase 14-observability-adapter]: Scaffolder removal test mirrors test_scaffolder_billing_removal.py: subprocess + inline ESM node --input-type=module targeting dist/remove.js, no TTY required
- [Phase 14-observability-adapter]: PostHogProvider outermost in both apps — inner tracker components need usePostHog() hook available inside provider tree
- [Phase 14-observability-adapter]: capture_pageview: false mandatory in Next.js App Router + manual PostHogPageView — SDK built-in tracking misses client-side navigations
- [Phase 14-observability-adapter]: autocapture.captureScreens: false in Expo — Expo Router incompatible with PostHog useNavigationState screen autocapture (crashes on launch)
- [Phase 14-observability-adapter]: String-based indexOf/slice used for multi-line JSX tag removal in removeObservability() — regex with /m flag + repeated group caused catastrophic backtracking; string approach is O(n) and deterministic
- [Phase 14-observability-adapter]: posthog in main [project.dependencies] (not optional group) — runtime dep; NoOpAdapter handles absent key at runtime via settings, not at install time
- [Phase 14-observability-adapter]: process_exception returns None (not re-raise) — Django propagates exception naturally; re-raise causes duplicate processing
- [Phase 14-observability-adapter]: task_failure signal connected in CoreConfig.ready() with weak=False — PostHogAdapter creates fresh client per call so no pre-fork thread issue
- [Phase 15-health-probes-celery-infrastructure]: django-celery-beat and flower placed in [project.dependencies] not dev group — both need runtime presence (beat needs migrations + AppConfig, flower runs as standalone process)
- [Phase 15-health-probes-celery-infrastructure]: \_check_postgres, \_count_pending_migrations, \_do_work mocked as internal helpers — drives exact interface Plans 15-02 and 15-03 must implement

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 17 (Dev-Time Security Gates) has no hard dependency on phases 13–16 — can be executed in parallel if context allows
- Phase 14 (ObservabilityAdapter) depends on Phase 13 middleware setup being in place for Django request context

## Session Continuity

Last session: 2026-03-11T19:55:44.461Z
Stopped at: Completed 15-01-PLAN.md
Resume file: None
