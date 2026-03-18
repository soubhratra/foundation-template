## Requirements

### Requirement: API Key Creation with Scopes

Authenticated users SHALL be able to create scoped API keys for programmatic access, with the raw key shown exactly once at creation.

#### Scenario: User creates an API key

- **WHEN** an authenticated user calls `POST /api/v1/me/api-keys/` with a name and list of scopes
- **THEN** an `APIKey` record SHALL be created
- **AND** the full raw key SHALL be returned in the response body exactly once (format: `<prefix><64 hex chars>`, e.g. `ft_a1b2c3d4...`)
- **AND** only the key prefix and SHA-256 hash SHALL be stored in the database — the raw key SHALL NOT be persisted

#### Scenario: Key prefix stored for identification

- **WHEN** a user lists their API keys via `GET /api/v1/me/api-keys/`
- **THEN** each key SHALL be identified by its prefix (e.g. `ft_a1b2c3d4`) and name
- **AND** the full raw key SHALL NOT appear in any list or detail response

#### Scenario: Scopes validated against API_KEY_SCOPES at creation

- **WHEN** a user requests a key with scope `"unknown_scope"`
- **AND** `"unknown_scope"` is not defined in `API_KEY_SCOPES` settings
- **THEN** the system SHALL return `400 Bad Request`

### Requirement: API Key Authentication via Bearer Token

The system SHALL authenticate requests carrying an `Authorization: Bearer <key>` header by resolving the key to its owner and setting `request.user`.

#### Scenario: Valid API key authenticates request

- **WHEN** a request includes `Authorization: Bearer ft_<key>`
- **THEN** the Ninja auth backend SHALL hash the provided key, look up the matching `APIKey` by hash, and set `request.user` to the key's owner
- **AND** all existing `IsAuthenticated` checks SHALL pass transparently

#### Scenario: Invalid or revoked key rejected

- **WHEN** a request includes an `Authorization: Bearer` header with an invalid, expired, or revoked key
- **THEN** the system SHALL return `401 Unauthorized`

#### Scenario: Session-authenticated requests rejected by RequireScope

- **WHEN** a request is authenticated via session cookie (not API key) and the endpoint uses `RequireScope`
- **THEN** the system SHALL return `403 Forbidden`
- **AND** `RequireScope` SHALL NOT fall back to session auth — API key Bearer token is required

### Requirement: RequireScope Permission Class

The system SHALL provide a `RequireScope` Ninja Extra permission class that enforces scope-based access on API endpoints.

#### Scenario: Key with required scope passes

- **WHEN** a request authenticated by an API key with scope `"read"` reaches an endpoint decorated with `RequireScope("read")`
- **THEN** the request SHALL be processed normally

#### Scenario: Key without required scope blocked

- **WHEN** a request authenticated by an API key that does NOT have scope `"write"` reaches an endpoint decorated with `RequireScope("write")`
- **THEN** the system SHALL return `403 Forbidden`

### Requirement: Per-Key Rate Limiting with Response Headers

API key requests SHALL be rate-limited per key, with rate limit state exposed via response headers.

#### Scenario: Rate limit headers returned on every API key request

- **WHEN** a valid API key authenticates a request
- **THEN** the response SHALL include:
  - `X-RateLimit-Limit`: the configured limit (e.g. `1000`)
  - `X-RateLimit-Remaining`: requests remaining in the current window
  - `X-RateLimit-Reset`: Unix timestamp when the window resets

#### Scenario: Rate limit exceeded

- **WHEN** an API key exceeds the configured rate limit
- **THEN** the system SHALL return `429 Too Many Requests`
- **AND** `X-RateLimit-Remaining` SHALL be `0`

### Requirement: Key Revocation

Users SHALL be able to revoke API keys, immediately invalidating them.

#### Scenario: User revokes an API key

- **WHEN** a user calls `DELETE /api/v1/me/api-keys/{id}/`
- **THEN** the key SHALL be deleted or marked revoked
- **AND** subsequent requests using that key SHALL return `401 Unauthorized`

### Requirement: Usage Tracking

The system SHALL track `last_used_at` and `usage_count` on every API key, updated on each authenticated request.

#### Scenario: Usage stats updated on authenticated request

- **WHEN** a valid API key authenticates a request
- **THEN** `APIKey.last_used_at` SHALL be updated to the current timestamp
- **AND** `APIKey.usage_count` SHALL be incremented by 1

### Requirement: Settings-Based Scope Catalog

Available API key scopes SHALL be defined in an `API_KEY_SCOPES` settings dict.

#### Scenario: Scope catalog validated at startup

- **WHEN** the Django application starts
- **THEN** `manage.py check` SHALL validate the `API_KEY_SCOPES` dict is non-empty and well-formed

## Implementation Decisions

### Why API keys are user-owned (not org-owned)

All keys in v1.4 are owned by the user who created them, managed at `/api/v1/me/api-keys/`. Org context is derived from the user's membership if products need it. Org-level API keys with per-org rate limits are a v2 consideration; adding that complexity to the template now would over-engineer for the common case.

### Why prefix + SHA-256 hash (not bcrypt or full-key storage)

- **Not full-key:** A database breach would expose all keys, enabling immediate unauthorized access.
- **Not bcrypt:** bcrypt is slow by design (for password hashing). API key auth happens on every request — bcrypt would add 100–300ms per request. SHA-256 is fast and sufficient because API keys are 256-bit random values (not low-entropy passwords that need stretching).
- **Prefix stored:** The 8-character stored prefix (e.g. `ft_a1b2c3d4`) lets users identify keys in list views without exposing the full key — consistent with GitHub and Stripe's key display pattern.

### Why `RequireScope` rejects session-authenticated requests entirely

An endpoint protected with `RequireScope` is explicitly an API/programmatic endpoint. Allowing session cookies to bypass scope checks would make the scope system meaningless — a browser session would have implicit full access. The strict rejection forces product developers to be explicit about which endpoints accept both auth methods.

### Why the key format uses `API_KEY_PREFIX` (default `ft_`)

Products can override `API_KEY_PREFIX` to match their brand (e.g. `"gh_"`, `"sk_live_"`). The prefix is in settings (not hardcoded) so no template code needs changing per product. The `ft_` default is a placeholder the scaffolder README instructs developers to update.

### Why rate limit state derives from django-ratelimit's Redis counter

A separate counter for `X-RateLimit-*` headers would drift from the actual rate limiter's state. Reading from the same Redis key that `django-ratelimit` uses ensures headers always reflect true remaining capacity. One source of truth, no synchronization complexity.

### Why `last_used_at` / `usage_count` update synchronously in the auth backend

Updating usage stats in a `transaction.on_commit()` callback or async task risks losing updates if the worker crashes. Since the auth backend already has a database connection open for key lookup, updating stats in the same transaction is low overhead and guarantees consistency. Products with extremely high throughput can override this to use Redis counters flushed periodically.

### Why the key is shown once (not emailed or retrievable later)

Emailing the raw key creates a second exposure vector (email interception). Storing the key for later retrieval requires keeping plaintext or a reversible cipher, which defeats hashing. The "shown once at creation" model is the industry standard (GitHub PATs, Stripe secret keys, Heroku API tokens). Product UIs must show a copy-to-clipboard affordance with a clear warning.
