## ADDED Requirements

### Requirement: Standardized Error Response Format
All API error responses SHALL use a consistent JSON envelope with error code, message, and optional details fields.

#### Scenario: API validation error response
- **WHEN** the Django API receives invalid request data that fails Pydantic validation
- **THEN** it MUST return HTTP 400 with error envelope:
  ```json
  {
    "error": {
      "code": "VALIDATION_001",
      "message": "Validation failed.",
      "details": {
        "field_errors": {
          "email": ["Enter a valid email address."]
        }
      }
    }
  }
  ```

#### Scenario: Authentication error response
- **WHEN** an unauthenticated client requests a protected endpoint
- **THEN** the API MUST return HTTP 401 with error code `AUTH_001`
- **THEN** the message MUST be "Authentication credentials were not provided."
- **THEN** the details object MAY be empty

### Requirement: Error Code Taxonomy
The system SHALL use a standardized error code taxonomy organized by category for consistent error identification.

#### Scenario: Error code assignment by category
- **WHEN** an authentication error occurs
- **THEN** the error code MUST start with `AUTH_` prefix (e.g., `AUTH_001`, `AUTH_002`)
- **WHEN** a validation error occurs
- **THEN** the error code MUST start with `VALIDATION_` prefix
- **WHEN** an unhandled server error occurs
- **THEN** the error code MUST be `SERVER_001`

### Requirement: Django Exception Handlers
The Django API SHALL register custom exception handlers that convert all exceptions to the standardized error format.

#### Scenario: Pydantic validation exception handling
- **WHEN** Pydantic validation raises `ValidationError` on request input
- **THEN** the exception handler MUST intercept it
- **THEN** it MUST convert Pydantic errors to field-level errors in `details.field_errors`
- **THEN** it MUST return HTTP 400 with code `VALIDATION_001`

#### Scenario: Unhandled exception catching
- **WHEN** an unhandled exception occurs in a Django view
- **THEN** the exception handler MUST log the full traceback at ERROR level
- **THEN** it MUST return HTTP 500 with code `SERVER_001` and generic message
- **THEN** it MUST NOT include stack traces or internal details in the response body in production

### Requirement: Frontend Error Boundary Components
Next.js SHALL implement error boundary components at route group and root levels to catch rendering errors.

#### Scenario: Dashboard error boundary catches rendering error
- **WHEN** a component in the dashboard route group throws an error during render
- **THEN** the `app/(dashboard)/error.tsx` boundary MUST catch it
- **THEN** it MUST display "Something went wrong" message with a "Try again" button
- **THEN** clicking "Try again" MUST call the `reset()` function to re-render

### Requirement: Form Validation Error Display
Form validation errors SHALL display inline on form fields, while non-field errors display as toast notifications.

#### Scenario: Client-side validation before submission
- **WHEN** a user submits a signup form with an empty email field
- **THEN** the Zod schema MUST validate client-side before API request
- **THEN** the email field MUST display "Email is required." error inline
- **THEN** NO API request MUST be made
- **THEN** NO toast notification MUST be shown

#### Scenario: Server-side validation error merging
- **WHEN** client-side validation passes but the API returns field errors (e.g., "Email already exists")
- **THEN** the field error MUST be merged into the form field errors
- **THEN** the email field MUST display the server-provided error message
- **THEN** the form MUST retain all other field values

### Requirement: Mobile Error Handling with Offline Detection
The Expo app SHALL handle network errors gracefully with offline state detection and user notifications.

#### Scenario: Device goes offline
- **WHEN** the mobile device loses network connectivity
- **THEN** the `NetInfo` listener MUST detect `isConnected=false`
- **THEN** a persistent banner MUST display "You are offline. Some features may be unavailable."
- **THEN** React Query MUST pause all pending queries with `networkMode: "online"`
- **THEN** cached data MUST remain visible

#### Scenario: Network restored after offline
- **WHEN** network connectivity is restored
- **THEN** the offline banner MUST disappear
- **THEN** React Query MUST resume paused queries automatically
- **THEN** fresh data MUST replace cached data
