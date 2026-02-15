## ADDED Requirements

### Requirement: Next.js 15 App Router Structure
The web application SHALL use Next.js 15 App Router with file-based routing organized into route groups for authentication flows and authenticated dashboard areas.

#### Scenario: App Router directory organization
- **WHEN** the web application is scaffolded
- **THEN** it MUST include `(auth)` route group for login, signup, reset-password, and verify-email pages
- **THEN** it MUST include `(dashboard)` route group for dashboard, settings, and profile pages
- **THEN** each route group MUST have its own `layout.tsx` defining layout behavior
- **THEN** the root `app/layout.tsx` MUST provide theme provider, query client provider, and global metadata

#### Scenario: Layout system implementation
- **WHEN** a user accesses an auth route
- **THEN** the auth layout MUST render a centered card with no sidebar or header chrome
- **WHEN** a user accesses a dashboard route
- **THEN** the dashboard layout MUST render a sidebar navigation and top header with user avatar

### Requirement: Authentication Middleware and Routing
The application SHALL implement middleware-based authentication guards that redirect users based on session state.

#### Scenario: Unauthenticated access to dashboard
- **WHEN** a user with no session cookie navigates to `/dashboard`
- **THEN** the middleware MUST redirect to `/login` with HTTP 302
- **THEN** the user MUST NOT see any dashboard content

#### Scenario: Authenticated access to auth pages
- **WHEN** a user with a valid session cookie navigates to `/login`
- **THEN** the middleware MUST redirect to `/dashboard` with HTTP 302
- **THEN** the login page MUST NOT render

### Requirement: Server Component Data Fetching with Cookie Forwarding
The web application SHALL fetch data in Server Components using cookie-forwarding API client to maintain authentication context.

#### Scenario: Server Component fetches user data
- **WHEN** a Server Component in the dashboard layout needs to render user information
- **THEN** it MUST call `createServerApiClient()` which forwards the session cookie to Django
- **THEN** the Django API MUST validate the session and return user data
- **THEN** the component MUST render HTML with user data without client-side fetch

#### Scenario: Expired session in Server Component
- **WHEN** the Django API returns 401 for an expired session during Server Component rendering
- **THEN** the Server Component MUST call `redirect("/login")` from `next/navigation`
- **THEN** the user MUST be redirected to the login page

### Requirement: API Route BFF Proxy for Same-Origin Auth
The application SHALL proxy authentication API requests through Next.js API routes to maintain same-origin cookie behavior.

#### Scenario: Auth request proxying
- **WHEN** the frontend submits a POST to `/api/auth/login`
- **THEN** the Next.js API route MUST proxy the request to Django Allauth endpoint
- **THEN** it MUST forward request cookies and body to Django
- **THEN** it MUST forward `Set-Cookie` headers from Django response back to the browser
- **THEN** the browser MUST receive session cookies as same-origin

### Requirement: Dark Mode with System Preference
The application SHALL implement dark mode using `next-themes` with system preference detection and no flash of incorrect theme.

#### Scenario: Initial page load with system preference
- **WHEN** a user loads the application for the first time with system preference set to "dark"
- **THEN** the dark theme MUST activate without flash of light theme
- **THEN** the root `<html>` element MUST have `suppressHydrationWarning` attribute
- **THEN** Tailwind `dark:` variant classes MUST apply

#### Scenario: Manual theme toggle
- **WHEN** a user clicks the theme toggle button
- **THEN** the theme MUST switch between "light" and "dark"
- **THEN** the preference MUST persist to `localStorage`
- **THEN** subsequent page loads MUST use the stored preference

### Requirement: Shadcn/ui Design System Integration
The application SHALL use Shadcn/ui components for the web design system with Tailwind CSS styling.

#### Scenario: Form with Shadcn/ui components
- **WHEN** a developer creates a signup form
- **THEN** they MUST use Shadcn/ui primitives like `Button`, `Input`, `Card`, and `Label`
- **THEN** components MUST be installed into `components/ui/` via Shadcn CLI
- **THEN** components MUST support Tailwind class customization via the `cn()` utility
