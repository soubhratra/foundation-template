---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Observability & DevEx Hardening
status: planning
stopped_at: Completed 18-dev-time-quality-gates/18-02-PLAN.md
last_updated: "2026-03-11T23:44:29.505Z"
last_activity: 2026-03-11 — v1.2 roadmap created (phases 13–18)
progress:
  total_phases: 6
  completed_phases: 6
  total_plans: 19
  completed_plans: 19
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
| Phase 15-health-probes-celery-infrastructure P02 | 12 | 2 tasks | 6 files |
| Phase 15-health-probes-celery-infrastructure P03 | 4 | 2 tasks | 4 files |
| Phase 16-security-hardening P01 | 2 | 1 tasks | 1 files |
| Phase 16-security-hardening P02 | 5 | 2 tasks | 7 files |
| Phase 16-security-hardening P03 | 9 | 2 tasks | 6 files |
| Phase 17-dev-time-security-gates P01 | 5 | 1 tasks | 1 files |
| Phase 17-dev-time-security-gates P02 | 3 | 2 tasks | 4 files |
| Phase 17-dev-time-security-gates P03 | 15 | 2 tasks | 5 files |
| Phase 18-dev-time-quality-gates P01 | 1 | 1 tasks | 1 files |
| Phase 18-dev-time-quality-gates P03 | 2 | 2 tasks | 3 files |
| Phase 18-dev-time-quality-gates P02 | 525602 | 2 tasks | 5 files |

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
- [Phase 15-health-probes-celery-infrastructure]: Plain Django views (not Ninja) for health probes — probes must work even if Ninja app is misconfigured; health probes mounted before Ninja path to prevent URL shadowing
- [Phase 15-health-probes-celery-infrastructure]: Internal helpers (\_check_postgres, \_check_redis, \_check_celery, \_count_pending_migrations) extracted as module-level functions — Phase 15-01 RED test stubs mock these directly
- [Phase 15-health-probes-celery-infrastructure]: raise self.retry(...) from exc required — ruff B904 enforces exception chaining in except blocks for proper traceback context
- [Phase 15-health-probes-celery-infrastructure]: Flower is dev-only (docker-compose.yml only, not prod) per OBS-06; celery-worker added to dev compose so beat-dispatched tasks have a consumer
- [Phase 15-health-probes-celery-infrastructure]: DatabaseScheduler chosen over PersistentScheduler — DB-backed schedule allows runtime interval edits via admin without container restart
- [Phase 16-security-hardening]: [Phase 16-01]: pytest.fail() with RED reason strings used for all 9 security test stubs — cleaner FAILED output that identifies which plan implements each behavior
- [Phase 16-02]: AuthRateLimitMiddleware returns response directly (not raise Ratelimited()) — Django default Ratelimited handler returns 403 HTML, not 429 JSON
- [Phase 16-02]: RATELIMIT_FAIL_OPEN=True — auth availability prioritised over strict enforcement during Redis outages
- [Phase 16-02]: test_isolation_settings autouse fixture: LocMemCache + RATELIMIT_ENABLE=False for all tests; rate limit tests use override_settings per-test
- [Phase 16-03]: django-csp 4.0 CONTENT*SECURITY_POLICY dict API (not old CSP*\* flat settings); NONCE sentinels for per-request nonce injection in script-src, style-src
- [Phase 16-03]: HSTS in production.py only (not base.py) — local HTTP development would break; test requires secure=True + ALLOWED_HOSTS=['testserver'] to simulate HTTPS
- [Phase 16-03]: Next.js CSP uses unsafe-inline (static headers() function) — App Router hydration requires it; Django CSP uses nonces (different origin, no conflict)
- [Phase 17-dev-time-security-gates]: pytest.fail() with RED reason strings used for all 8 dev-gate test stubs — mirrors Phase 16-01 pattern; cleaner FAILED output identifies which plan implements each behavior
- [Phase 17-dev-time-security-gates]: Initial .secrets.baseline generated alongside detect-secrets hook (Rule 3 auto-fix) — hook exits with error 2 if baseline missing, blocking all commits
- [Phase 17-dev-time-security-gates]: [Phase 17-02]: Security audit steps placed in existing jobs (api/web) rather than separate security job — avoids overhead, co-located with dep installs
- [Phase 17-dev-time-security-gates]: detect-secrets baseline generated via user Python binary (~/Library/Python/3x/bin/detect-secrets) — pre-commit manages its own isolated env, not available via uv run
- [Phase 17-dev-time-security-gates]: [Phase 17-03]: DDT import placed inside if settings.DEBUG block in urls.py — prevents ImportError in CI where debug-toolbar is a dev-group dep not installed in test envs
- [Phase 17-dev-time-security-gates]: [Phase 17-03]: INTERNAL_IPS = ['127.0.0.1'] sufficient for DDT — default callback checks INTERNAL_IPS, no custom SHOW_TOOLBAR_CALLBACK needed for template use case
- [Phase 18-01]: pytest.fail() with RED reason strings used for all 6 quality-gate test stubs — cleaner FAILED output identifies which plan implements each behavior (mirrors Phase 16-01 and 17-01 pattern)
- [Phase 18-01]: Imports limited to pytest + pathlib.Path — no runtime deps since nplusone is not installed yet; file-level assertions deferred to Plan 18-02 GREEN phase
- [Phase 18-03]: schemathesis CLI tool (schemathesis run) used — not the pytest plugin; CI job runs against live Django dev server with separate postgres DB (foundation_schemathesis) to avoid state pollution
- [Phase 18-03]: --hypothesis-max-examples 30 for CI cost control; --max-response-time 5000 for performance regression detection; billing/webhook + health + auth paths excluded from fuzzing
- [Phase 18-02]: nplusone 1.0.0 has no pytest plugin — implemented allow_lazy_load and \_LazyLoadProfiler directly in conftest.py; synthetic nplusone.ext.pytest module registered in sys.modules for import compatibility
- [Phase 18-02]: \_LazyLoadProfiler activates LazyListener only (not EagerListener) — avoids false positives on unused eager loads in billing tests that correctly use select_related
- [Phase 18-02]: LazyListener requires explicit blinker signal disconnect in **exit** — teardown() is a no-op; without explicit disconnect, handlers fire in subsequent tests causing spurious NPlusOneError

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 17 (Dev-Time Security Gates) has no hard dependency on phases 13–16 — can be executed in parallel if context allows
- Phase 14 (ObservabilityAdapter) depends on Phase 13 middleware setup being in place for Django request context

## Session Continuity

Last session: 2026-03-11T23:40:23.925Z
Stopped at: Completed 18-dev-time-quality-gates/18-02-PLAN.md
Resume file: None
