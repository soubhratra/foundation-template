---
phase: 30-admin-backoffice
verified: 2026-03-13T17:30:00Z
status: human_needed
score: 11/11 automated must-haves verified
re_verification: false
human_verification:
  - test: "Visit http://localhost:8000/admin/ after starting the dev server"
    expected: "Unfold theme renders (dark sidebar, clean modern layout) — NOT the default Django admin grey theme"
    why_human: "Visual rendering cannot be verified programmatically; the Unfold CSS/template override only manifests in a browser"
  - test: "Log in as a staff user, navigate to Users & Auth -> Users, click a regular user's change page"
    expected: "An Impersonate button appears on the change page"
    why_human: "HijackUserAdminMixin injects the button at template render time — requires live browser verification"
  - test: "Click the Impersonate button on a regular user, then navigate the application"
    expected: "A persistent banner appears at the top of every page showing 'You are impersonating [user]' with a Release/Stop button"
    why_human: "The hijack banner is rendered by django-hijack's middleware template tag — requires live browser to confirm banner presence and persistence across page loads"
  - test: "Click the Release button on the impersonation banner"
    expected: "Redirect to /admin/accounts/user/ and the banner disappears"
    why_human: "Post-release redirect behaviour requires browser interaction"
  - test: "Attempt to impersonate a staff user (is_staff=True) from the admin"
    expected: "Impersonation is blocked — no Impersonate button visible, or 403 returned if URL accessed directly"
    why_human: "Permission enforcement at the HTTP layer requires live request; automated test covers the permission function but not the HTTP rejection UI"
---

# Phase 30: Admin Backoffice Verification Report

**Phase Goal:** Install and configure django-unfold for a themed admin interface and django-hijack for staff impersonation, with full audit trail via ImpersonationEvent model
**Verified:** 2026-03-13T17:30:00Z
**Status:** human_needed — all automated checks pass; 5 items require live browser verification
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                    | Status   | Evidence                                                                                      |
| --- | ---------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------- |
| 1   | django-unfold and django-hijack are installed and importable                             | VERIFIED | `pyproject.toml` lines 47-48; `uv run python -c "import unfold; import hijack"` exits 0       |
| 2   | unfold appears before django.contrib.admin in INSTALLED_APPS                             | VERIFIED | `base.py` line 98: `"unfold"`, line 104: `"django.contrib.admin"`                             |
| 3   | hijack apps are inside B2B_START/B2B_END in INSTALLED_APPS                               | VERIFIED | `base.py` lines 100-103: `"hijack"` and `"hijack.contrib.admin"` inside B2B block             |
| 4   | HijackUserMiddleware is after AuthenticationMiddleware, inside B2B_START/B2B_END         | VERIFIED | `base.py` lines 145-147: Auth line 145, Hijack line 147, allauth line 149                     |
| 5   | UNFOLD settings dict present with 4-section sidebar (B2B, Users & Auth, Billing, System) | VERIFIED | `base.py` lines 511-617: all 4 sections present with correct titles and items                 |
| 6   | hijack.urls included in config/urls.py inside B2B_START/B2B_END                          | VERIFIED | `urls.py` line 171: `path("hijack/", include("hijack.urls"))`                                 |
| 7   | ImpersonationEvent model exists with correct fields                                      | VERIFIED | `apps/audit/models.py`: action, hijacker (FK), hijacked (FK), timestamp                       |
| 8   | Migration created and covers ImpersonationEvent table                                    | VERIFIED | `apps/audit/migrations/0001_impersonation_event.py`: CreateModel ImpersonationEvent           |
| 9   | hijack_started and hijack_ended signals write ImpersonationEvent rows                    | VERIFIED | `apps/audit/apps.py` ready(): connects both signals; test_hijack.py 7/7 GREEN                 |
| 10  | AuditContextMiddleware.get_context() injects impersonator_id when hijack_history present | VERIFIED | `apps/audit/middleware.py` lines 34-38: reads `hijack_history`, sets `ctx["impersonator_id"]` |
| 11  | All domain ModelAdmins inherit unfold.admin.ModelAdmin                                   | VERIFIED | All 6 admin.py files confirmed; `uv run pytest tests/admin/ -q` → 19 passed                   |

**Score:** 11/11 truths verified (automated)

---

### Required Artifacts

| Artifact                                                     | Expected                                                  | Status   | Details                                                                                                                                              |
| ------------------------------------------------------------ | --------------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/tests/admin/__init__.py`                           | Test package marker                                       | VERIFIED | Empty file, exists                                                                                                                                   |
| `apps/api/tests/admin/conftest.py`                           | staff_user, regular_user, superuser, staff_client         | VERIFIED | All 4 fixtures present                                                                                                                               |
| `apps/api/tests/admin/test_admin_smoke.py`                   | ADMIN-01 UnfoldModelAdmin inheritance RED->GREEN          | VERIFIED | 7 tests, all GREEN                                                                                                                                   |
| `apps/api/tests/admin/test_unfold_config.py`                 | ADMIN-01 UNFOLD settings structure                        | VERIFIED | 5 tests, all GREEN                                                                                                                                   |
| `apps/api/tests/admin/test_hijack.py`                        | ADMIN-02 permission + signal + middleware                 | VERIFIED | 7 tests, all GREEN                                                                                                                                   |
| `apps/api/apps/accounts/permissions.py`                      | staff_can_hijack_regular_users() function                 | VERIFIED | Function exists, logic correct (active + non-staff check)                                                                                            |
| `apps/api/apps/audit/models.py`                              | ImpersonationEvent model                                  | VERIFIED | class ImpersonationEvent with all required fields                                                                                                    |
| `apps/api/apps/audit/migrations/0001_impersonation_event.py` | ImpersonationEvent table migration                        | VERIFIED | Generated by Django 5.2.11, CreateModel present                                                                                                      |
| `apps/api/apps/audit/apps.py`                                | AuditConfig.ready() with signal wiring                    | VERIFIED | Both hijack_started and hijack_ended connected                                                                                                       |
| `apps/api/apps/audit/middleware.py`                          | AuditContextMiddleware impersonator_id injection          | VERIFIED | hijack_history branch adds impersonator_id to ctx                                                                                                    |
| `apps/api/apps/accounts/admin.py`                            | UserAdmin with HijackUserAdminMixin + UnfoldModelAdmin    | VERIFIED | MRO: HijackUserAdminMixin, BaseUserAdmin, ModelAdmin; Unfold forms set                                                                               |
| `apps/api/apps/billing/admin.py`                             | 5 billing admins inheriting UnfoldModelAdmin              | VERIFIED | CustomerAdmin, SubscriptionAdmin, PaymentAdmin, ProcessedWebhookEventAdmin, PlanProviderMappingAdmin — all use `from unfold.admin import ModelAdmin` |
| `apps/api/apps/orgs/admin.py`                                | OrganizationAdmin + MembershipAdmin                       | VERIFIED | Both classes, B2B_START/B2B_END markers present                                                                                                      |
| `apps/api/apps/api_keys/admin.py`                            | APIKeyAdmin                                               | VERIFIED | Exists with UnfoldModelAdmin, B2B markers                                                                                                            |
| `apps/api/apps/webhooks/admin.py`                            | WebhookEndpointAdmin + WebhookDeliveryAdmin               | VERIFIED | Both classes, field name corrected to signing_key+secret_hash                                                                                        |
| `apps/api/apps/audit/admin.py`                               | ImpersonationEventAdmin read-only + HasImpersonatorFilter | VERIFIED | has_add/change/delete_permission all return False; filter class present                                                                              |

---

### Key Link Verification

| From                                          | To                                                         | Via                                                  | Status | Details                                                                                                    |
| --------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------- |
| `base.py HIJACK_PERMISSION_CHECK`             | `apps.accounts.permissions.staff_can_hijack_regular_users` | Dotted import path string in settings                | WIRED  | `base.py` line 699: `HIJACK_PERMISSION_CHECK = "apps.accounts.permissions.staff_can_hijack_regular_users"` |
| `apps/audit/apps.py ready()`                  | `hijack.signals.hijack_started / hijack_ended`             | signal.connect()                                     | WIRED  | `apps.py` lines 36-37: both signals connected in ready()                                                   |
| `apps/audit/middleware.py get_context()`      | `request.hijack_history`                                   | getattr(request, 'hijack_history', None)             | WIRED  | `middleware.py` line 34: reads hijack_history, injects impersonator_id                                     |
| `apps/accounts/admin.py UserAdmin`            | `hijack.contrib.admin.HijackUserAdminMixin`                | MRO: HijackUserAdminMixin, BaseUserAdmin, ModelAdmin | WIRED  | `admin.py` line 13: correct MRO order confirmed                                                            |
| `apps/audit/admin.py ImpersonationEventAdmin` | `apps/audit/models.ImpersonationEvent`                     | @admin.register(ImpersonationEvent)                  | WIRED  | `admin.py` line 30: `@admin.register(ImpersonationEvent)`                                                  |

---

### Requirements Coverage

| Requirement | Source Plans        | Description                                                                                                                                               | Status                              | Evidence                                                                                                                               |
| ----------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| ADMIN-01    | 30-01, 30-02, 30-03 | Django admin themed with django-unfold across all domain ModelAdmin registrations; navigation sidebar configured                                          | SATISFIED                           | All 6 domain admin.py files import from `unfold.admin`; UNFOLD sidebar dict with 4 sections verified; 12/19 smoke tests cover ADMIN-01 |
| ADMIN-02    | 30-01, 30-02, 30-03 | Staff users can impersonate any non-staff user via django-hijack; persistent banner shown; impersonation events written to audit log with impersonator FK | PARTIALLY SATISFIED (human pending) | Permission function, signals, ImpersonationEvent model all verified; 7/7 ADMIN-02 tests GREEN; persistent banner requires live browser |

No orphaned requirements: both ADMIN-01 and ADMIN-02 are claimed by plans 01-03 and have implementation evidence.

---

### Anti-Patterns Found

| File | Line | Pattern    | Severity | Impact |
| ---- | ---- | ---------- | -------- | ------ |
| N/A  | —    | None found | —        | —      |

No TODO/FIXME/placeholder comments, no empty implementations, no stub returns found in any of the 16 phase files inspected.

**Note — pre-existing issue (not caused by Phase 30):** `tests/billing/test_controllers.py::test_get_subscription` has a pre-existing nplusone error documented in the Plan 03 SUMMARY. Not caused by Phase 30.

---

### Human Verification Required

#### 1. Unfold Theme Renders

**Test:** Start the dev server (`docker compose up -d && cd apps/api && uv run python manage.py runserver`), visit http://localhost:8000/admin/
**Expected:** The Unfold theme renders — dark sidebar, clean modern layout. The default Django admin grey theme must NOT appear.
**Why human:** CSS/template overrides only render in a browser; no programmatic check covers visual output.

#### 2. Impersonate Button on User Change Page

**Test:** Log in to admin as a staff user. Navigate to Users & Auth -> Users -> click on any regular (non-staff) user's change page.
**Expected:** An "Impersonate" button appears on the change page, rendered by HijackUserAdminMixin.
**Why human:** The button is injected via Django admin template inheritance at render time — can only be confirmed in a live browser.

#### 3. Persistent Impersonation Banner

**Test:** Click the Impersonate button on a regular user's change page.
**Expected:** You are redirected to the main app (not admin). A persistent banner appears at the top of every page reading "You are impersonating [user]" with a Release or Stop Impersonating button. The banner persists across page navigation.
**Why human:** The banner is rendered by HijackUserMiddleware's template context and the `{% hijack_notification %}` template tag — live browser needed.

#### 4. Release Redirects Correctly

**Test:** While impersonating, click the Release/Stop button in the banner.
**Expected:** You are returned to `/admin/accounts/user/` (the value of HIJACK_LOGOUT_REDIRECT_URL).
**Why human:** Post-release redirect requires a live HTTP session.

#### 5. Staff-to-Staff Impersonation Blocked at the UI Level

**Test:** Navigate to a staff user's change page in the admin.
**Expected:** No Impersonate button appears (or clicking a direct hijack URL returns 403). The `staff_can_hijack_regular_users()` function is verified by test, but the HTTP-level rejection UI needs visual confirmation.
**Why human:** UI-level button suppression depends on how HijackUserAdminMixin reads the permission check — requires browser inspection.

---

### Gaps Summary

No automated gaps found. All 11 truths are verified. All 16 artifacts exist and are substantive. All 5 key links are wired.

The only outstanding items are the 5 human verification points above, all of which relate to the runtime UI behavior of django-unfold and django-hijack — CSS rendering, template-injected buttons, and banner persistence. These cannot be verified programmatically and were explicitly flagged as a human checkpoint in Plan 03 (Task 3).

The SUMMARY for Plan 03 notes that Task 3 was "APPROVED via automated testing" rather than a live browser session. This means the human checkpoint was not fully completed as specified in the plan. The 5 items above constitute the outstanding human verification.

---

_Verified: 2026-03-13T17:30:00Z_
_Verifier: Claude (gsd-verifier)_
