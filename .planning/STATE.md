---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: SaaS Functional Baseline
status: planning
stopped_at: Completed 23-feature-entitlements-23-03-PLAN.md
last_updated: "2026-03-12T22:38:23.891Z"
last_activity: 2026-03-11 — v1.3 roadmap created; all 19 requirements mapped across Phases 19–23
progress:
  total_phases: 11
  completed_phases: 11
  total_plans: 39
  completed_plans: 39
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
| Phase 20-social-auth P01 | 9 | 2 tasks | 5 files |
| Phase 20-social-auth P02 | 5 | 2 tasks | 3 files |
| Phase 20-social-auth P03 | 18 | 2 tasks | 2 files |
| Phase 20-social-auth P04 | 3 | 2 tasks | 5 files |
| Phase 20-social-auth P05 | 6 | 1 tasks | 4 files |
| Phase 20-social-auth P06 | 8 | 2 tasks | 3 files |
| Phase 21-gdpr-baseline P01 | 285 | 2 tasks | 3 files |
| Phase 21-gdpr-baseline P02 | 25 | 2 tasks | 9 files |
| Phase 21-gdpr-baseline P03 | 3 | 2 tasks | 4 files |
| Phase 21-gdpr-baseline P04 | 4 | 2 tasks | 4 files |
| Phase 22-rbac P01 | 252 | 1 tasks | 2 files |
| Phase 22-rbac P02 | 525 | 2 tasks | 3 files |
| Phase 22-rbac P03 | 6 | 2 tasks | 3 files |
| Phase 23-feature-entitlements P01 | 4 | 2 tasks | 2 files |
| Phase 23-feature-entitlements P02 | 3 | 2 tasks | 7 files |
| Phase 23-feature-entitlements P03 | 4 | 1 tasks | 2 files |

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
- [Phase 20-social-auth]: Per-test import gate pattern: pytest.fail() inside test body prevents collection ERRORs that block other test files
- [Phase 20-social-auth]: \_configure_social_providers import path: config.settings.base (not apps.api.config...) — pytest rootdir is apps/api with python_paths=['.']
- [Phase 20-social-auth]: Google and GitHub registration requires both client_id AND secret — not just id alone
- [Phase 20-social-auth]: bool() wrapping of super().can_authenticate_by_email() ensures consistent True/False return type — allauth returns raw provider setting value which is MagicMock in unit tests
- [Phase 20-social-auth]: APPLE_PRIVATE_KEY base64 decode has graceful fallback to raw string — covers test PEM values and production base64-encoded keys
- [Phase 20-social-auth]: JWKS cache-bust-on-InvalidSignatureError: delete cache and retry once — handles Apple key rotation and test isolation (same kid, different test RSA key pairs)
- [Phase 20-social-auth]: AppleSignInController calls django_login() before JWT issuance — allauth JWTTokenStrategy requires request.session.session_key; falls back to jwt_internal.create_access_token() directly when SessionAwareJWTTokenStrategy returns None
- [Phase 20-social-auth]: NEXT_PUBLIC_GOOGLE_ENABLED / NEXT_PUBLIC_GITHUB_ENABLED evaluated at module scope for tree-shaking; SocialButtons returns null (not empty JSX) when no provider enabled; Apple Sign In absent from web UI (iOS-only); SOCIAL AUTH MODULE sentinel comment enables scaffolder removeModule() detection
- [Phase 20-social-auth]: Use useAuthContext() for token storage after Apple Sign In — useAuth() does not expose setTokens; correct field names are accessToken/refreshToken not access/refresh
- [Phase 20-social-auth]: expo-apple-authentication must be explicitly installed even in Expo 52 managed workflow — not auto-included; use npx expo install for correct version resolution
- [Phase 20-social-auth]: Env removal three-pass strategy: fenced block + comment-line + per-var regex covering all line forms — required because real .env.example has comment-form references
- [Phase 20-social-auth]: SocialButtons JSX removal uses broad pattern to match inline return statements not just standalone element lines
- [Phase 21-gdpr-baseline]: billing signal auto-creates Customer on user save — test fixtures must use get_or_create then update stripe_customer_id (not create directly)
- [Phase 21-gdpr-baseline]: import gate pattern (pytest.fail inside try/except ImportError) chosen for GDPR test stubs — gives actionable messages pointing to exact class/file to implement
- [Phase 21-gdpr-baseline]: Alias-import pattern for Celery task patchability: import get_adapter as PaymentAdapter so tests can patch apps.accounts.tasks.PaymentAdapter while production calls get_adapter()
- [Phase 21-gdpr-baseline]: GDPR export plan_id is None — Subscription model stores stripe_subscription_id not internal plan_id; exposing Stripe ID would violate no-Stripe-IDs requirement
- [Phase 21-gdpr-baseline]: conftest force_login patch scoped to tests/accounts/ via session fixture — patches ninja.testing.TestClient with ninja_extra.testing.TestClient for ControllerBase support
- [Phase 21-gdpr-baseline]: posthog.init() moved out of providers.tsx into CookieConsentBanner — PostHogProvider wrapper stays but init is consent-gated (GDPR-03)
- [Phase 21-gdpr-baseline]: deleteAccountAction uses direct fetch (not createApiClient) — DELETE /api/v1/account/ not in generated OpenAPI client; raw fetch with cookie forwarding matches createUpstreamFetcher pattern
- [Phase 21-gdpr-baseline]: DangerZone session clear uses useAuth().logout.mutate() — calls DELETE /api/v1/auth/browser/v1/auth/session, same path as header Sign Out button
- [Phase 22-rbac]: Inline helper functions for admin_user/member_user in test bodies — fixture-level Group.DoesNotExist produces ERROR not FAIL; helpers catch DoesNotExist and call pytest.fail() for readable RED output
- [Phase 22-rbac]: RequireRole returns False from has_permission (not raise PermissionDenied) — ninja_extra converts False to HttpError 403, TestClient handles it via default HttpError handler
- [Phase 22-rbac]: Migration named migration*0003_seed_roles.py (not 0003*) so Python import system can import seed_roles() for idempotency tests
- [Phase 22-rbac]: AdminController stub added in 22-02 as test vehicle for TestRequireRole — no auth= so RequireRole is sole gate returning 403 (not 401 from auth layer)
- [Phase 22-rbac]: GET /admin/users/{id}/roles returns list[str] directly — test_get_user_roles asserts isinstance(data, list); UserRoleOut dict would fail that check
- [Phase 22-rbac]: AdminController retains no auth= (consistent with 22-02 pattern) — RequireRole handles both anonymous and non-admin cases; Django middleware sets request.user before ninja processes
- [Phase 23-feature-entitlements]: noqa F401 on inline import gates: ruff F401 fires on unused imports in try/except blocks; noqa preserves import gate pattern from Phase 20/21 without ruff auto-removal
- [Phase 23-feature-entitlements]: Cache key is entitlements:{user.pk} with 300s TTL — per-user granularity allows targeted invalidation in Plan 03
- [Phase 23-feature-entitlements]: Import of \_has_feature inside has_feature() function body — catches ImportError per-call, not at module load time (billing-absent fallback)
- [Phase 23-feature-entitlements]: cache.delete() is unconditional on subscription.updated webhook — fires even when PlanProviderMapping has no entry for price_id (covers unmapped plan downgrades)
- [Phase 23-feature-entitlements]: \_extract_price_id_from_event guards against empty items.data — returns empty string for Stripe subscriptions with no line items

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

Last session: 2026-03-12T22:33:53.734Z
Stopped at: Completed 23-feature-entitlements-23-03-PLAN.md
Resume file: None
