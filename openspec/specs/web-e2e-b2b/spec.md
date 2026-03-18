## Requirements

### Requirement: E2E social auth redirect tests

The Playwright suite SHALL include tests verifying that OAuth provider buttons are present and initiate the correct redirect — no live OAuth credentials are required.

#### Scenario: Google OAuth button present on login page

- **WHEN** a guest user navigates to the login page
- **THEN** a "Continue with Google" button (or equivalent) MUST be visible

#### Scenario: GitHub OAuth button present on login page

- **WHEN** a guest user navigates to the login page
- **THEN** a "Continue with GitHub" button (or equivalent) MUST be visible

#### Scenario: Google OAuth button triggers correct redirect

- **WHEN** a guest user clicks the Google OAuth button
- **THEN** the browser MUST navigate to a URL starting with `https://accounts.google.com`
- **THEN** the redirect URL MUST include a `redirect_uri` parameter pointing back to the app's OAuth callback route

#### Scenario: GitHub OAuth button triggers correct redirect

- **WHEN** a guest user clicks the GitHub OAuth button
- **THEN** the browser MUST navigate to a URL starting with `https://github.com/login/oauth`

### Requirement: E2E RBAC access control tests

The Playwright suite SHALL include tests verifying that role-based access control is enforced at the browser level.

#### Scenario: Regular user blocked from admin route

- **WHEN** an authenticated user without the admin role navigates to an admin-only route
- **THEN** the response status MUST be 403, OR the browser MUST redirect to a "forbidden" or "not found" page
- **THEN** the admin-only content MUST NOT be rendered

#### Scenario: Admin user can access admin route

- **WHEN** an authenticated user with the admin role navigates to the same admin-only route
- **THEN** the page MUST render without a 403 or redirect

### Requirement: E2E organization management tests

The Playwright suite SHALL include tests for the core organization lifecycle visible in the UI.

#### Scenario: Create organization succeeds

- **WHEN** an authenticated user submits the "Create organization" form with a unique name
- **THEN** the new organization MUST appear in the user's organization list
- **THEN** the user MUST be shown as the owner of the new organization

#### Scenario: Invite flow creates pending member

- **WHEN** an org owner submits an invitation form with a valid email address
- **THEN** the invited email MUST appear in the org member list with a "Pending" status indicator
- **THEN** the invitation MUST NOT immediately grant membership

### Requirement: E2E API key management tests

The Playwright suite SHALL include tests verifying the API key lifecycle in the UI.

#### Scenario: Create key displays raw value once

- **WHEN** an authenticated user creates a new API key
- **THEN** the raw key value MUST be displayed on screen exactly once immediately after creation
- **THEN** the UI MUST indicate that the raw key will not be shown again

#### Scenario: Key appears masked in key list

- **WHEN** the user navigates to the API keys list after creating a key
- **THEN** the key MUST appear with its value masked (e.g., `sk-****1234`)
- **THEN** the raw key value MUST NOT be visible in the list

#### Scenario: Delete key removes it from list

- **WHEN** the user deletes an API key
- **THEN** the key MUST no longer appear in the API keys list
- **THEN** the delete action MUST NOT require a page refresh to reflect the removal

### Requirement: E2E webhook endpoint management tests

The Playwright suite SHALL include tests for outbound webhook endpoint management in the UI.

#### Scenario: Register webhook endpoint appears in list

- **WHEN** an authenticated user registers a new webhook endpoint URL
- **THEN** the endpoint MUST appear in the webhook endpoint list
- **THEN** the displayed URL MUST match the registered URL

#### Scenario: Delete webhook endpoint removes from list

- **WHEN** an authenticated user deletes a webhook endpoint
- **THEN** the endpoint MUST no longer appear in the webhook list

### Requirement: E2E audit log display tests

The Playwright suite SHALL include tests verifying that audit log entries are visible to admin users with the required fields.

#### Scenario: Audit log entry shows actor, action, and timestamp

- **WHEN** an admin user navigates to the audit log page
- **THEN** at least one audit log entry MUST be visible
- **THEN** each visible entry MUST display: actor identity (username or email), action type, and a timestamp
- **THEN** entries MUST be ordered with the most recent first
