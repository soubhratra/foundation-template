# Phase 04: Web Application - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the production-ready Next.js 15 App Router experience for the web client: complete auth flows (login, signup, password reset, email verification), strict route guarding, and an authenticated dashboard shell with navigation, profile/settings, and dark-mode support. No extra product features beyond this template surface.

</domain>

<decisions>
## Implementation Decisions

### Auth flow experience

- Root `/` renders the login form immediately with a small marketing blurb/hero; no separate marketing landing.
- Signup and password reset each live on their own dedicated routes (`/signup`, `/reset`) with full-page forms.
- Users must verify email before logging in; unverified accounts cannot enter the UI.
- After auth success we respect any `?next` param captured by middleware and default to `/dashboard`.

### Dashboard shell & navigation

- Desktop layout uses a persistent left sidebar with logo and links to Dashboard, Profile, Settings (include an Activity/Log placeholder to show navigation depth) plus a top header.
- Header includes user avatar menu (profile/logout) and the dark-mode toggle; planner can surface toast/notifications there later.
- On mobile/tablet the sidebar collapses behind a hamburger-triggered sheet; header stays visible for toggle + avatar.

### Route guards & session states

- Protected routes redirect unauthenticated visitors to `/login?next=...` immediately.
- While the session is being validated (SSR or client hydration) show a skeleton version of the destination page rather than a blank screen.
- If a session expires mid-flow, force redirect back to `/login` and show a flash/toast explaining the session ended.
- Default auth middleware + hooks should honor `redirect` query params so successful logins land on the originally requested page, falling back to `/dashboard`.

### Design system template

- Ship a comprehensive but minimal/unopinionated design system baseline (buttons, inputs, cards, tables, alerts, toggle, etc.) aligned with the shared UI primitives so downstream repos can reskin easily.
- Provide both light and dark modes with a reliable toggle but keep the palette neutral (grays + accent) so product teams can extend it.

### Claude's Discretion

- Exact marketing blurb copy, imagery, and layout around the login card.
- Visual style of skeleton/loading states and the animation when sidebars collapse.
- Microcopy on session-expired toast and inline error wording.

</decisions>

<specifics>
## Specific Ideas

- Login page should feel like a template hero: concise marketing sentence above/beside the sign-in card.
- Sidebar needs the three core links (Dashboard, Profile, Settings) plus an Activity/log stub to demonstrate navigation depth.
- AuthProvider-integrated skeleton should mirror final layouts so transitions are smooth.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

_Phase: 04-web-application_
_Context gathered: 2026-02-16_
