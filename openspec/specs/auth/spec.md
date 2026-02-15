## ADDED Requirements

### Requirement: Django Allauth Headless Mode Configuration
The authentication system SHALL use Django Allauth in headless mode to provide API-driven authentication for both web and mobile platforms.

#### Scenario: Django Allauth installed and configured
- **WHEN** the Django application starts
- **THEN** Django Allauth headless mode MUST be enabled with `HEADLESS_ONLY = True`
- **AND** the account middleware MUST be installed in the middleware stack
- **AND** email-based authentication MUST be configured as the primary authentication method
- **AND** mandatory email verification MUST be enabled in production

#### Scenario: Frontend redirect URLs configured
- **WHEN** Allauth sends verification or password reset emails
- **THEN** the email links MUST point to frontend URLs defined in `HEADLESS_FRONTEND_URLS`
- **AND** email confirmation links MUST redirect to `{FRONTEND_URL}/auth/verify-email/{key}`
- **AND** password reset links MUST redirect to `{FRONTEND_URL}/auth/reset-password/{key}`

### Requirement: Dual Authentication Strategy
The system SHALL support dual authentication strategies: session cookies for web browsers and JWT tokens for mobile applications.

#### Scenario: Web client authenticates with session cookies
- **WHEN** a Next.js web client submits login credentials
- **THEN** Django MUST create a server-side session
- **AND** an httpOnly session cookie MUST be set in the response
- **AND** subsequent requests MUST include the session cookie automatically
- **AND** CSRF tokens MUST be validated for all mutation requests

#### Scenario: Mobile client authenticates with JWT tokens
- **WHEN** an Expo mobile client submits login credentials
- **THEN** Django MUST issue both access and refresh JWT tokens
- **AND** the tokens MUST be stored in expo-secure-store (Keychain/Keystore)
- **AND** API requests MUST include the access token in the `Authorization: Bearer` header
- **AND** CSRF validation MUST NOT apply to JWT-authenticated requests

#### Scenario: Next.js middleware enforces authentication
- **WHEN** a user navigates to a protected page on the web app
- **THEN** Next.js middleware MUST read the session cookie from the request
- **AND** unauthenticated users MUST be redirected to `/auth/login`
- **AND** the original URL MUST be preserved as a `redirect` query parameter

### Requirement: User Signup with Email Verification
The system SHALL implement user signup with mandatory email verification before granting access to authenticated endpoints.

#### Scenario: User completes signup form
- **WHEN** a user submits the signup form with email, password, first_name, and last_name
- **THEN** Django Allauth MUST create a new user account
- **AND** a verification email MUST be sent with a confirmation link
- **AND** the API MUST return 200 with user data and authentication credentials
- **AND** the user MUST be shown a "check your email" message

#### Scenario: User clicks email verification link
- **WHEN** a user clicks the verification link from the email
- **THEN** the frontend MUST send the verification key to `/api/v1/auth/verify-email`
- **AND** Django Allauth MUST mark the email as verified
- **AND** the user MUST be redirected to the dashboard

#### Scenario: Unverified user attempts to access protected endpoints
- **WHEN** a user with unverified email attempts to access authenticated endpoints in production
- **THEN** the API MUST return 403 with error code `email_not_verified`
- **AND** the frontend MUST display a message prompting email verification

### Requirement: Password Reset Flow
The system SHALL provide a secure password reset flow that sends reset links via email.

#### Scenario: User requests password reset
- **WHEN** a user submits their email address on the password reset page
- **THEN** Django Allauth MUST send a password reset email with a unique key
- **AND** the reset link MUST point to `{FRONTEND_URL}/auth/reset-password/{key}`
- **AND** the user MUST see a "check your email" confirmation message

#### Scenario: User submits new password with reset key
- **WHEN** a user submits a new password via the reset link
- **THEN** the frontend MUST send the key and new password to `/api/v1/auth/password/reset/confirm`
- **AND** Django Allauth MUST validate the key and update the password
- **AND** the user MUST be redirected to the login page

### Requirement: JWT Token Refresh Flow
The mobile application SHALL implement transparent token refresh to maintain user sessions without manual re-authentication.

#### Scenario: API request with expired access token
- **WHEN** a mobile client makes an API request with an expired access token
- **THEN** the API MUST return 401 Unauthorized
- **AND** the API client interceptor MUST catch the 401 response
- **AND** the interceptor MUST send the refresh token to `/api/v1/auth/token/refresh`
- **AND** Django MUST return a new access token
- **AND** the new token MUST be stored in expo-secure-store
- **AND** the original request MUST be retried with the new access token

#### Scenario: Refresh token is expired or invalid
- **WHEN** the token refresh request returns 401
- **THEN** the API client MUST clear all tokens from expo-secure-store
- **AND** the user MUST be navigated to the login screen
- **AND** the original request MUST fail with an authentication error

### Requirement: CSRF Protection for Session-Based Authentication
The web application SHALL implement CSRF protection for all mutation requests using session-based authentication.

#### Scenario: Web client sends POST request with CSRF token
- **WHEN** a web client sends a POST, PATCH, or DELETE request to the Django API
- **THEN** the client MUST read the CSRF token from the `csrftoken` cookie
- **AND** the token MUST be included in the `X-CSRFToken` request header
- **AND** Django MUST validate the token before processing the request
- **AND** requests with invalid or missing CSRF tokens MUST be rejected with 403

#### Scenario: Mobile client sends POST request without CSRF token
- **WHEN** a mobile client sends a POST request using JWT Bearer token authentication
- **THEN** CSRF validation MUST NOT apply to the request
- **AND** the request MUST proceed if the JWT is valid
