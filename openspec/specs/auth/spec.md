# Authentication Extensions

> Extends the base authentication specification with billing fields and social auth infrastructure. For the core dual-auth strategy (session cookies, JWT, all auth flows, CSRF), see `openspec/specs/foundation/auth.md`.

## Overview

`foundation/auth.md` defines the complete authentication architecture for the template: Django Allauth in headless mode, session cookies for web, JWT for mobile, all signup/login/logout/password-reset flows, token refresh, and CSRF handling. That spec is the source of truth and should be read first.

This spec adds two sets of extensions introduced in later milestones:

1. **Billing fields** — `stripe_customer_id` and `subscription_status` on the User model, surfaced in auth and current-user responses so frontends can gate UI without a separate billing API call.
2. **Social auth base infrastructure** — `allauth.socialaccount` must be installed unconditionally (it owns the social account data model), with providers registered conditionally via `_configure_social_providers()`. The `FoundationSocialAccountAdapter` enforces email auto-merge. Provider-specific flows (Google, GitHub, Apple OAuth) are in `openspec/specs/social-auth/spec.md`.

## Requirements

### Requirement: User model billing fields

The `accounts.User` model SHALL include two new fields:

- `stripe_customer_id`: `CharField(max_length=255, blank=True, null=True, unique=True, db_index=True)` — the Stripe Customer ID (`cus_...`). `null` until the user initiates their first checkout.
- `subscription_status`: `CharField(max_length=50, default="none")` — denormalized subscription state. Valid values: `"none"`, `"trialing"`, `"active"`, `"past_due"`, `"canceled"`. Updated by the Stripe webhook handler; NOT written directly by user-facing endpoints.

Both fields MUST be added via a Django migration (`accounts/migrations/0002_user_billing_fields.py` or next in sequence).

#### Scenario: New user has default billing state

- **WHEN** a new user account is created
- **THEN** `stripe_customer_id` is `null` and `subscription_status` is `"none"`

#### Scenario: stripe_customer_id uniqueness is enforced

- **WHEN** two users are assigned the same `stripe_customer_id`
- **THEN** a database integrity error is raised

### Requirement: subscription_status included in auth responses

The authenticated user response schema SHALL include `subscription_status`. This applies to:

- The session/token response after login
- The `GET /api/auth/me/` (or equivalent current-user) endpoint

The field MUST be read from `User.subscription_status` (the local denormalized value) — no live Stripe API call is made during auth responses.

#### Scenario: Login response includes subscription status

- **WHEN** a user authenticates successfully
- **THEN** the response body includes `"subscription_status": "<value>"` alongside other user fields

#### Scenario: Current-user endpoint includes subscription status

- **WHEN** an authenticated user calls `GET /api/auth/me/`
- **THEN** the response includes `"subscription_status": "<current value>"`

### Requirement: Social Account Provider Installation

The authentication system SHALL support social login by installing `allauth.socialaccount` unconditionally, with provider apps registered conditionally based on environment variables.

#### Scenario: allauth.socialaccount is always installed

- **WHEN** the Django application starts
- **THEN** `"allauth.socialaccount"` SHALL appear in `INSTALLED_APPS` as a static unconditional entry
- **AND** it SHALL NOT carry a `# SOCIAL AUTH MODULE` sentinel comment (it is always required for the social account data model, regardless of which providers are active)

#### Scenario: Provider apps are conditionally registered

- **WHEN** the social auth module is active
- **THEN** `_configure_social_providers()` SHALL conditionally append the following to `INSTALLED_APPS` (each with `# SOCIAL AUTH MODULE` comment):
  - `"allauth.socialaccount.providers.google"` — only when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
  - `"allauth.socialaccount.providers.github"` — only when `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set
  - `"allauth.socialaccount.providers.apple"` — only when Apple credentials are set
- **AND** the `# SOCIAL AUTH MODULE` / `# END SOCIAL AUTH MODULE` fence in `base.py` wraps the `_configure_social_providers` function and its call site

#### Scenario: SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT is enabled

- **WHEN** social auth is active
- **THEN** `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True` SHALL be set
- **AND** this SHALL enable automatic merging of social logins with existing accounts that share the same verified email

### Requirement: Social Auth Adapter Override

The system SHALL use a custom `FoundationSocialAccountAdapter` that extends allauth's `DefaultSocialAccountAdapter` to enforce email auto-connect behavior.

#### Scenario: Adapter normalizes can_authenticate_by_email return type

- **WHEN** `can_authenticate_by_email()` is called on the adapter
- **THEN** the return value SHALL be wrapped in `bool()` to normalize allauth's raw settings value (which may be a non-boolean in test environments)

## Implementation Decisions

### Why billing fields on User (not on a separate Profile model)

`stripe_customer_id` and `subscription_status` are read on every authenticated request (surfaced in auth responses). An additional JOIN to a Profile model on every session/token response would add unnecessary query cost. Denormalized fields on the User model are appropriate given their high read frequency and low write frequency (only updated by Stripe webhook handler).

### Why subscription_status is denormalized (not live from Stripe)

Live Stripe API calls during auth responses would add ~200–400ms latency and create a hard dependency on Stripe availability for every login. The denormalized `subscription_status` field is updated asynchronously by the webhook handler; a stale value window (time between webhook delivery and next login) is acceptable for the template's use case.

### Why allauth.socialaccount is always installed (not gated by SOCIAL_AUTH_MODULE)

`allauth.socialaccount` owns the `SocialAccount` and `SocialToken` database models. These models must exist even when no providers are active — removing them via scaffolder would require dropping tables that may have existing data in a production database. The app is safe to install with zero providers configured. Provider apps (`providers.google`, etc.) are the things that are conditionally installed.

### Why \_configure_social_providers() is a pure function

Pure function (accepts an env dict, returns settings) makes the social provider registration logic unit-testable without triggering Django settings imports. Tests can call it with arbitrary dicts without mocking `os.environ` or touching `settings`.
