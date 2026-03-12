---
phase: 14-observability-adapter
verified: 2026-03-11T19:37:10Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 14: ObservabilityAdapter Verification Report

**Phase Goal:** Implement the ObservabilityAdapter pattern — a Django ABC + concrete adapters (NoOp, PostHog) + middleware for request tracking + Celery signal for task failure capture — that ships as ready-to-use in the template and can be completely removed by the CLI scaffolder for projects that don't need observability.
**Verified:** 2026-03-11T19:37:10Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                           | Status   | Evidence                                                                                                |
| --- | ----------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------- |
| 1   | Unhandled Django exception auto-captured with user_id, path, method, exc_type                   | VERIFIED | `ObservabilityMiddleware.process_exception` in middleware.py; 2 tests PASS GREEN                        |
| 2   | Unhandled Celery task exception auto-captured via task_failure signal                           | VERIFIED | `@task_failure.connect(weak=False)` in CoreConfig.ready(); test_celery_signal_handler PASSES            |
| 3   | NoOpAdapter is the default — CI and dev without POSTHOG_API_KEY produce zero overhead           | VERIFIED | `OBSERVABILITY_ADAPTER` defaults to `apps.core.observability.NoOpAdapter` in base.py                    |
| 4   | PostHogAdapter uses posthog.Posthog instance (thread-safe)                                      | VERIFIED | PostHogAdapter.**init** uses `posthog.Posthog(api_key=..., host=...)` instance; test PASSES             |
| 5   | SentryAdapter stub present with NotImplementedError and migration guide comment                 | VERIFIED | SentryAdapter in observability.py raises NotImplementedError; 14-line migration guide comment above     |
| 6   | Next.js fires $pageview events on every client-side navigation without per-page instrumentation | VERIFIED | PostHogPageView + usePathname + useRef dedup in providers.tsx; posthog.init with capture_pageview:false |
| 7   | Expo fires $screen events on every screen change without per-screen instrumentation             | VERIFIED | PostHogScreenTracker + useSegments + useRef dedup in \_layout.tsx                                       |
| 8   | Session replay enabled with maskAllInputs: true (privacy-safe default)                          | VERIFIED | `session_recording: { maskAllInputs: true }` in posthog.init call in providers.tsx                      |
| 9   | Both frontends work with no PostHog key — SDK silences itself                                   | VERIFIED | `loaded: (ph) => { if (!NEXT_PUBLIC_POSTHOG_KEY) ph.opt_out_capturing(); }` in providers.tsx            |
| 10  | autocapture.captureScreens is false in Expo (avoids Expo Router crash)                          | VERIFIED | `autocapture={{ captureScreens: false }}` on PostHogProvider in \_layout.tsx                            |
| 11  | --without observability removes all 7 touch points without orphaned imports                     | VERIFIED | removeObservability() handles all 7 touch points; integration test PASSES in 0.32s                      |
| 12  | observability appears as selectable option in interactive CLI prompt                            | VERIFIED | SelectedFeatures includes "observability"; promptFeatures() has the option + initialValues entry        |
| 13  | All 7 TDD tests pass GREEN                                                                      | VERIFIED | 6 unit tests + 1 scaffolder integration test all PASS (confirmed by live test run)                      |

**Score:** 13/13 truths verified

---

## Required Artifacts

| Artifact                                                  | Expected                                                                               | Status   | Details                                                                              |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| `apps/api/apps/core/observability.py`                     | ObservabilityAdapter ABC, PostHogAdapter, NoOpAdapter, SentryAdapter, factory          | VERIFIED | 146 lines; all 5 exports present; lazy posthog import inside **init**                |
| `apps/api/apps/core/middleware.py`                        | ObservabilityMiddleware with process_exception returning None                          | VERIFIED | 102 lines; ObservabilityMiddleware appended; returns None explicitly                 |
| `apps/api/apps/core/apps.py`                              | task_failure signal connected in CoreConfig.ready() with weak=False                    | VERIFIED | task_failure.connect(weak=False) decorator; lazy import of get_observability_adapter |
| `apps/api/config/settings/base.py`                        | OBSERVABILITY MODULE block; NoOpAdapter default; ObservabilityMiddleware in MIDDLEWARE | VERIFIED | Lines 83–92: OBSERVABILITY MODULE block; line 127: middleware in list                |
| `apps/api/pyproject.toml`                                 | posthog>=7.9.0 in main dependencies                                                    | VERIFIED | `"posthog>=7.9.0"` on line 36                                                        |
| `apps/api/.env.example`                                   | POSTHOG_API_KEY and POSTHOG_HOST env vars documented                                   | VERIFIED | Lines 18–19 present                                                                  |
| `apps/web/app/providers.tsx`                              | PostHogProvider, PostHogPageView, posthog.init, capture_pageview: false                | VERIFIED | All elements present; posthog.init with opt_out_capturing fallback                   |
| `apps/web/.env.example`                                   | NEXT_PUBLIC_POSTHOG_KEY and NEXT_PUBLIC_POSTHOG_HOST                                   | VERIFIED | Lines 8–9 present                                                                    |
| `apps/mobile/app/_layout.tsx`                             | PostHogProvider, PostHogScreenTracker, autocapture captureScreens:false                | VERIFIED | All elements present; useSegments dedup pattern correct                              |
| `apps/mobile/.env.example`                                | EXPO_PUBLIC_POSTHOG_KEY                                                                | VERIFIED | Line 8 present                                                                       |
| `packages/create-foundation-app/src/remove.ts`            | removeObservability() with all 7 touch points                                          | VERIFIED | Exported function at line 363; all 7 steps documented and implemented                |
| `packages/create-foundation-app/src/prompts.ts`           | SelectedFeatures includes "observability"; promptFeatures() has option                 | VERIFIED | Line 8: union type; line 76: option value; line 80: in initialValues                 |
| `packages/create-foundation-app/src/index.ts`             | removeObservability() called when observability not selected                           | VERIFIED | Lines 125–126: if-not-includes guard calling removeObservability()                   |
| `apps/api/tests/core/test_observability.py`               | 6 test functions covering full adapter contract                                        | VERIFIED | 6 functions collected and passing GREEN                                              |
| `apps/api/tests/test_scaffolder_observability_removal.py` | Integration test invoking compiled dist/remove.js                                      | VERIFIED | 1 test class + test function; PASSES in 0.32s                                        |

---

## Key Link Verification

| From                                           | To                                             | Via                                                | Status | Details                                                                             |
| ---------------------------------------------- | ---------------------------------------------- | -------------------------------------------------- | ------ | ----------------------------------------------------------------------------------- |
| `apps/core/middleware.py`                      | `apps/core/observability.py`                   | `get_observability_adapter()` in process_exception | WIRED  | Line 26: module-level import; line 98: called in process_exception                  |
| `apps/core/apps.py`                            | `apps/core/observability.py`                   | lazy import inside task_failure handler            | WIRED  | Line 42: `from apps.core.observability import get_observability_adapter` inside def |
| `apps/api/config/settings/base.py`             | `apps/core/observability.py`                   | OBSERVABILITY_ADAPTER dotted path string           | WIRED  | `apps.core.observability.NoOpAdapter` as default on line 89                         |
| `apps/web/app/providers.tsx`                   | `posthog-js`                                   | posthog.init() with window guard                   | WIRED  | Lines 14–24: init block; PostHogProvider wraps AppProviders; PostHogPageView inside |
| `apps/mobile/app/_layout.tsx`                  | `posthog-react-native`                         | PostHogProvider wrapping Stack                     | WIRED  | Lines 78–102: PostHogProvider outermost; PostHogScreenTracker inside                |
| `packages/create-foundation-app/src/index.ts`  | `packages/create-foundation-app/src/remove.ts` | removeObservability() call                         | WIRED  | Line 19: import; lines 125–126: called when observability not in features           |
| `packages/create-foundation-app/src/remove.ts` | `apps/api/config/settings/base.py`             | regex remove OBSERVABILITY MODULE block            | WIRED  | Lines 390–393: regex targeting `# OBSERVABILITY MODULE` delimiter pattern           |

---

## Requirements Coverage

| Requirement | Source Plans               | Description                                                                                                                                                                                  | Status    | Evidence                                                                                                             |
| ----------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | -------------------------------------------------------------------------------------------------------------------- |
| OBS-03      | 14-01, 14-02, 14-03, 14-04 | ObservabilityAdapter ABC with PostHogAdapter as default — covers Django + Celery + Next.js + Expo — `--without observability` removes it cleanly; SentryAdapter available as documented swap | SATISFIED | All artifacts verified; all 7 tests pass; integration test passes; REQUIREMENTS.md marks OBS-03 Complete at Phase 14 |

No orphaned requirements found. REQUIREMENTS.md confirms OBS-03 maps to Phase 14 and is marked Complete.

---

## Anti-Patterns Found

None. No TODO/FIXME/placeholder/stub implementations found in any production artifact. The `SentryAdapter.NotImplementedError` is a deliberate, documented design choice (stub with migration guide), not an anti-pattern.

---

## Human Verification Required

### 1. Live PostHog Event Capture (Web)

**Test:** Set `NEXT_PUBLIC_POSTHOG_KEY=phc_...` in `apps/web/.env.local`; start dev server; navigate between pages
**Expected:** `$pageview` events appear in PostHog Live Events within 30s; events carry `$current_url`
**Why human:** Requires live PostHog credentials and a running browser session; cannot be verified by static code analysis

### 2. Live PostHog Screen Tracking (Expo)

**Test:** Set `EXPO_PUBLIC_POSTHOG_KEY=phc_...` in `apps/mobile/.env`; start Expo dev server on device/emulator; navigate between screens
**Expected:** `$screen` events appear in PostHog Live Events within 30s; screen names match Expo Router segments
**Why human:** Requires live PostHog credentials, Expo runtime, and physical navigation

### 3. Session Replay Recording

**Test:** Run the web app with PostHog key set; interact with any form (type in inputs); view PostHog Session Replay
**Expected:** Recording appears with all input content masked (asterisks)
**Why human:** Session replay requires live PostHog and browser interaction to verify masking behavior

### 4. Expo App Does Not Crash on Launch

**Test:** Launch the Expo app with the PostHog provider in place (no key required)
**Expected:** App opens normally; no `useNavigationState` crash in logs
**Why human:** The `autocapture={{ captureScreens: false }}` guard prevents the crash — only verifiable at Expo runtime

---

## Gaps Summary

No gaps. All 13 truths verified, all 15 artifacts pass all three levels (exists, substantive, wired), all 7 key links confirmed wired, OBS-03 is satisfied. The 4 human verification items require live credentials and runtime but do not block goal achievement — the code correctness is verified.

---

_Verified: 2026-03-11T19:37:10Z_
_Verifier: Claude (gsd-verifier)_
