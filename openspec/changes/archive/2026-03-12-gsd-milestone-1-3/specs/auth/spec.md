## ADDED Requirements

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
