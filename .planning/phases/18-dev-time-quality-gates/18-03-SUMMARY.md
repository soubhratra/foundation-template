---
phase: 18-dev-time-quality-gates
plan: "03"
subsystem: ci
tags: [schemathesis, api-fuzzing, contract-testing, ci, quality-gates]
dependency_graph:
  requires: []
  provides: [schemathesis-ci-job, api-contract-fuzzing]
  affects: [.github/workflows/ci.yml, apps/api/pyproject.toml]
tech_stack:
  added: [schemathesis==4.12.0]
  patterns: [property-based-api-fuzzing, live-server-ci-testing]
key_files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - apps/api/pyproject.toml
    - apps/api/uv.lock
decisions:
  - schemathesis CLI tool (schemathesis run) used — not the pytest plugin (@schema.parametrize); CI job runs against live Django dev server, not pytest fixtures
  - Separate postgres DB (foundation_schemathesis) for schemathesis job — avoids state pollution with api job's foundation_test DB since schemathesis creates/modifies real DB rows
  - --checks all enables not_a_server_error + status_code_conformance + content_type_conformance + response_schema_conformance — covers all contract violation categories
  - --hypothesis-max-examples 30 balances CI cost with coverage (default 100 is too slow for template-level checks)
  - --max-response-time 5000 catches accidental blocking calls or slow ORM queries introduced by new endpoints
  - Excluded paths billing/webhook (requires Stripe signature), health (returns 503 without Redis/Celery in CI), auth (allauth CSRF session flows cause false positives)
metrics:
  duration_min: 2
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_modified: 3
---

# Phase 18 Plan 03: Schemathesis API Contract Fuzzing CI Summary

**One-liner:** Property-based API contract fuzzing via schemathesis CLI against live Django dev server as a standalone fourth CI job.

## What Was Built

Added schemathesis as a CI quality gate that fuzzes every API endpoint against the live OpenAPI spec served by a Django test server. The job is independent of the pytest suite — it validates API contracts and catches 5xx responses using property-based test generation.

### Files Modified

- `.github/workflows/ci.yml` — Added `schemathesis` as a fourth top-level job alongside `api`, `web`, `mobile`
- `apps/api/pyproject.toml` — Added `schemathesis>=3.39` to `[dependency-groups].dev`
- `apps/api/uv.lock` — Updated with schemathesis 4.12.0 and 17 transitive dependencies

## Task Commits

| Task | Name                                        | Commit  | Files                                     |
| ---- | ------------------------------------------- | ------- | ----------------------------------------- |
| 1    | Add schemathesis to pyproject.toml dev deps | dcefcec | apps/api/pyproject.toml, apps/api/uv.lock |
| 2    | Add schemathesis CI job to ci.yml           | d637ba4 | .github/workflows/ci.yml                  |

## CI Job Design

The `schemathesis` job in ci.yml:

1. Spins up postgres 16 with a dedicated `foundation_schemathesis` database
2. Installs Python 3.12 + uv + all dev dependencies
3. Runs Django migrations against the schemathesis DB
4. Starts `manage.py runserver 8000` in the background
5. Polls `http://127.0.0.1:8000/api/openapi.json` with wget (up to 30 attempts, 2s delay each)
6. Runs `schemathesis run` with:
   - `--checks all` (not_a_server_error, status_code_conformance, content_type_conformance, response_schema_conformance)
   - `--exclude-path /api/billing/webhook/` (requires valid Stripe signature)
   - `--exclude-path "/api/health/"` (returns 503 without Redis/Celery in CI)
   - `--exclude-path "/api/v1/auth/"` (allauth CSRF session flows cause false positives)
   - `--max-response-time 5000` (catches blocking calls / slow queries)
   - `--hypothesis-max-examples 30` (CI cost control, down from 100 default)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `.github/workflows/ci.yml` exists and contains `schemathesis` job
- `apps/api/pyproject.toml` contains `schemathesis>=3.39` in dev group
- YAML parses without errors: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` exits 0
- `uv run schemathesis --version` exits 0 and prints `schemathesis, version 4.12.0`
- Commits dcefcec and d637ba4 exist in git log
