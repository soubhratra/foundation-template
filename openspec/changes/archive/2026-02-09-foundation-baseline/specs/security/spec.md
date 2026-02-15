## ADDED Requirements

### Requirement: Dual Authentication Strategy with Secure Storage
The system SHALL implement session cookies for web and JWT tokens for mobile, with platform-appropriate secure storage mechanisms.

#### Scenario: Web session cookie configuration
- **WHEN** a user logs in on the Next.js web app
- **THEN** Django MUST set a session cookie with `httpOnly=True`, `Secure=True` (in production), and `SameSite=Lax`
- **THEN** the cookie MUST NOT be accessible via JavaScript `document.cookie`
- **THEN** the cookie MUST only be sent over HTTPS in production

#### Scenario: Mobile JWT storage
- **WHEN** a user logs in on the Expo mobile app
- **THEN** the access token MUST be stored in `expo-secure-store` under key `auth_access_token`
- **THEN** the refresh token MUST be stored in `expo-secure-store` under key `auth_refresh_token`
- **THEN** tokens MUST NOT be stored in `localStorage`, `sessionStorage`, or `AsyncStorage`

### Requirement: CSRF Protection for Session-Based Auth
The web application SHALL enforce CSRF protection for all state-changing requests using session authentication.

#### Scenario: CSRF token validation on form submission
- **WHEN** a logged-in web user submits a form that changes server state
- **THEN** the request MUST include the CSRF token in the `X-CSRFToken` header
- **THEN** Django MUST validate the CSRF token against the cookie
- **THEN** if the token is missing or invalid, Django MUST return HTTP 403

#### Scenario: Cross-site request attack prevention
- **WHEN** a malicious website attempts to submit a POST request to the Django API with a user's session cookie
- **THEN** the request MUST lack a valid CSRF token (attacker cannot read the CSRF cookie from different origin)
- **THEN** Django MUST reject the request with HTTP 403
- **THEN** no state change MUST occur on the server

### Requirement: CORS Policy with Explicit Allowed Origins
The Django API SHALL enforce CORS policy with explicitly allowed origins, never allowing all origins in production.

#### Scenario: CORS allowed origins in development
- **WHEN** Django runs in development mode
- **THEN** `CORS_ALLOWED_ORIGINS` MUST include `http://localhost:3000` and `http://localhost:8081`
- **THEN** `CORS_ALLOW_CREDENTIALS` MUST be `True` for session cookie auth

#### Scenario: CORS denied for unlisted origin
- **WHEN** a request arrives from an origin not in `CORS_ALLOWED_ORIGINS`
- **THEN** the Django CORS middleware MUST reject the request
- **THEN** the browser MUST NOT allow the response to be read by the requesting script

### Requirement: Secrets Management with Environment Variables
The system SHALL store all secrets in environment variables or `.env` files, never committing secrets to version control.

#### Scenario: SECRET_KEY generation and storage
- **WHEN** the CLI scaffolder creates a new project
- **THEN** it MUST generate a cryptographically random `SECRET_KEY`
- **THEN** it MUST write the key to `.env` file
- **THEN** `.env` MUST be listed in `.gitignore`
- **THEN** the repository MUST contain `.env.example` with placeholder value `django-insecure-change-me-in-production`

#### Scenario: Production secrets from environment
- **WHEN** the Django app runs in production
- **THEN** it MUST read `SECRET_KEY`, `DATABASE_URL`, and API keys from environment variables
- **THEN** secrets MUST NOT be hardcoded in any committed file

### Requirement: Input Validation with Double Validation Strategy
All user input SHALL be validated both client-side (Zod) and server-side (Pydantic) with identical constraints.

#### Scenario: Client-side Zod validation before API call
- **WHEN** a user submits a signup form on web or mobile
- **THEN** the Zod schema MUST validate the input before sending any API request
- **THEN** if validation fails, field errors MUST display inline
- **THEN** NO network request MUST be made

#### Scenario: Server-side Pydantic validation
- **WHEN** the Django API receives a request with user input
- **THEN** it MUST validate the input against a Pydantic schema
- **THEN** if validation fails, it MUST return HTTP 400 with field-level errors in standardized format
- **THEN** validation MUST enforce the same constraints as the client-side Zod schema

### Requirement: Dependency Vulnerability Scanning
The CI pipeline SHALL run automated dependency vulnerability scans for Python and JavaScript packages.

#### Scenario: Python dependency audit in CI
- **WHEN** the API CI job runs
- **THEN** it MUST execute `uv run pip-audit`
- **THEN** if known vulnerabilities are found, the build MUST fail

#### Scenario: JavaScript dependency audit in CI
- **WHEN** the web or mobile CI job runs
- **THEN** it MUST execute `pnpm audit --audit-level=high`
- **THEN** if high or critical vulnerabilities are found, the build MUST fail

### Requirement: Secure Database Access with Parameterized Queries
All database queries SHALL use parameterized queries via Django ORM or parameterized raw SQL to prevent SQL injection.

#### Scenario: ORM query safety
- **WHEN** a service layer queries the database
- **THEN** it MUST use Django ORM methods like `filter()`, `get()`, `create()`
- **THEN** user input MUST be passed as parameters, not interpolated into query strings

#### Scenario: Raw SQL with parameters
- **WHEN** raw SQL is necessary (e.g., PGVector similarity search)
- **THEN** the query MUST use parameterized placeholders: `cursor.execute("SELECT * FROM items WHERE id = %s", [user_input])`
- **THEN** string interpolation (f-strings, `%` formatting) MUST NOT be used
