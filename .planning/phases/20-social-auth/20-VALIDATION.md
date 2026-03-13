---
phase: 20
slug: social-auth
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
audited: 2026-03-12
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                                                                                       |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Framework**          | pytest 8.x + pytest-django                                                                                                  |
| **Config file**        | `apps/api/pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`                                                         |
| **Quick run command**  | `cd apps/api && python -m pytest tests/test_social_settings.py tests/test_apple_auth.py tests/test_social_adapter.py -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest -x -q && cd ../../packages/create-foundation-app && pnpm test`                             |
| **Estimated runtime**  | ~30 seconds                                                                                                                 |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/test_social_settings.py tests/test_apple_auth.py tests/test_social_adapter.py -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest -x -q && cd ../../packages/create-foundation-app && pnpm test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement          | Test Type               | Automated Command                                                                                                  | File Exists | Status   |
| -------- | ---- | ---- | -------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------- | -------- |
| 20-01-01 | 01   | 0    | SOCIAL-01, SOCIAL-02 | unit                    | `pytest tests/test_social_settings.py -x -q`                                                                       | ✅          | ✅ green |
| 20-01-02 | 01   | 0    | SOCIAL-03            | unit                    | `pytest tests/test_apple_auth.py -x -q`                                                                            | ✅          | ✅ green |
| 20-01-03 | 01   | 0    | SOCIAL-04            | unit                    | `pytest tests/test_social_adapter.py -x -q`                                                                        | ✅          | ✅ green |
| 20-01-04 | 01   | 0    | SOCIAL-05            | unit (TS) + integration | `npx vitest run tests/remove-social-auth.test.ts && pytest tests/test_scaffolder_social_removal.py -x`             | ✅          | ✅ green |
| 20-02-01 | 02   | 1    | SOCIAL-01            | unit                    | `pytest tests/test_social_settings.py::TestGoogleProviderRegistration::test_google_provider_registered -x`         | ✅          | ✅ green |
| 20-02-02 | 02   | 1    | SOCIAL-02            | unit                    | `pytest tests/test_social_settings.py::TestGoogleProviderRegistration::test_github_provider_registered -x`         | ✅          | ✅ green |
| 20-03-01 | 03   | 1    | SOCIAL-03            | unit                    | `pytest tests/test_apple_auth.py::TestVerifyAppleIdentityToken::test_verify_identity_token_accepts_valid_token -x` | ✅          | ✅ green |
| 20-03-02 | 03   | 1    | SOCIAL-03            | unit                    | `pytest tests/test_apple_auth.py::TestAppleNamePersistence::test_name_persisted_first_login -x`                    | ✅          | ✅ green |
| 20-04-01 | 04   | 1    | SOCIAL-04            | unit                    | `pytest tests/test_social_adapter.py::TestRelayEmailAutoConnect::test_relay_email_not_auto_connected -x`           | ✅          | ✅ green |
| 20-05-01 | 05   | 2    | SOCIAL-05            | unit (TS)               | `cd packages/create-foundation-app && npx vitest run tests/remove-social-auth.test.ts`                             | ✅          | ✅ green |
| 20-05-02 | 05   | 2    | SOCIAL-05            | integration             | `pytest tests/test_scaffolder_social_removal.py -x`                                                                | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `apps/api/tests/test_social_settings.py` — SOCIAL-01, SOCIAL-02 (11 tests)
- [x] `apps/api/tests/test_apple_auth.py` — SOCIAL-03 (5 tests)
- [x] `apps/api/tests/test_social_adapter.py` — SOCIAL-04 (4 tests)
- [x] `apps/api/tests/test_scaffolder_social_removal.py` — SOCIAL-05 (1 test)
- [x] `packages/create-foundation-app/tests/remove-social-auth.test.ts` — SOCIAL-05 (11 tests)

---

## Manual-Only Verifications

| Behavior                                       | Requirement          | Why Manual                                              | Test Instructions                                                                                                             |
| ---------------------------------------------- | -------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Google button present on web login/signup page | SOCIAL-01            | Visual UI check — requires browser                      | Open `/login` and `/signup`, verify "Continue with Google" button appears when `GOOGLE_CLIENT_ID` is set                      |
| GitHub button present on web login/signup page | SOCIAL-02            | Visual UI check — requires browser                      | Open `/login` and `/signup`, verify "Continue with GitHub" button appears when `GITHUB_CLIENT_ID` is set                      |
| Buttons absent when credentials not set        | SOCIAL-01, SOCIAL-02 | Visual UI check — requires browser                      | Unset env vars, verify buttons do not appear                                                                                  |
| Apple button absent from web pages             | SOCIAL-03            | Visual UI check — requires browser                      | Verify no Apple button on `/login` or `/signup`                                                                               |
| Full Google OAuth redirect flow                | SOCIAL-01            | Requires real OAuth credentials + browser               | With real `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`, click "Continue with Google", complete flow, verify landing on dashboard |
| Full GitHub OAuth redirect flow                | SOCIAL-02            | Requires real OAuth credentials + browser               | With real `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`, complete flow, verify dashboard landing                                  |
| iOS Apple Sign In flow                         | SOCIAL-03            | Requires iOS device/simulator + Apple developer account | Tap "Sign in with Apple" in mobile app, complete Apple authorization, verify logged in                                        |
| Email/password account merge via Google        | SOCIAL-04            | Requires real OAuth + existing email/password account   | Create account with email, then sign in with Google using same email — verify lands on existing account, no duplicate created |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s (actual: 2.41s Python + 0.72s TS)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-12 — 30/30 tests passing (19 Python + 11 TypeScript)

---

## Validation Audit 2026-03-12

| Metric        | Count |
| ------------- | ----- |
| Gaps found    | 0     |
| Resolved      | 0     |
| Escalated     | 0     |
| Tests run     | 30    |
| Tests passing | 30    |
