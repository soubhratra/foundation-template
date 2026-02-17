# Phase 7: DevEx + CI/CD - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers automated quality enforcement and production deployment readiness:
- Pre-commit hooks enforce code standards locally before commits reach the repository
- GitHub Actions CI/CD validates all changes (linting, type checking, testing) across all three platforms (API, web, mobile)
- Production Dockerfiles enable deployment of Django API and Next.js web app
- Test infrastructure demonstrates comprehensive coverage across unit, integration, component, and E2E tests

**Out of scope for this phase:**
- Performance/load testing infrastructure (deferred - see below)
- Security/penetration testing tooling (deferred - see below)
- Deployment automation beyond Dockerfile creation (future phase)

</domain>

<decisions>
## Implementation Decisions

### Pre-commit Hook Enforcement

**Locked Decisions:**
- **Block all quality violations**: Commits must pass formatting (ruff, prettier), linting (ruff, eslint), and type checking (mypy, tsc)
  - *Rationale:* Comprehensive quality gate at commit time prevents technical debt from entering the codebase. All three dimensions (format, lint, types) catch different classes of issues - formatting catches style violations, linting catches code smells and potential bugs, type checking catches type safety issues. Blocking all ensures template demonstrates production-grade standards.

**Claude's Discretion:**
- Auto-fix behavior (whether hooks auto-fix formatting or just report errors)
  - *Context:* User wants all violations blocked but deferred the UX decision (auto-fix vs report-only) to Claude
  - *Consideration:* Balance developer convenience (auto-fix saves time) vs explicit control (report-only keeps developers aware of what changed)
- Bypass capability (whether `--no-verify` is allowed)
  - *Context:* User trusts Claude to decide if developers should be able to bypass hooks for WIP commits
  - *Consideration:* CI remains the ultimate quality gate, so bypass may be acceptable for local workflows
- Check scope (changed files only vs entire codebase)
  - *Context:* User deferred speed vs thoroughness tradeoff to Claude
  - *Consideration:* Pre-commit hooks should be fast (< 5 seconds) for good DX, but must be thorough enough to catch issues

### CI Job Parallelization & Caching

**Locked Decisions:**
- **Comprehensive caching strategy**: Cache dependencies (pnpm, uv), build outputs (turbo cache), and Docker layers
  - *Rationale:* Maximizes CI speed across all three optimization vectors. Dependency caching saves package installation time (major speedup on most runs). Turbo cache enables incremental builds (skip rebuilding unchanged apps). Docker layer caching accelerates image builds. Combined, these can reduce CI time from 10+ minutes to 2-3 minutes on typical changes.

**Claude's Discretion:**
- Job parallelization strategy (all jobs parallel vs sequential)
  - *Context:* User wants fast CI but deferred the specific execution model to Claude
  - *Consideration:* GitHub Actions supports matrix builds for parallelization; balance speed (parallel) vs clear error reporting (sequential)
- Fail-fast behavior (cancel remaining jobs on first failure vs run all)
  - *Context:* User trusts Claude to choose between saving CI minutes (fail-fast) vs comprehensive failure visibility (run all)
  - *Consideration:* Developers often prefer seeing all failures at once to fix multiple issues in one iteration
- CI trigger strategy (every push, PRs only, or main + PRs)
  - *Context:* User deferred trigger configuration to Claude
  - *Consideration:* Template should balance comprehensive validation (every push) vs CI minute consumption (PRs only)

### Test Coverage Expectations

**Locked Decisions:**
- **Comprehensive test coverage**: Template demonstrates production-ready testing, not minimal examples
  - *Rationale:* As a starter template, this sets the quality bar for projects built from it. Comprehensive coverage means developers inherit working examples of all test patterns they'll need. Shows best practices rather than "good enough to prove it works."
- **All four test categories**: Unit tests (pure logic), integration tests (API endpoints), component tests (UI), and E2E tests (full user flows)
  - *Rationale:* Each test type catches different classes of bugs:
    - *Unit tests:* Pure logic bugs in utilities, helpers, business logic functions
    - *Integration tests:* API contract violations, database interaction issues, auth flow bugs
    - *Component tests:* UI rendering bugs, user interaction issues, prop validation
    - *E2E tests:* Cross-system integration issues, complete user journey validation
  - Having all four means the template demonstrates the full testing pyramid - developers can see working examples of each pattern and understand when to use which approach.

**Claude's Discretion:**
- Coverage thresholds (enforce minimum % or track without enforcement)
  - *Context:* User wants comprehensive tests but deferred the enforcement mechanism to Claude
  - *Consideration:* Thresholds can be helpful quality guardrails but may be overly strict for a template (vs production app)
- Test data strategy (factories, fixtures, or mix)
  - *Context:* User trusts Claude to choose appropriate test data management
  - *Consideration:* Factories (factory_boy, faker) offer flexibility; fixtures offer predictability; mix may be best (factories for most, fixtures for specific scenarios)

### Production Docker Strategy

**Claude's Discretion:**
- Image size vs build speed optimization
  - *Context:* User deferred the optimization tradeoff to Claude
  - *Consideration:* Multi-stage builds can achieve both (reasonable size, reasonable speed). Template should demonstrate production-grade Dockerfiles, not necessarily the most aggressively optimized.
- Base image selection (Alpine, Debian slim, or full Debian)
  - *Context:* User trusts Claude to choose appropriate base images for Django API and Next.js web
  - *Consideration:* Alpine is smallest but can have compatibility issues (especially with Python wheels). Debian slim balances size and compatibility. Full Debian prioritizes compatibility over size.
- Security scanning integration (include vulnerability scanning or keep simple)
  - *Context:* User deferred security scanning decision to Claude
  - *Consideration:* Template should be production-ready, but security scanning adds CI complexity. Free tools like Trivy are available.
- Layer caching optimization (dependency-first ordering vs simple single-stage)
  - *Context:* User trusts Claude to optimize layer ordering for cache effectiveness
  - *Consideration:* Dependency-first ordering (COPY package.json, RUN install, COPY code) maximizes cache hits when code changes but deps don't. Standard Docker best practice.

</decisions>

<specifics>
## Specific Ideas

**Documentation Requirements:**
- All discretionary decisions should include brief justifications in documentation (README, comments)
- Decisions are "very important" and need clear context for future review
- Template users should understand WHY choices were made, not just WHAT was implemented

**Template Philosophy:**
- This is a production-ready starter template, not a minimal proof-of-concept
- Quality bar should reflect production standards (comprehensive testing, all quality gates)
- Demonstrate best practices rather than "just enough to work"

</specifics>

<deferred>
## Deferred Ideas

**Performance & Load Testing:**
- Document approach to performance/load testing at both app level (web/mobile) and API level
- Research and document free & open-source tools for load testing
- *Why deferred:* This is a distinct capability beyond the DevEx + CI/CD phase boundary. Could be its own phase or added to Phase 8 (CLI Scaffolder) as optional documentation.

**Security & Penetration Testing:**
- Document penetration testing approach for the stack
- Research and document free & open-source tools for security testing
- *Why deferred:* This is a distinct capability beyond the DevEx + CI/CD phase boundary. Security testing infrastructure (automated vulnerability scanning, pen testing frameworks) could be its own phase.

**Recommendation:** Consider these as potential Phase 7.1 (inserted) or post-Phase-8 additions if documentation-only. If implementing actual tooling/automation, they warrant full phases.

</deferred>

---

*Phase: 07-devex-ci-cd*
*Context gathered: 2026-02-17*
