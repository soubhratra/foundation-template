## ADDED Requirements

### Requirement: API Client Package with Type Generation
The monorepo SHALL provide a `@repo/api-client` package that generates TypeScript types from the Django OpenAPI spec and wraps them in a type-safe HTTP client.

#### Scenario: OpenAPI types generated from Django spec
- **WHEN** a developer runs the type generation command
- **THEN** Django MUST export the OpenAPI 3.0 spec to `packages/api-client/openapi.json`
- **AND** the `openapi-typescript` tool MUST generate TypeScript types in `src/types.d.ts`
- **AND** both files MUST be committed to git for frontend-only development
- **AND** CI MUST verify that committed types match the current Django output

#### Scenario: Type-safe API client created with auth provider
- **WHEN** an application creates an API client instance
- **THEN** the client MUST use `openapi-fetch` with the generated path types
- **AND** the client MUST accept an optional auth provider for request/response interception
- **AND** web applications MUST use `WebAuthProvider` (relies on automatic cookie sending)
- **AND** mobile applications MUST use `MobileAuthProvider` (attaches JWT Bearer tokens)

#### Scenario: Mobile auth provider handles token refresh
- **WHEN** a mobile API request returns 401 Unauthorized
- **THEN** the auth provider MUST intercept the 401 response
- **AND** the provider MUST attempt to refresh the access token using the refresh token
- **AND** if refresh succeeds, the provider MUST store new tokens and retry the original request
- **AND** if refresh fails, the provider MUST clear tokens and trigger auth failure callback

### Requirement: Validation Package with Zod Schemas
The monorepo SHALL provide a `@repo/validation` package containing Zod schemas for client-side form validation shared across web and mobile.

#### Scenario: Auth validation schemas defined once
- **WHEN** authentication forms are implemented on web and mobile
- **THEN** the `loginSchema` MUST be defined once in `@repo/validation`
- **AND** the `signupSchema` MUST include email, password, password_confirm, first_name, and last_name fields
- **AND** password fields MUST be validated with strength requirements (min 8 chars, uppercase, lowercase, number)
- **AND** TypeScript types MUST be derived via `z.infer<typeof schema>` for type safety

#### Scenario: Validation schemas used with react-hook-form on both platforms
- **WHEN** a form is implemented using react-hook-form
- **THEN** both Next.js and Expo MUST use `@hookform/resolvers/zod` with the same schema
- **AND** validation errors MUST be identical on both platforms
- **AND** TypeScript input types MUST be identical via `z.infer<>`
- **AND** no validation logic MUST be duplicated between platforms

### Requirement: UI Package with React Native Web Primitives
The monorepo SHALL provide a `@repo/ui` package containing cross-platform UI primitives built with React Native core components.

#### Scenario: Button component renders on both platforms
- **WHEN** the `Button` component is imported and rendered on web
- **THEN** webpack MUST resolve `react-native` to `react-native-web`
- **AND** the component MUST render as a DOM element (e.g., `<div role="button">`)
- **AND** the component MUST be interactive and styled correctly in the browser

#### Scenario: Button component renders natively on mobile
- **WHEN** the `Button` component is imported and rendered on mobile
- **THEN** Metro MUST resolve the `.native.tsx` variant if present, otherwise `.tsx`
- **AND** the component MUST render as a native touchable element
- **AND** the component MUST be interactive and styled correctly on the device

#### Scenario: UI package has zero monorepo dependencies
- **WHEN** the `@repo/ui` package is defined
- **THEN** it MUST NOT depend on any other monorepo packages
- **AND** it MUST only have `react` and `react-native` as peer dependencies
- **AND** it MUST NOT import Zod, API client, or business logic packages
- **AND** it MUST use only React Native core APIs (View, Text, Pressable, TextInput, etc.)

#### Scenario: Platform-specific variants using file extensions
- **WHEN** a component needs different implementations per platform
- **THEN** the package MUST use file extensions: `.tsx` (default), `.web.tsx` (web), `.native.tsx` (mobile)
- **AND** Metro MUST resolve `.native.tsx` before `.tsx` on mobile
- **AND** webpack MUST resolve `.web.tsx` before `.tsx` on web
- **AND** no bundler configuration changes MUST be required

### Requirement: Business Logic Package with Shared Hooks
The monorepo SHALL provide a `@repo/business-logic` package containing platform-agnostic React hooks and utility functions.

#### Scenario: useAuth hook provides authentication methods
- **WHEN** a component uses the `useAuth` hook
- **THEN** the hook MUST provide `login`, `logout`, and `register` mutation functions
- **AND** the hook MUST expose `isAuthenticated`, `isLoading`, and `user` state
- **AND** the hook MUST invalidate the `currentUser` query on login
- **AND** the hook MUST clear the React Query cache on logout

#### Scenario: useUser hook fetches and updates user profile
- **WHEN** a component uses the `useUser` hook
- **THEN** the hook MUST fetch the current user via `/api/v1/users/me`
- **AND** the hook MUST provide an `updateProfile` mutation function
- **AND** profile updates MUST invalidate the `currentUser` query
- **AND** the hook MUST expose loading and error states

#### Scenario: Business logic package depends on api-client and validation
- **WHEN** the `@repo/business-logic` package is defined
- **THEN** it MUST depend on `@repo/api-client` and `@repo/validation`
- **AND** it MUST NOT depend on `@repo/ui`
- **AND** hooks MUST accept the API client as a parameter (dependency injection)
- **AND** hooks MUST use validation schemas for input type safety

### Requirement: Config Packages for ESLint and TypeScript
The monorepo SHALL provide `@repo/config-eslint` and `@repo/config-ts` packages for shared linting and compiler configuration.

#### Scenario: ESLint flat config presets consumed by apps
- **WHEN** an application configures ESLint
- **THEN** Next.js apps MUST extend `@repo/config-eslint/next` preset
- **AND** Expo apps MUST extend `@repo/config-eslint/react-native` preset
- **AND** all packages MUST extend the base config with TypeScript and React rules
- **AND** apps MAY override rules for app-specific requirements

#### Scenario: TypeScript configs extend base with platform-specific settings
- **WHEN** an application configures TypeScript
- **THEN** Next.js apps MUST extend `@repo/config-ts/nextjs.json`
- **AND** Expo apps MUST extend `@repo/config-ts/react-native.json`
- **AND** shared packages MUST extend `@repo/config-ts/library.json`
- **AND** all configs MUST inherit strict mode and compiler safety settings from `base.json`

### Requirement: Package Dependency Graph Rules
All packages SHALL follow a flat dependency graph with maximum one-hop chains between shared packages.

#### Scenario: Package dependency chain depth enforced
- **WHEN** a package is created or modified
- **THEN** the maximum dependency chain MUST be two hops from app to leaf package
- **AND** `config-ts` and `config-eslint` MUST have zero monorepo dependencies
- **AND** `validation`, `ui`, and `api-client` MUST have zero monorepo dependencies
- **AND** `business-logic` MAY depend on `api-client` and `validation` only
- **AND** no circular dependencies MUST exist between packages

#### Scenario: Apps consume packages directly without deep chains
- **WHEN** an app imports from a shared package
- **THEN** the import path MUST be direct (e.g., `from "@repo/ui"`)
- **AND** apps MAY depend on any shared package without restriction
- **AND** shared packages MUST NOT import from app directories
- **AND** the dependency direction MUST always be `app -> package`, never `package -> app`

### Requirement: Package Naming and Export Conventions
All shared packages SHALL use the `@repo/` scope and follow consistent export patterns.

#### Scenario: Packages use @repo scope with source entry points
- **WHEN** a package is defined in the monorepo
- **THEN** the package name MUST use the `@repo/` scope
- **AND** the package MUST be marked `"private": true` (not published to npm)
- **AND** the main entry point MUST be `src/index.ts` (source, not built `dist/`)
- **AND** Metro and webpack MUST handle TypeScript compilation directly

#### Scenario: Packages consumed via pnpm workspace protocol
- **WHEN** an app or package depends on another monorepo package
- **THEN** the dependency MUST use `workspace:*` protocol in `package.json`
- **AND** pnpm MUST resolve the dependency to the local workspace package
- **AND** changes to the package MUST be immediately available without rebuild
- **AND** TypeScript MUST resolve types from source files
