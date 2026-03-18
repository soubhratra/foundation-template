## Requirements

### Requirement: Expo Router File-Based Navigation

The mobile application SHALL use Expo Router with file-based navigation organized into auth stack and authenticated tab navigator.

#### Scenario: Navigation structure

- **WHEN** the mobile app is scaffolded
- **THEN** it MUST include `app/(auth)/` route group with `login.tsx` and `signup.tsx` screens
- **THEN** it MUST include `app/(tabs)/` route group with `index.tsx`, `settings.tsx`, and `profile.tsx` tabs
- **THEN** the root `app/_layout.tsx` MUST conditionally route to `(auth)` or `(tabs)` based on authentication state

#### Scenario: Tab navigation for authenticated users

- **WHEN** an authenticated user opens the app
- **THEN** they MUST see a bottom tab bar with Home, Settings, and Profile tabs
- **THEN** each tab MUST have an icon from `lucide-react-native`
- **THEN** navigation between tabs MUST preserve navigation state per tab

### Requirement: JWT Token Storage with Expo Secure Store

The mobile application SHALL store JWT access and refresh tokens securely using `expo-secure-store` which leverages OS-level secure storage.

#### Scenario: Token storage after login

- **WHEN** a user successfully logs in on mobile
- **THEN** the application MUST store the access token in `expo-secure-store` under key `auth_access_token`
- **THEN** it MUST store the refresh token in `expo-secure-store` under key `auth_refresh_token`
- **THEN** tokens MUST NOT be stored in `AsyncStorage` or any plaintext storage

#### Scenario: Token retrieval on app launch

- **WHEN** the app launches and the root layout initializes
- **THEN** it MUST attempt to retrieve the access token from `expo-secure-store`
- **THEN** if a valid token exists, `isAuthenticated` state MUST become true
- **THEN** if no token exists, `isAuthenticated` state MUST become false

### Requirement: Transparent Token Refresh with API Interceptor

The mobile application SHALL implement transparent access token refresh when the API returns 401 unauthorized.

#### Scenario: Access token expired during request

- **WHEN** an API request returns 401 with an expired access token
- **THEN** the API client interceptor MUST send POST to `/api/v1/auth/token/refresh` with the refresh token
- **THEN** upon success, it MUST store the new access token in `expo-secure-store`
- **THEN** it MUST retry the original request with the new access token
- **THEN** the user MUST NOT see any error or interruption

#### Scenario: Refresh token also expired

- **WHEN** the token refresh request also returns 401
- **THEN** both access and refresh tokens MUST be deleted from `expo-secure-store`
- **THEN** the user MUST be redirected to `/(auth)/login`
- **THEN** a message MUST display "Your session has expired. Please log in again."

### Requirement: Metro Bundler Monorepo Configuration

The mobile application SHALL configure Metro bundler for monorepo package resolution with pnpm workspaces.

#### Scenario: Metro resolves shared packages

- **WHEN** the Expo app imports from `@repo/ui`, `@repo/api-client`, or `@repo/validation`
- **THEN** Metro MUST resolve packages from monorepo root using `nodeModulesPaths` configuration
- **THEN** it MUST watch the monorepo root for hot reload via `watchFolders` configuration
- **THEN** it MUST prevent duplicate React instances via `disableHierarchicalLookup` setting

### Requirement: Shared Package Consumption

The mobile application SHALL consume shared TypeScript packages for UI primitives, API client types, validation schemas, and business logic.

#### Scenario: Using shared UI components

- **WHEN** a mobile screen needs a Button component
- **THEN** it MUST import from `@repo/ui` which provides React Native primitives
- **THEN** Metro MUST resolve the `.native.tsx` variant if present, otherwise `.tsx` default

#### Scenario: Form validation with shared Zod schemas

- **WHEN** a login form validates user input
- **THEN** it MUST use the `loginSchema` from `@repo/validation`
- **THEN** validation errors MUST display inline on form fields
- **THEN** client-side validation MUST run before API submission
