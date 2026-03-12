## 1. Verify Delta Specs Against Shipped Code

- [x] 1.1 Verify `specs/observability/spec.md` matches `apps/core/logging.py`, `apps/core/tracing.py`, `apps/core/observability.py`, and `apps/providers.tsx` / `apps/mobile/app/_layout.tsx`
- [x] 1.2 Verify `specs/health-probes/spec.md` matches `apps/core/health.py` and `config/urls.py` health route registrations
- [x] 1.3 Verify `specs/security/spec.md` (rate limiting, CSP headers, Redis cache/session) matches `apps/core/ratelimit.py`, `apps/core/middleware.py`, and `config/settings/base.py` CACHES + SESSION config
- [x] 1.4 Verify `specs/devex-ci/spec.md` (detect-secrets, bandit, nplusone, schemathesis, commitlint, C90) matches `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `pyproject.toml`, and `apps/api/tests/conftest.py`
- [x] 1.5 Verify `specs/background-tasks/spec.md` (celery-beat with DatabaseScheduler, Flower, example periodic task) matches `docker-compose.yml`, `config/celery.py`, and `config/settings/base.py` CELERY_BEAT_SCHEDULE
- [x] 1.6 Verify `specs/docker-infra/spec.md` (Jaeger, CACHE_REDIS_URL/SESSION_REDIS_URL, celery-beat/flower services) matches `docker-compose.yml` and `.env.example`

## 2. Archive Delta Specs to Main Specs

- [ ] 2.1 Run `/opsx:archive gsd-milestone-12-sync` to merge delta specs into `openspec/specs/` and archive the change
- [ ] 2.2 Confirm `openspec/specs/observability/spec.md` exists after archive (new capability)
- [ ] 2.3 Confirm `openspec/specs/health-probes/spec.md` exists after archive (new capability)
- [ ] 2.4 Confirm `openspec/specs/security/spec.md` includes the new rate limiting, headers, and Redis backend requirements
- [ ] 2.5 Confirm `openspec/specs/devex-ci/spec.md` includes all six new quality gate requirements
- [ ] 2.6 Confirm `openspec/specs/background-tasks/spec.md` reflects always-on celery-worker and new celery-beat/Flower/example task requirements
- [ ] 2.7 Confirm `openspec/specs/docker-infra/spec.md` reflects Jaeger and Redis DB split requirements

## 3. Documentation Cleanup

- [x] 3.1 Add `pre-commit install --hook-type commit-msg` as an explicit step in `DEV_SETUP.md` so the commitlint commit-msg hook is activated after cloning
- [x] 3.2 Make mobile PostHog host configurable: update `apps/mobile/app/_layout.tsx` to read `EXPO_PUBLIC_POSTHOG_HOST` env var with `eu.i.posthog.com` as default (fixes hardcoded EU host)
- [x] 3.3 Add `EXPO_PUBLIC_POSTHOG_HOST` to `apps/mobile/.env.example` with a comment explaining US vs EU PostHog regions

## 4. Known Gaps (Deferred to v1.3)

- [ ] 4.1 Track schemathesis Redis service gap: CI `schemathesis` job has no `redis` service — cache/session middleware degrades silently. Add `redis` to the job's `services:` block in `.github/workflows/ci.yml`
- [ ] 4.2 Track Nyquist validation debt: all 6 v1.2 phase VALIDATION.md files have `nyquist_compliant: false`; Phases 15 and 18 are missing VALIDATION.md entirely — run `/gsd:validate-phase` on each before v1.3 planning
