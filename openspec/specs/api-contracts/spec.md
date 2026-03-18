# API Contracts and Type Generation

## Requirements

### Requirement: OpenAPI 3.1 Schema Export

The Django Ninja Extra API MUST generate an OpenAPI 3.1 JSON specification from Pydantic schemas and controller definitions. The schema MUST be exportable via a management command and accessible at runtime via `/api/v1/openapi.json`.

#### Scenario: Management Command Export

- **WHEN** `python manage.py export_openapi_schema` is executed from apps/api/
- **THEN** the command outputs the complete OpenAPI 3.1 schema to stdout
- **AND** the schema includes all registered controller endpoints with request/response schemas
- **AND** the output can be redirected to a file for frontend consumption

#### Scenario: Runtime Schema Endpoint

- **WHEN** a GET request is sent to `/api/v1/openapi.json`
- **THEN** the API returns the OpenAPI 3.1 schema as JSON with status 200
- **AND** the schema is identical to the management command output
- **AND** no authentication is required to access the schema

### Requirement: TypeScript Type Generation Pipeline

The api-client package SHALL use openapi-typescript to generate TypeScript type definitions from the exported OpenAPI schema. The generated types MUST be committed to version control for frontend development without a running backend.

#### Scenario: Type Generation from Schema

- **WHEN** `pnpm generate:types` is run in packages/api-client/
- **THEN** openapi-typescript reads openapi.json
- **AND** generates src/types.d.ts with full TypeScript type definitions
- **AND** the generated file includes types for all paths, operations, request bodies, and response schemas

#### Scenario: CI Type Drift Detection

- **WHEN** the CI pipeline runs after an API schema change
- **THEN** CI regenerates types.d.ts from the OpenAPI schema
- **AND** compares the output to the committed types.d.ts file
- **AND** fails the build if the files differ, forcing the developer to regenerate and commit

### Requirement: Type-Safe HTTP Client with openapi-fetch

The api-client package MUST export a type-safe HTTP client using openapi-fetch configured with the generated types. All HTTP methods SHALL be fully typed based on the OpenAPI schema.

#### Scenario: Typed GET Request

- **WHEN** a frontend calls `apiClient.GET("/users/me")`
- **THEN** TypeScript infers the response type from the OpenAPI schema
- **AND** the data property is typed as UserOut (or the appropriate response schema)
- **AND** the error property is typed as ErrorOut
- **AND** autocomplete suggests all available API paths

#### Scenario: Typed POST Request

- **WHEN** a frontend calls `apiClient.POST("/users", { body: userData })`
- **THEN** TypeScript validates the body matches the UserCreateIn schema
- **AND** compilation fails if required fields are missing or types are wrong
- **AND** the response type is automatically inferred from the OpenAPI schema

### Requirement: CORS Configuration

The Django API MUST configure django-cors-headers to allow requests from frontend origins. CORS_ALLOWED_ORIGINS MUST be explicit (never wildcard) and CORS_ALLOW_CREDENTIALS MUST be True for session cookie auth.

#### Scenario: Development CORS for Next.js

- **WHEN** Next.js dev server (http://localhost:3000) makes a request to Django API (http://localhost:8000)
- **THEN** Django responds with `Access-Control-Allow-Origin: http://localhost:3000`
- **AND** `Access-Control-Allow-Credentials: true` is included in the response
- **AND** the browser allows the request to proceed

#### Scenario: Production CORS Restriction

- **WHEN** CORS_ALLOWED_ORIGINS is set to `["https://app.example.com"]` in production
- **THEN** only requests from https://app.example.com receive CORS headers
- **AND** requests from other origins are blocked by the browser
- **AND** CORS_ALLOW_ALL_ORIGINS is False

### Requirement: Standardized Error Response Format

All API errors MUST conform to a standard ErrorOut Pydantic schema with detail (string), code (optional string), and errors (optional list of field errors). HTTP status codes MUST map consistently to error types.

#### Scenario: Validation Error Response

- **WHEN** a POST request fails Pydantic validation (missing required field)
- **THEN** the API returns 422 with an ErrorOut body
- **AND** the detail field describes the validation failure
- **AND** the errors field lists each invalid field with a specific message

#### Scenario: Not Found Error Response

- **WHEN** a GET request targets a non-existent resource (404)
- **THEN** the API returns 404 with an ErrorOut body
- **AND** the detail field is "Resource not found" (or equivalent message)
- **AND** the code field is "not_found"

### Requirement: Pagination Convention

List endpoints MUST use offset/limit pagination with a standardized response format containing items (array), total (count), offset, limit, has_next, and has_previous fields.

#### Scenario: Paginated List Request

- **WHEN** a GET request is sent to a list endpoint with `?offset=20&limit=10`
- **THEN** the API returns 10 items starting from the 21st record
- **AND** the response includes total (total record count), offset (20), limit (10)
- **AND** has_next is true if more records exist, has_previous is true if offset > 0

#### Scenario: Maximum Limit Enforcement

- **WHEN** a GET request specifies `?limit=500`
- **THEN** the API caps the limit at 100 (maximum allowed)
- **AND** returns at most 100 items
- **AND** does not raise an error for the oversized limit

### Requirement: API Versioning via URL Prefix

All API endpoints MUST be versioned with a URL prefix `/api/v1/`. Breaking changes to the API SHALL require a new version (v2), while non-breaking changes (new fields, new endpoints) SHALL NOT increment the version.

#### Scenario: Versioned Endpoint Access

- **WHEN** a client makes a request to `/api/v1/users/me`
- **THEN** the request is routed to the v1 API controller
- **AND** the response conforms to the v1 schema
- **AND** the OpenAPI schema is available at `/api/v1/openapi.json`

#### Scenario: Backward-Compatible Change

- **WHEN** a new optional field is added to UserOut schema
- **THEN** the API version remains v1
- **AND** existing clients continue to work without changes
- **AND** new clients can access the additional field
