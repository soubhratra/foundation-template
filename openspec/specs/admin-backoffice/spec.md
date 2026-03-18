## Requirements

### Requirement: django-unfold Theme Across All ModelAdmins

The Django admin interface SHALL use the `django-unfold` theme with a configured navigation sidebar covering all B2B and existing domains.

#### Scenario: Admin renders with unfold theme

- **WHEN** a staff user visits the Django admin
- **THEN** the interface SHALL render with the django-unfold theme (not Django's default admin)
- **AND** a navigation sidebar SHALL be displayed with sections for all domains

#### Scenario: Sidebar covers all B2B and existing domain models

- **WHEN** a staff user views the admin sidebar
- **THEN** it SHALL include sections for: B2B (Organizations, Memberships, API Keys, Webhooks, Audit Log), Users & Auth, Billing, and System (Celery Beat/Results)
- **AND** Heroicons (outline style) SHALL be used for section headers and model items

#### Scenario: All domain ModelAdmins inherit from UnfoldModelAdmin

- **WHEN** any model is registered in the Django admin
- **THEN** its `ModelAdmin` class SHALL inherit from `UnfoldModelAdmin` (not Django's base `ModelAdmin`)
- **AND** this applies to existing domains (`accounts`, `billing`) as well as new B2B domains

### Requirement: Staff Impersonation via django-hijack

Staff users SHALL be able to impersonate non-staff, non-superuser accounts with a persistent banner and full audit trail.

#### Scenario: Staff impersonates a user from the admin

- **WHEN** a staff user navigates to a user's change page at `/admin/accounts/user/{id}/change/`
- **AND** clicks the "Impersonate" button
- **THEN** the staff user SHALL be signed in as the target user in the main web app
- **AND** a persistent banner SHALL be visible on every page showing the impersonated user and a "Release" button

#### Scenario: Impersonation restricted to non-staff, non-superuser targets

- **WHEN** a staff user attempts to impersonate another staff user or a superuser
- **THEN** the impersonation SHALL be rejected
- **AND** the system SHALL return an error

#### Scenario: Impersonation events written to audit log

- **WHEN** a staff user starts or ends an impersonation session
- **THEN** an `AuditLog` entry SHALL be written with the `impersonator` FK populated
- **AND** this entry SHALL be visible to staff in the admin
- **AND** this entry SHALL NOT appear in org-level audit log queries

#### Scenario: Release redirects staff back to impersonated user's admin page

- **WHEN** a staff user clicks "Release" in the impersonation banner
- **THEN** the staff user SHALL be redirected to the impersonated user's admin change page
- **AND** the staff user's own session SHALL be restored

## Implementation Decisions

### Why django-unfold (not django-jazzmin or a custom theme)

`django-unfold` provides a modern Tailwind-based admin that ships with Heroicons natively and has active maintenance. It requires minimal configuration for the navigation sidebar (`UNFOLD = {...}` dict in `base.py`). `django-jazzmin` is jQuery-based and was deprioritized; custom admin themes are high-maintenance.

**Alternative rejected:** django-jazzmin — Bootstrap-based, older UX patterns, less active development trajectory.

### Why `UNFOLD` config lives in `config/settings/base.py`

Consistent with how `SIMPLE_JWT`, `CELERY_*`, and other third-party configs are defined in this codebase — all in `base.py`. Keeping it inline (not in a separate file) makes it discoverable and avoids additional import indirection.

### Why the impersonation trigger is on the user change page only (not a list action)

Placing the "Impersonate" button on the user detail page (`/admin/accounts/user/{id}/change/`) requires staff to navigate to a specific user before impersonating. This intentional friction prevents accidental impersonation from a list view where a single misclick could impersonate the wrong user. Support workflows naturally involve pulling up a user's detail page first.

### Why django-hijack's default banner is used without customization

The built-in `HIJACK_INSERT_BEFORE` banner injection meets the requirement (shows impersonated user info + Release button) without custom templates. Customizing the banner is a product-level decision — the template ships a functional baseline.

### Why `HIJACK_LOGOUT_REDIRECT_URL` points back to the impersonated user's admin page

After releasing impersonation, staff are returned to the admin context they came from — the user's change page. This matches the natural support workflow (investigate → impersonate → reproduce → release → continue investigation). An arbitrary redirect (e.g., admin homepage) would lose the context of which user was being investigated.

### Why impersonation audit entries are excluded from org-level queries

Impersonation is a staff action, not an org action. Exposing impersonation events to org admins would: (1) reveal internal support tooling to customers, (2) cause confusion about "who" performed an action (staff-as-user vs. actual user). Staff-only visibility via the admin is the correct access level.
