# Domain Pitfalls: v1.3 SaaS Functional Baseline

**Domain:** Adding transactional email, social auth (Google/GitHub/Apple), GDPR baseline, RBAC, and feature entitlements to an existing Django + Next.js + Expo monorepo
**Researched:** 2026-03-11
**Confidence:** MEDIUM-HIGH (WebSearch verified against official documentation; Apple-specific claims verified against Expo and django-allauth current docs. GDPR claims verified against Django ORM behavior. Feature entitlement and RBAC claims corroborated by multiple sources.)

> **Note:** This file supersedes the v1.1 billing pitfalls document for v1.3 work. The billing pitfalls remain valid and apply to their respective phases. This file focuses exclusively on the five new v1.3 features being added to the already-shipped v1.2 system.

---

## Critical Pitfalls

Mistakes that cause security holes, data loss, broken auth flows, or compliance violations.

---

### Pitfall 1: Apple Sign In — Native Token vs. Web Token Are Not Interchangeable

**What goes wrong:**
Expo's `expo-apple-authentication` generates a native iOS identity token (a JWT signed by Apple's native service). Django Allauth's Apple provider expects a token from the web OAuth flow (which uses a `client_secret` derived from a Service ID, not a Bundle ID). These two tokens have different `aud` (audience) claims.

When you pass a native Expo token directly to Allauth's standard social token endpoint, Apple's server-side token verification fails with an audience mismatch error. The error is often misleading — it surfaces as `jwt.exceptions.InvalidAudienceError` or a generic "invalid token" response, not a clear explanation of the mismatch.

Additionally, Apple only sends the user's name and email on the **first** authentication. Subsequent authentications return `null` for `fullName`, even if the user reinstalls the app. If the backend does not persist the name on first receipt, it is permanently unrecoverable.

**Why it happens:**
Sign In with Apple requires two separate Apple developer configurations:

- **App ID** (`com.yourcompany.app`) — used for native iOS flows; the `client_id` Apple checks in native tokens
- **Service ID** (`com.yourcompany.app.web`) — used for web OAuth flows; what Allauth's standard Apple provider expects

Developers configure only one and assume both flows use the same token format.

**How to avoid:**

1. Register both an App ID and a Service ID in the Apple Developer portal.
2. On the mobile side, use `expo-apple-authentication` to get the native identity token.
3. Send this token to a **dedicated Django endpoint** (not Allauth's standard provider flow) that verifies the native JWT using Apple's public keys fetched from `https://appleid.apple.com/auth/keys`.
4. After verification, use `allauth.socialaccount` APIs internally to connect or create the social account, bypassing the web OAuth redirect dance.
5. Persist `fullName` (first + last) on the very first successful auth; never rely on subsequent calls returning it.

**Warning signs:**

- A single `APPLE_CLIENT_ID` setting without a separate `APP_BUNDLE_ID` setting
- `jwt.InvalidAudienceError` or `"aud" claim mismatch` in error logs
- Users reporting their name shows as blank after re-installation
- Allauth's `/auth/provider/token/` endpoint used directly from the Expo app for Apple

**Phase to address:** Social Auth phase. Design the dedicated native-token verification endpoint before writing any Expo-side Apple auth code.

**Recovery cost:** HIGH — the two-flow architecture is a design decision. Retrofitting it after building around a single flow requires changing both the Django endpoint and the Expo auth module.

**Confidence:** HIGH (Expo docs, Apple Developer forum, multiple 2025 community posts confirming native vs. web token distinction)

---

### Pitfall 2: Social Auth — Email Account Conflict With Existing Password Accounts

**What goes wrong:**
A user registered with `user@example.com` and a password. Later they try to sign in with Google using the same email. Django Allauth (with `SOCIALACCOUNT_EMAIL_AUTHENTICATION=False`, the default) will either:

- **Block the social login** with "An account already exists with this e-mail address" — confusing and a dead end for the user
- **Create a duplicate account** with the same email if `ACCOUNT_UNIQUE_EMAIL=False` — two accounts, split data, billing chaos

Neither is acceptable UX. The secure way to handle this is email-verified account merging: verify the social provider's email is confirmed by the provider, then automatically link the social account to the existing password account.

**Why it happens:**
The default Allauth configuration is conservative: it does not auto-link social accounts to existing email accounts because the social provider's email may not be verified. This is correct security behavior for providers that don't guarantee email verification (older Facebook, some OpenID providers). But Google and GitHub **do** guarantee verified emails, so the conservative default becomes needlessly hostile.

**How to avoid:**

1. Set `SOCIALACCOUNT_EMAIL_AUTHENTICATION = True` and `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` in settings for Google and GitHub (these providers always return verified emails).
2. Do NOT set auto-connect for Apple — Apple's email relay (`privaterelay.appleid.com`) does not verify the user's actual email in the same way.
3. Write a custom `SocialAccountAdapter` that enforces the per-provider rule:

```python
class FoundationSocialAccountAdapter(DefaultSocialAccountAdapter):
    TRUSTED_PROVIDERS = {"google", "github"}

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider not in self.TRUSTED_PROVIDERS:
            return
        if not sociallogin.is_existing:
            email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
            if email:
                try:
                    existing = User.objects.get(email=email)
                    sociallogin.connect(request, existing)
                except User.DoesNotExist:
                    pass
```

4. Test explicitly: create a password account, then log in via Google with the same email, and verify the same user object is returned (not a new one).

**Warning signs:**

- `SOCIALACCOUNT_EMAIL_AUTHENTICATION` not set (defaults to conservative False)
- Users reporting "two accounts" or missing subscription data after Google login
- No test covering the email-collision scenario
- `pre_social_login` adapter method not overridden

**Phase to address:** Social Auth phase. Account merging logic must be in place before any social provider is activated in production.

**Recovery cost:** HIGH — duplicate accounts in production require a manual merge operation with potential data loss decisions (which subscription survives?).

**Confidence:** HIGH (django-allauth GitHub issue #418, official configuration docs, multiple community discussions)

---

### Pitfall 3: Transactional Email — Celery Task Dispatched Before DB Transaction Commits

**What goes wrong:**
A common pattern is:

```python
def register_user(email, password):
    user = User.objects.create_user(email=email, password=password)
    send_welcome_email.delay(user.id)   # Celery task dispatched here
```

The Celery task starts executing on a worker before the outer view's database transaction commits. The worker queries `User.objects.get(id=user_id)` and gets `DoesNotExist` because the row is not yet visible to other connections. The email is never sent. Django's default `ATOMIC_REQUESTS=True` makes this worse: the entire view runs in a transaction, meaning the `create_user` call is not committed until the view function returns — which is after `send_welcome_email.delay()` has already been called.

This is one of the most commonly reported Django + Celery bugs, and it is silent: the task fails with `DoesNotExist`, Celery retries, the user's row may be committed by then, but the retry delay means the welcome email arrives 30-60 seconds late (or never, if max retries is low).

**How to avoid:**
Use `transaction.on_commit()` to defer task dispatch until the transaction is committed:

```python
from django.db import transaction

def register_user(email, password):
    user = User.objects.create_user(email=email, password=password)
    transaction.on_commit(lambda: send_welcome_email.delay(user.id))
```

For Celery 5.x with `task_always_eager=False`, this is the correct and only reliable pattern.

**Warning signs:**

- `send_*.delay()` called immediately after `Model.objects.create()`
- `User.DoesNotExist` appearing in Celery task logs
- Welcome emails arriving inconsistently (sometimes 30-60 seconds late)
- No `transaction.on_commit()` wrapping any task dispatch that follows a write

**Phase to address:** Transactional Email phase. The `on_commit` pattern must be enforced as a code review rule for every email task dispatch.

**Recovery cost:** LOW to fix, but MEDIUM for trust — users who received no welcome email may have already churned or marked the email as spam.

**Confidence:** HIGH (Django documentation on `on_commit`, Celery documentation, multiple community post-mortems)

---

### Pitfall 4: GDPR Hard Delete — Orphaned Data in Third-Party and Allauth Tables

**What goes wrong:**
`user.delete()` cascades through Django ORM relationships that Django knows about. However, several third-party packages store user-related data in tables the ORM cascade does not automatically reach:

1. **django-allauth** — `EmailAddress`, `SocialAccount`, `SocialToken`, `EmailConfirmation` rows in `account_*` and `socialaccount_*` tables. Django Allauth's `User.delete()` cascade works correctly IF the ForeignKey `on_delete=CASCADE` is set, but `SocialToken` rows can be orphaned if Allauth's cascade is not properly applied in all versions.

2. **PostHog** (ObservabilityAdapter) — If `identify()` was called, the user's profile exists in PostHog. Django's `user.delete()` does not notify PostHog. The deleted user's events persist in PostHog indefinitely, linked to an anonymous ID. Under GDPR, analytics data tied to an identified person must be deleted on request.

3. **Celery task results** — If `django-celery-results` is used, task result rows may contain user IDs or email addresses in the `result` JSON field. These rows are not cascade-deleted with the user.

4. **Stripe** (BillingProfile cascade) — The `BillingProfile` model cascades from User, and deleting it does NOT delete the Stripe customer object. Under GDPR's right to erasure, the Stripe customer record (which contains payment method fingerprints and billing address) must also be deleted via `stripe.Customer.delete()`.

5. **Structlog / OpenTelemetry traces** — Logs and traces emitted with `user_id` in the structured context are stored in whatever log sink is configured (CloudWatch, Grafana, etc.). These are not erased by `user.delete()`.

**How to avoid:**

1. Write a `UserDeletionService` that orchestrates deletion across all systems, not just Django ORM:

```python
class UserDeletionService:
    def delete_user(self, user: User) -> None:
        # 1. External services first (before row is gone)
        self._delete_stripe_customer(user)
        self._delete_posthog_person(user)

        # 2. Celery task result cleanup (if django-celery-results used)
        TaskResult.objects.filter(result__contains=str(user.id)).delete()

        # 3. Django ORM cascade (handles allauth tables if FK cascade is set)
        user.delete()
```

2. For PostHog: call `posthog.delete(distinct_id=str(user.id))` which flags the person for deletion in PostHog's pipeline.
3. For logs: document in the data processing record that logs are retained for N days and purged on schedule — this is legally acceptable under GDPR's data minimization principle if the retention period is stated.
4. Add a test that verifies no `SocialAccount`, `EmailAddress`, or `BillingProfile` rows remain after user deletion.

**Warning signs:**

- `user.delete()` called directly without a service orchestrating external cleanup
- No `stripe.Customer.delete()` call in the deletion flow
- PostHog `identify()` calls without a corresponding deletion path
- No test asserting that all related tables are empty post-deletion

**Phase to address:** GDPR Baseline phase. The `UserDeletionService` must be designed before the deletion endpoint is exposed.

**Recovery cost:** HIGH — retroactively discovering orphaned data after production deletions means data exists in external systems for users who requested erasure, which is a GDPR violation with potential fines.

**Confidence:** MEDIUM-HIGH (Django ORM cascade behavior HIGH confidence; PostHog and Stripe cascade gaps MEDIUM — verified against each service's API docs)

---

### Pitfall 5: RBAC Permissions Checked at the Wrong Layer (Object-Level vs. Endpoint-Level vs. Service-Level)

**What goes wrong:**
Django's built-in permission system (`has_perm`, `groups`) checks permissions at the model level, not the object level. Three common mistakes:

**Mistake A: Endpoint-only guard without service-layer check.**
A `@require_role("admin")` decorator on the Django Ninja endpoint correctly blocks anonymous users and non-admins. But a service function called from a Celery task or a management command has no HTTP context, so the guard is bypassed entirely. The data is unprotected when accessed outside the HTTP request cycle.

**Mistake B: Model-level permission without object ownership check.**
`user.has_perm("app.change_post")` checks if the user's role can edit posts in general. It does not check if this specific post belongs to the user. A user with `editor` role can call `PATCH /posts/123/` and modify another user's post if the endpoint only checks the model permission and not `post.owner == request.user`.

**Mistake C: Caching `user.get_all_permissions()` across requests.**
Django caches the permission set on the user object for the duration of the request. If a user's role is changed (e.g., demoted from admin to member), the next request picks up the new role correctly. But if the user object is cached in the session or another cache, the old permission set is served. This is specifically a risk when `django-redis` (already in the stack) is used as the session backend and the user object is serialized into the session.

**How to avoid:**

1. Permission checks must live in the **service layer** (`services.py`), not just in the endpoint guard. The guard is a UX convenience; the service is the security boundary.
2. Object-ownership checks must be explicit:

```python
# services.py
def update_post(requesting_user: User, post_id: int, data: PostUpdateSchema) -> Post:
    post = get_object_or_404(Post, id=post_id)
    if post.owner != requesting_user and not requesting_user.has_perm("posts.change_any_post"):
        raise PermissionDenied("You do not own this post.")
    post.title = data.title
    post.save()
    return post
```

3. Do not cache `user.get_all_permissions()` or the user object beyond a single request cycle. Use `user.refresh_from_db()` before permission checks in Celery tasks.

**Warning signs:**

- Permission checks only in `@require_role` endpoint decorators, not in service functions
- No test that verifies a user cannot edit another user's resource via the API
- Celery tasks that perform privileged operations without any permission check
- `user.get_all_permissions()` result cached in Redis with a TTL > 0

**Phase to address:** RBAC phase. Service-layer permission checks must be established as the primary pattern before any endpoint guard is written.

**Recovery cost:** MEDIUM — adding service-layer checks retroactively is mechanical but requires auditing every service function for missing ownership checks.

**Confidence:** HIGH (Django permissions documentation, django-guardian docs, multiple RBAC security audit reports)

---

### Pitfall 6: Feature Entitlements — Stale Entitlement Cache After Plan Change

**What goes wrong:**
`has_feature(user, "advanced_exports")` is implemented by checking `user.subscription.plan.features["advanced_exports"]`. To avoid hitting the DB on every request, the result is cached in Redis with a TTL of, say, 1 hour.

A user downgrades their plan via Stripe webhook. The webhook fires, the `Subscription.plan` is updated in the DB. But the `has_feature` cache for this user still returns `True` for `advanced_exports` for up to 1 hour. The user continues to access a feature they are no longer paying for.

The inverse is equally damaging: a user upgrades but the cache still returns `False`, making them feel their payment had no effect. This generates support tickets immediately.

**How to avoid:**

1. Cache entitlements by a composite key that includes the plan ID and the subscription's `current_period_end`:

```python
def _cache_key(user_id: int, plan_id: int) -> str:
    return f"entitlements:user:{user_id}:plan:{plan_id}"
```

2. On Stripe webhook processing (when `Subscription.plan` changes), explicitly invalidate the user's entitlement cache:

```python
# In the webhook handler for customer.subscription.updated
old_plan_id = subscription.plan_id
subscription.plan = new_plan
subscription.save()
cache.delete(_cache_key(user_id, old_plan_id))
cache.delete(_cache_key(user_id, new_plan.id))
```

3. Keep cache TTL short (5-15 minutes) as a backstop even with explicit invalidation.

4. In the `BILLING_PLANS` settings dict, features are defined at the plan level, not the user level — this means the cache key does NOT need to be per-user if the plan hasn't changed. One cache entry per plan is sufficient.

**Warning signs:**

- `has_feature` result cached with TTL > 30 minutes without explicit invalidation on plan change
- No cache invalidation step in the Stripe webhook handler for subscription updates
- Feature checks query the DB on every request (opposite problem: no caching = N+1 on every page render)
- Users reporting "I upgraded but feature X still doesn't work"

**Phase to address:** Feature Entitlements phase. Cache invalidation strategy must be designed at the same time as the caching strategy.

**Recovery cost:** LOW to fix technically, but HIGH in user trust — users who were incorrectly billed for features they could not access, or who accessed features without paying, create support and refund burden.

**Confidence:** HIGH (Django caching documentation, LaunchDarkly post on feature flag mistakes, multiple SaaS engineering blogs)

---

## Moderate Pitfalls

Mistakes that create bugs, compliance gaps, or significant developer confusion.

---

### Pitfall 7: Transactional Email — SendGrid Suppression List Silently Swallowing Emails

**What goes wrong:**
SendGrid maintains global suppression lists: unsubscribes, bounces, spam reports, and invalid addresses. If a user's email is on any of these lists, SendGrid silently drops the email and returns a `202 Accepted` response to the Django sender. The Celery task completes successfully, Celery reports no error, and the developer sees no indication the email was never delivered.

This is particularly painful for:

- Password reset emails — the user cannot log in and support tickets pile up
- Account verification emails — the user is stuck in an unverified state
- Billing failure notifications — the user is unaware their subscription is at risk

**How to avoid:**

1. Configure SendGrid webhook events for bounces, drops, and spam reports. Write a Django endpoint that receives these events and records them in a `SuppressedEmail` model.
2. Before queuing any Celery email task, check `SuppressedEmail.objects.filter(email=recipient).exists()`. If suppressed, log a warning and skip or alert the team.
3. For critical transactional emails (password reset, billing failure), check suppression before sending and surface a UI-level warning to the user if their email is on the suppression list.
4. Never use a global unsubscribe link for transactional emails — use SendGrid's Unsubscribe Groups so that marketing unsubscribes do not suppress password resets.

**Warning signs:**

- No SendGrid event webhook configured in the Django app
- `send_mail()` or `sg.send()` returns success but user never receives the email
- Support tickets about "I never got my password reset email"
- Using a single global unsubscribe link for all email types

**Phase to address:** Transactional Email phase. Suppression tracking must be implemented alongside the SendGrid adapter.

**Confidence:** MEDIUM-HIGH (SendGrid suppression documentation, multiple Django-SendGrid community reports)

---

### Pitfall 8: Social Auth — OAuth Redirect URI Misconfiguration in Multi-Environment Setup

**What goes wrong:**
Google and GitHub OAuth apps require exact redirect URI registration. In the template's multi-environment setup (local dev, staging, production), developers register only the production redirect URI, then wonder why OAuth fails locally. Or they register `http://localhost:8000` for development and forget to register the staging URL.

Apple is worse: the Apple Service ID requires the exact redirect domain to be registered in the Apple Developer portal. Unlike Google/GitHub, which have a console UI for rapid URI management, Apple changes take 5-15 minutes to propagate and cannot be done programmatically. A staging URL not registered in Apple's portal means Apple OAuth is completely broken on staging.

**How to avoid:**

1. Document all required redirect URIs per environment in the project setup guide:
   - Local: `http://localhost:8000/accounts/google/login/callback/`
   - Staging: `https://staging.yourapp.com/accounts/google/login/callback/`
   - Production: `https://yourapp.com/accounts/google/login/callback/`
2. For Apple: register staging and production domains in the Apple Service ID **before** any testing on those environments. Plan for the propagation delay.
3. Use separate OAuth application credentials per environment (not shared between staging and production) — this prevents a staging misconfiguration from taking down production auth.
4. Add a health-check test that verifies the configured redirect URI matches the expected pattern for the current environment.

**Warning signs:**

- `redirect_uri_mismatch` errors in OAuth provider logs
- Single OAuth app credentials shared across local, staging, and production
- Apple auth working in development but broken on staging

**Phase to address:** Social Auth phase. URI registration checklist must be part of the phase's environment setup documentation.

**Confidence:** HIGH (Google OAuth documentation, Apple Sign In documentation, community experience)

---

### Pitfall 9: GDPR Data Export — Incomplete Export Missing Third-Party Data

**What goes wrong:**
A data export endpoint collects `User`, `Profile`, and app-specific model data via Django's serialization framework. It returns a JSON with all the ORM rows it knows about. But it misses:

1. **Allauth data** — `SocialAccount`, `EmailAddress` rows (the user's connected OAuth accounts and verified emails)
2. **Billing data** — Invoice history, subscription history from the `BillingProfile` tables
3. **PostHog analytics** — Events captured under the user's identity
4. **Celery task history** — If stored in `django-celery-results`

A GDPR data export that returns only 60% of the user's data is a compliance violation (Article 15 — right of access).

**How to avoid:**

1. Write a `UserDataExportService` that aggregates data from all modules with explicit sections:

```python
class UserDataExportService:
    def export(self, user: User) -> dict:
        return {
            "profile": self._export_profile(user),
            "auth": self._export_auth(user),          # EmailAddress, SocialAccount
            "billing": self._export_billing(user),    # BillingProfile, Subscription, Invoice
            "content": self._export_content(user),    # App-specific models
            "export_generated_at": timezone.now().isoformat(),
            "note": "Analytics data retained per privacy policy section 4.2",
        }
```

2. Each module (billing, social auth, RBAC) must register an export hook with the service. The CLI scaffolder's `--without` flags must also clean up the export hooks.
3. Test by creating a user, performing actions that touch every module, then running the export and asserting all sections are present and non-empty.

**Warning signs:**

- Data export endpoint queries only `User` and app-specific models, not `account_emailaddress` or billing tables
- No test verifying export completeness across all installed modules
- Export returns empty `billing` section even when the user has a subscription

**Phase to address:** GDPR Baseline phase. Export completeness is a legal requirement, not a nice-to-have.

**Confidence:** MEDIUM-HIGH (GDPR Article 15 requirement, django-gdpr-assist documentation patterns)

---

### Pitfall 10: GDPR Cookie Consent — Hydration Mismatch in Next.js App Router

**What goes wrong:**
Cookie consent state is stored in `localStorage` (or a cookie read client-side). The consent banner component reads this state on mount. Because the server renders the page without knowing the consent state, the server outputs "show banner" HTML. After hydration, the client reads localStorage and finds the user already consented, so it sets the banner to hidden. This triggers a React hydration mismatch error in Next.js 15 App Router.

A common "fix" is to add `suppressHydrationWarning` to the banner element. This hides the error but does not fix the underlying problem: analytics scripts that depend on consent may fire before the client-side consent check completes, because the scripts are initialized during SSR or early hydration.

**How to avoid:**

1. Render the consent banner as a `"use client"` component that returns `null` on the initial render (server-rendered output is always "no banner"):

```typescript
"use client";

export function CookieConsentBanner() {
  const [mounted, setMounted] = useState(false);
  const [consented, setConsented] = useState<boolean | null>(null);

  useEffect(() => {
    setMounted(true);
    setConsented(getStoredConsent()); // reads localStorage
  }, []);

  if (!mounted || consented !== null) return null; // no flicker, no hydration mismatch

  return <BannerUI onAccept={() => setConsented(true)} onReject={() => setConsented(false)} />;
}
```

2. Initialize PostHog (ObservabilityAdapter) in `opt_out_capturing_by_default: true` mode. Only call `posthog.opt_in_capturing()` after the user consents. This prevents pre-consent analytics firing.
3. Do not use `suppressHydrationWarning` as the fix — it is a smell indicating the SSR/client split is not handled correctly.

**Warning signs:**

- `suppressHydrationWarning` on the consent banner element
- PostHog events appearing in the analytics dashboard for users who have not consented
- React hydration errors in the browser console on pages with the consent banner
- `localStorage` access outside of `useEffect` or event handlers

**Phase to address:** GDPR Baseline phase. Consent-gating analytics must be configured before PostHog is activated in production.

**Confidence:** MEDIUM-HIGH (Next.js hydration error docs, Next.js 15 App Router behavior, GDPR cookie consent implementation guides)

---

### Pitfall 11: RBAC — Role Assignment API Without Privilege Escalation Protection

**What goes wrong:**
A "role assignment" endpoint allows admins to set user roles. Developers implement the endpoint without checking whether the requesting user can assign the target role. A user with `manager` role can call `PATCH /users/123/role` with `{"role": "admin"}`, elevating their own or another user's privileges beyond what their current role permits.

The second form of this mistake: the role assignment endpoint accepts arbitrary role strings rather than validating against a defined role enum. `{"role": "superadmin"}` creates a role that no permission check handles, effectively granting an undefined (and therefore unchecked) level of access.

**How to avoid:**

1. Define a `Role` enum with all valid roles in a single location. The role assignment endpoint validates against this enum.
2. Enforce a role hierarchy: a user can only assign roles at or below their own level. An `admin` can assign `editor` or `viewer` but not `admin` or `owner`.
3. The `owner` role (highest privilege) can only be set during initial setup or via a management command — never via the API.

```python
ROLE_HIERARCHY = ["viewer", "editor", "manager", "admin", "owner"]

def can_assign_role(assigning_user: User, target_role: str) -> bool:
    assigning_level = ROLE_HIERARCHY.index(get_user_role(assigning_user))
    target_level = ROLE_HIERARCHY.index(target_role)
    return assigning_level > target_level  # Must be strictly higher
```

**Warning signs:**

- Role assignment endpoint only checks `is_admin(request.user)` without checking the target role level
- Role stored as a free-form `CharField` without a choices constraint
- No test verifying that a `manager` cannot assign the `admin` role

**Phase to address:** RBAC phase. Role hierarchy and escalation protection must be built into the first version of the assignment endpoint.

**Confidence:** HIGH (standard privilege escalation prevention pattern, OWASP)

---

### Pitfall 12: EmailAdapter Abstraction — HTML Email Rendering Without Plain-Text Fallback

**What goes wrong:**
The `EmailAdapter` sends HTML emails rendered from templates. No plain-text alternative is included. Gmail and Outlook display HTML correctly. But:

1. Some email clients (and corporate security gateways) strip HTML and display raw HTML tags as visible text.
2. GDPR and CAN-SPAM require emails to be readable without HTML rendering.
3. Deliverability scores (SpamAssassin, etc.) penalize HTML-only emails — they have a higher spam score than multipart emails with both HTML and text parts.

**How to avoid:**
Every email sent through the `EmailAdapter` must be `multipart/alternative` with both `text/html` and `text/plain` parts. Django's `EmailMultiAlternatives` handles this:

```python
from django.core.mail import EmailMultiAlternatives

msg = EmailMultiAlternatives(
    subject=subject,
    body=plain_text_body,       # Required — never empty
    from_email=from_email,
    to=[recipient],
)
msg.attach_alternative(html_body, "text/html")
msg.send()
```

Generate the plain-text version from the HTML template either via a separate `.txt` template or via `html2text`. Never use an empty string for `body`.

**Warning signs:**

- `send_mail()` or `EmailMessage` used with only `html_message=` parameter and no `body`
- No `*.txt` template alongside every `*.html` email template
- SpamAssassin score > 5 in deliverability tests

**Phase to address:** Transactional Email phase. The `EmailAdapter` base class must enforce multipart by construction.

**Confidence:** HIGH (CAN-SPAM compliance, SpamAssassin documentation, Django EmailMultiAlternatives docs)

---

## Minor Pitfalls

Annoyances that are easy to fix but easy to overlook during initial implementation.

---

### Pitfall 13: Apple Sign In — Development Build Limitation

Apple Sign In (`expo-apple-authentication`) only works in production builds and TestFlight. It does **not** work in Expo Go or development builds on the simulator without additional configuration. Developers who start Apple auth implementation expecting to test in Expo Go will get a misleading "Apple Sign In is not available on this device" error that has nothing to do with their code.

**Prevention:** Configure the dev environment to show a mock "Sign in with Apple" button that short-circuits to a test account in development builds. Gate real Apple auth behind `Constants.appOwnership === 'standalone'`. Set this expectation in the phase plan before implementation begins.

**Phase to address:** Social Auth (Mobile) phase.

**Confidence:** HIGH (Expo `expo-apple-authentication` docs)

---

### Pitfall 14: RBAC Groups — Django Admin Bypasses All Custom Guards

Django Admin uses Django's built-in `is_staff` and `is_superuser` flags, not the custom `@require_role("admin")` guards applied to Django Ninja endpoints. An `is_staff=True` user has full Django Admin access regardless of their application role. A user with application role `admin` but `is_staff=False` cannot access Django Admin.

These two permission systems are independent and will diverge as the application grows.

**Prevention:** Document clearly that Django Admin access (`is_staff`) is separate from application RBAC. For the template, Django Admin is the superuser-only operational tool; application RBAC governs API access. Never set `is_staff=True` programmatically from the application layer.

**Phase to address:** RBAC phase.

**Confidence:** HIGH (Django permission system documentation)

---

### Pitfall 15: Feature Entitlements — `has_feature` Called in Templates or Serializers Without N+1 Guard

`has_feature(user, key)` may trigger a DB query to load `user.subscription.plan` if the subscription is not already prefetched. Called once in a service function this is fine. Called in a loop (e.g., rendering a list of users each with their feature set) this becomes an N+1 query that the `nplusone` fixture (already in the stack) will catch in tests but not in production if the list view does not use `select_related`.

**Prevention:** The `has_feature` implementation must accept a pre-loaded plan object as an optional parameter, or always be called after a `select_related("subscription__plan")` queryset. Add a note in the function docstring.

**Phase to address:** Feature Entitlements phase.

**Confidence:** HIGH (Django ORM N+1 pattern, confirmed by nplusone's detection mechanism)

---

## Technical Debt Patterns

| Shortcut                                                               | Immediate Benefit    | Long-term Cost                                                                                     | When Acceptable                             |
| ---------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| Use Django's built-in `is_staff` as the sole admin gate                | No RBAC setup needed | Admin access tied to deployment flag, not application logic; grows unmanageable with team          | Never for new projects                      |
| Cache `has_feature` with a long TTL (1h+) and no explicit invalidation | Fewer DB hits        | Users see stale entitlements after plan change; billing disputes                                   | Never                                       |
| Skip plain-text email fallback                                         | Faster template work | Lower deliverability, CAN-SPAM non-compliance                                                      | Never                                       |
| Use `user.delete()` directly without a `UserDeletionService`           | Less code            | GDPR erasure violations; orphaned data in Stripe, PostHog                                          | Never for GDPR-covered users                |
| Single Apple OAuth credential for all environments                     | Simpler setup        | Staging misconfiguration can affect production; Apple's 15-minute propagation delay blocks testing | Only in greenfield before staging exists    |
| Dispatch Celery tasks without `transaction.on_commit()`                | Simpler code         | Race condition: task runs before DB row is visible                                                 | Only in tests with `task_always_eager=True` |

---

## Integration Gotchas

| Integration                    | Common Mistake                                                                         | Correct Approach                                                                             |
| ------------------------------ | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| SendGrid                       | Using global unsubscribe link for transactional emails (password reset, billing alert) | Use Unsubscribe Groups — marketing opt-out must not suppress transactional emails            |
| SendGrid                       | Ignoring 202 Accepted as success; not handling bounce/drop events                      | Configure event webhook; record suppressed addresses; surface to support team                |
| Apple Sign In                  | Passing native Expo identity token to Allauth's standard social token endpoint         | Build a dedicated native token verification endpoint; verify JWT against Apple's public keys |
| Google OAuth                   | Same OAuth app credentials for dev, staging, and production                            | Separate credentials per environment; all redirect URIs registered explicitly                |
| PostHog (ObservabilityAdapter) | `identify()` called on every request; `delete()` never called on user erasure          | Call `identify()` once on signup; add `posthog.delete()` to `UserDeletionService`            |
| Stripe + GDPR                  | `user.delete()` without calling `stripe.Customer.delete()`                             | Orchestrate Stripe deletion before ORM deletion in `UserDeletionService`                     |
| django-allauth social auth     | `SOCIALACCOUNT_EMAIL_AUTHENTICATION=False` (default) for trusted providers             | Set `True` + `AUTO_CONNECT=True` for Google/GitHub; write custom adapter for Apple           |

---

## Performance Traps

| Trap                                                                                | Symptoms                                                              | Prevention                                                                          | When It Breaks                           |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------- |
| `has_feature(user, key)` in a list view without `select_related`                    | N+1 queries on user list pages; `nplusone` failures in tests          | Always `select_related("subscription__plan")` before calling `has_feature` in loops | At ~50 users on a single page render     |
| Sending emails synchronously in the request cycle                                   | p99 API response time spikes on email-triggering endpoints            | All email sends via Celery task with `transaction.on_commit()`                      | Immediately if SendGrid is slow (>200ms) |
| GDPR data export building JSON in memory for large accounts                         | Memory exhaustion on Celery worker for power users with years of data | Stream export to a file/S3, return download URL rather than inline JSON             | At ~10,000 records per export            |
| Fetching Apple public keys from `appleid.apple.com/auth/keys` on every auth attempt | High latency on Apple login; failure if Apple CDN is slow             | Cache public keys in Redis with TTL of 12-24 hours                                  | Any Apple CDN degradation                |

---

## Security Mistakes

| Mistake                                                                                          | Risk                                                                                                     | Prevention                                                                                                     |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Role stored as free-form string in DB without choices validation                                 | Undefined roles bypass all permission checks                                                             | Use a `Role` enum with `choices=` constraint; validate on assignment                                           |
| Privilege escalation via role assignment API (manager assigns admin)                             | Horizontal privilege escalation                                                                          | Enforce role hierarchy: assigning user's level must be > target role level                                     |
| Social account auto-connect without verifying the provider confirmed the email                   | Account takeover: attacker adds your email to their social account, auto-connects to your Django account | Only auto-connect for providers that guarantee email verification (Google, GitHub); not for Apple relay emails |
| Serving Apple's private key (`AuthKey_*.p8`) from an environment variable not excluded from logs | Private key leaked in structured logs                                                                    | Ensure `SECRET_KEY`, `APPLE_PRIVATE_KEY` are masked in structlog's `BoundLogger`                               |
| GDPR deletion without verifying all cascade paths                                                | Right-to-erasure violation                                                                               | `UserDeletionService` with explicit external service cleanup; post-deletion assertion test                     |
| Feature entitlement check only at the API endpoint, not in service layer                         | Entitlement bypass via direct service or task invocation                                                 | Service-layer entitlement check is the security boundary; endpoint check is UX only                            |

---

## UX Pitfalls

| Pitfall                                                           | User Impact                                                                | Better Approach                                                                                      |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Social auth "email already exists" error with no merge path       | User cannot log in with their preferred method; creates duplicate accounts | Auto-connect for verified providers; show "Link your Google account" prompt for unverified conflicts |
| Cookie consent banner causes hydration flicker on every page load | Jarring visual glitch; reduces trust                                       | SSR renders nothing for banner; client renders banner only on first mount                            |
| Apple Sign In name is blank on all logins after first             | User profile shows empty name fields                                       | Persist `fullName` on first auth; mark as immutable afterward                                        |
| Password reset email silently suppressed by SendGrid              | User cannot log in; calls support                                          | Check suppression list before queuing; surface "email delivery issue" warning in UI                  |
| Downgraded plan still shows premium features for up to 1 hour     | User confusion; potential for chargeback disputes                          | Explicitly invalidate entitlement cache on plan change webhook; keep TTL ≤ 15 minutes                |
| Role change takes effect immediately without warning              | Admin accidentally locks themselves out                                    | Show confirmation dialog for role changes that would affect the requesting user                      |

---

## "Looks Done But Isn't" Checklist

- [ ] **Apple Sign In:** Does the native Expo token go to a dedicated verification endpoint (not Allauth's standard social token flow)? Is `fullName` persisted on first auth?
- [ ] **Social email conflict:** Does the `SocialAccountAdapter.pre_social_login()` method handle the case where an email already exists in a password account? Is there a test for this scenario?
- [ ] **Celery email dispatch:** Is every `send_*.delay()` call wrapped in `transaction.on_commit()`? Check every file that calls `.delay()` after a `.create()` or `.save()`.
- [ ] **GDPR erasure completeness:** Does `UserDeletionService` call `stripe.Customer.delete()`, `posthog.delete()`, and verify no orphaned `SocialAccount` or `EmailAddress` rows remain?
- [ ] **GDPR export completeness:** Does the export include `EmailAddress`, `SocialAccount`, `BillingProfile`, `Subscription`, and `Invoice` data in addition to the core `User` and profile models?
- [ ] **Cookie consent + PostHog:** Is PostHog initialized with `opt_out_capturing_by_default=True`? Is `opt_in_capturing()` called only after explicit user consent?
- [ ] **RBAC service-layer checks:** Is every privileged service function protected by an ownership or role check, not just the endpoint decorator?
- [ ] **Role escalation:** Does the role assignment endpoint reject attempts to assign a role equal to or higher than the assigning user's own role?
- [ ] **Entitlement cache invalidation:** Is `cache.delete()` called for the user's entitlement key in the Stripe webhook handler when the subscription plan changes?
- [ ] **Email plain-text fallback:** Does every email template have a corresponding `.txt` template? Is `body` never passed as an empty string?
- [ ] **SendGrid suppression:** Is there a webhook endpoint receiving SendGrid bounce/drop events? Is the suppression list checked before queuing critical emails?
- [ ] **OAuth redirect URIs:** Are all redirect URIs registered for all environments (local, staging, production) in each provider's developer console?

---

## Recovery Strategies

| Pitfall                                                   | Recovery Cost | Recovery Steps                                                                                   |
| --------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------ |
| Apple native token mismatch (built wrong endpoint)        | HIGH          | Rebuild dedicated native token endpoint; update Expo auth module; retest on physical device      |
| Duplicate accounts from social email conflict             | HIGH          | Write a merge migration: identify pairs, copy data to older account, delete newer, update FKs    |
| Celery tasks dispatched without `on_commit` (emails lost) | MEDIUM        | Add `on_commit` wrappers; replay lost tasks by querying DB for records created in the gap        |
| GDPR erasure missing Stripe/PostHog data                  | HIGH          | Retroactively call external deletion APIs for all previously deleted users; log as incident      |
| Entitlement cache stale after plan change                 | LOW           | Flush Redis `entitlements:*` namespace; add explicit invalidation; notify affected users         |
| Role escalation exploit discovered                        | HIGH          | Audit role assignment history; demote unauthorized admins; patch endpoint; security disclosure   |
| SendGrid suppression silently swallowing emails           | MEDIUM        | Pull suppression list from SendGrid API; identify affected users; resend via alternative channel |

---

## Pitfall-to-Phase Mapping

| Pitfall                                            | Prevention Phase     | Verification                                                                                                     |
| -------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Apple native vs. web token (Pitfall 1)             | Social Auth          | Test on physical iOS device with native Expo build; verify `aud` claim matches bundle ID                         |
| Email account merge conflict (Pitfall 2)           | Social Auth          | Test: create password account → sign in with Google → verify single user object returned                         |
| Celery task before DB commit (Pitfall 3)           | Transactional Email  | Test: inspect task execution time relative to transaction commit; simulate with `sleep()` in view                |
| GDPR orphaned data in third parties (Pitfall 4)    | GDPR Baseline        | Test: delete user → assert no rows in `socialaccount_*`, `account_*`, billing tables; verify Stripe customer 404 |
| RBAC wrong layer (Pitfall 5)                       | RBAC                 | Test: call service functions directly (bypassing HTTP); verify permission checks still fire                      |
| Entitlement cache stale (Pitfall 6)                | Feature Entitlements | Test: change plan → immediately check `has_feature` → verify result reflects new plan                            |
| SendGrid suppression swallowing emails (Pitfall 7) | Transactional Email  | Configure SendGrid event webhook in test mode; verify bounce events are recorded                                 |
| OAuth redirect URI misconfiguration (Pitfall 8)    | Social Auth          | Checklist: verify URIs registered in all three environments before merging                                       |
| Incomplete GDPR export (Pitfall 9)                 | GDPR Baseline        | Test: create user with activity in all modules → export → assert all sections present and non-empty              |
| Cookie consent hydration mismatch (Pitfall 10)     | GDPR Baseline        | Test: render consent banner in SSR mode → assert no hydration error in browser console                           |
| Role escalation vulnerability (Pitfall 11)         | RBAC                 | Test: manager attempts to assign admin role → assert 403                                                         |
| Email without plain-text fallback (Pitfall 12)     | Transactional Email  | Test: inspect `EmailMultiAlternatives` object → assert both `body` and `html` parts present                      |

---

## Sources

- [django-allauth Apple provider documentation](https://docs.allauth.org/en/dev/socialaccount/providers/apple.html) — native vs. web token distinction (confidence: HIGH)
- [Expo expo-apple-authentication documentation](https://docs.expo.dev/versions/latest/sdk/apple-authentication/) — managed workflow limitations, first-auth name constraint (confidence: HIGH)
- [django-allauth GitHub issue #418 — Social account auto-connect](https://github.com/pennersr/django-allauth/issues/418) — email conflict patterns (confidence: HIGH)
- [django-allauth headless token strategies](https://docs.allauth.org/en/dev/headless/tokens.html) — token strategy for headless mode (confidence: HIGH)
- [Apple Sign In with Expo + Golang 2025 guide](https://medium.com/@meszmate/apple-sign-in-with-expo-golang-complete-2025-guide-to-server-side-oauth-jwt-validation-and-01677dc27e08) — native JWT verification patterns (confidence: MEDIUM)
- [Implementing Sign in with Apple with Expo — DEV Community](https://dev.to/bendix/implementing-sign-in-with-apple-with-a-managed-expo-workflow-and-a-nest-js-backend-8ja) — managed workflow integration patterns (confidence: MEDIUM)
- [Apple Developer Forum — Mobile and Web under the same bundle](https://developer.apple.com/forums/thread/706607) — two client_ids required (confidence: HIGH)
- Django documentation — `transaction.on_commit()`, `ATOMIC_REQUESTS`, `EmailMultiAlternatives` (confidence: HIGH)
- [django-gdpr-assist documentation](https://django-gdpr-assist.readthedocs.io/) — third-party model registration, anonymization vs deletion (confidence: HIGH)
- [GDPR on Django's model Collector](https://blog.eleni.co/garden/gdpr-on-top-of-django-s-model-collector/) — cascade completeness analysis (confidence: MEDIUM)
- [SendGrid suppression documentation](https://www.twilio.com/docs/sendgrid/ui/sending-email/index-suppressions) — suppression list behavior, event webhooks (confidence: HIGH)
- [SendGrid List-Unsubscribe docs](https://www.twilio.com/docs/sendgrid/ui/sending-email/list-unsubscribe) — global vs. group unsubscribe distinction (confidence: HIGH)
- [Next.js hydration error documentation](https://nextjs.org/docs/messages/react-hydration-error) — cookie consent hydration mismatch prevention (confidence: HIGH)
- [React Cookie Consent GDPR guide for Next.js](https://www.cookietrust.io/react-nextjs-cookie-consent-gdpr-guide/) — consent banner SSR pattern (confidence: MEDIUM)
- [7 Feature Flag Mistakes — LaunchDarkly](https://launchdarkly.com/blog/feature-flag-mistakes/) — flag reuse, long-lived flags, cache invalidation (confidence: MEDIUM)
- [Django RBAC implementation guide — Permit.io](https://www.permit.io/blog/how-to-implement-role-based-access-control-rbac-into-a-django-application) — role hierarchy, escalation prevention (confidence: MEDIUM)
- [Django Ninja Extra permissions documentation](https://eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/) — endpoint vs. service-layer guard distinction (confidence: HIGH)
- Training data — Django ORM cascade behavior, Celery task timing, RBAC patterns (confidence: MEDIUM — corroborated by search results)

---

_Pitfalls research for: v1.3 SaaS Functional Baseline (transactional email, social auth, GDPR baseline, RBAC, feature entitlements)_
_Researched: 2026-03-11_
_Supersedes: v1.1 billing PITFALLS.md for v1.3-specific concerns only. Billing pitfalls remain valid for billing phases._
