# Phase 03: Shared Packages + Type Generation - Research

**Researched:** 2026-02-15
**Domain:** Shared TS packages & OpenAPI type pipeline
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions
- CONTEXT.md not provided; follow global commitments: Django Ninja Extra backend at `apps/api/`, Next.js 15 web + Expo mobile clients, HS256 headless JWT strategy, pnpm + Turborepo monorepo, and PKG-01..PKG-08 require shared packages consumed by both web and mobile (STATE.md, REQUIREMENTS.md).

### Claude's Discretion
- No extra guidance supplied; research best-practice implementations for PKG-01 through PKG-08 on top of the locked stack.

### Deferred Ideas (OUT OF SCOPE)
- None recorded.

## Summary

Phase 03 succeeds only if the Django Ninja API remains the single source of truth: keep `/api/docs` + `/api/openapi.json` reachable (already required in Phase 02) and script a repeatable export that feeds `openapi-typescript`, which emits namespaced `paths` and `components` typings ready for package builds.[^django-docs][^oats-intro] This removes drift between backend and frontend contracts, unlocks DX-03 “types are fresh” later, and lets CI diff generated artifacts.

The api-client package should layer `openapi-fetch` for 6 kB spec-safe HTTP calls, then wrap it with `openapi-react-query`+`@tanstack/react-query` so business hooks (PKG-05/06) gain caching, retries, and mutation flows without rewriting fetch logic.[^oafetch][^oarq][^tanstack] Validation and UI packages pivot on React Native primitives: share Zod schemas + React Hook Form resolvers so both Next.js and Expo screens can re-use form logic, and ship React Native Web-based components (Button/Text/Input/Card) with aliasing + module-alias so the exact same JSX works on web/mobile.[^zod][^rhf][^rnw]

**Primary recommendation:** Treat the OpenAPI artifact as code—add a `pnpm generate:types` turbo task that (1) runs `python manage.py dump_openapi` or curls `/api/openapi.json`, (2) pipes it through `openapi-typescript`, and (3) re-builds `packages/api-client`, failing CI if outputs change.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openapi-typescript | 7.13.0 | Generate `paths`/`components` typings from OpenAPI 3.0/3.1 | CLI handles local/remote specs with millisecond output and recommends stricter TS compiler flags for accuracy.[^oats-intro] |
| openapi-fetch | 0.17.0 | Typed fetch client using generated schema | 6 kB bundle with schema-accurate params/responses and faster benchmarks than axios or codegen SDKs, so ideal for template consumers.[^oafetch] |
| openapi-react-query | 0.5.4 | Glue between openapi-fetch and React Query | Exposes `$api.useQuery/useMutation` that infer request/response types straight from the spec, so shared hooks never repeat generics.[^oarq] |
| @tanstack/react-query | 5.90.21 | Server-state caching + retries | Canonical async data layer for React web/mobile; integrates with Suspense, devtools, and mutation lifecycles PKG-05 needs.[^tanstack] |
| zod | 4.3.6 | Schema validation for shared forms | Zod’s `.parse/.safeParse` yields inferred TS types so validation + business logic stay in sync.[^zod] |
| react-native-web | 0.21.2 | React Native primitives rendered on web | Official setup doc covers aliasing, Babel/Jest mappings, and SSR root styles so `packages/ui` can export RN components consumed everywhere.[^rnw] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-hook-form | 7.71.1 | Lightweight form controller w/ hook API | All shared form wrappers (login/signup/profile) to minimize re-renders and align validations.[^rhf] |
| @hookform/resolvers | 5.2.2 | Bridge Zod schemas into `useForm` via `zodResolver` | Whenever a shared Zod schema should drive React Hook Form validation (web + mobile).[^rhf] |
| module-alias | 2.3.4 | Map `react-native` → `react-native-web` for SSR/build tooling | Required when rendering shared `packages/ui` components in Node contexts (Next.js RSC, Storybook) per RNW setup guide.[^rnw] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openapi-fetch | axios | axios is 32 kB and ~1.3× slower while offering no schema inference, so it bloats template bundles and reintroduces `any` types.[^oafetch] |
| openapi-react-query | Custom React Query wrappers | Hand-written wrappers repeat endpoint typings and error branches, whereas openapi-react-query auto-infers everything from the schema.[^oarq] |

**Installation:**
```bash
pnpm add openapi-fetch openapi-react-query @tanstack/react-query zod react-hook-form @hookform/resolvers
pnpm add -D openapi-typescript typescript
python -m pip install django-ninja-extra  # already present from earlier phases
```

## Architecture Patterns

### Recommended Project Structure
```
apps/
  api/
    manage.py
    schema/openapi.json        # exported spec committed for reproducibility
packages/
  api-client/
    src/index.ts               # re-exports typed client + helpers
    src/gen/v1.d.ts            # generated by openapi-typescript (git-tracked)
  validation/
    src/auth.ts                # shared Zod schemas (signup/login/profile)
  ui/
    src/primitives/Button.tsx  # React Native Web components
  business-logic/
    src/use-auth.ts            # hooks built on openapi-react-query
scripts/
  generate-openapi.ts          # orchestrates spec export + typegen per turbo task
```

### Pattern 1: Deterministic OpenAPI → Types pipeline
**What:** Export `/api/openapi.json` (or reuse a stored copy) every time backend contracts change, then run `npx openapi-typescript schema.json -o packages/api-client/src/gen/v1.d.ts` and check the file in.[^django-docs][^oats-intro]
**When to use:** Any change to Django controllers/schemas or auth envelope.
**Example:**
```bash
python apps/api/manage.py runserver &
curl http://localhost:8000/api/openapi.json > apps/api/schema/openapi.json
npx openapi-typescript apps/api/schema/openapi.json -o packages/api-client/src/gen/v1.d.ts
```

### Pattern 2: Cross-platform UI primitives
**What:** Implement `packages/ui` components with `react-native` imports (`Pressable`, `Text`, `View`, etc.) and alias `react-native` → `react-native-web` in bundlers, Babel, Jest, and SSR (module-alias) so the same source renders on both clients.[^rnw]
**When to use:** Base controls (buttons, cards, inputs) and layout primitives consumed by Next.js (App Router) and Expo.

### Pattern 3: Query-driven business hooks
**What:** Create a single `client.ts` per API version that instantiates `openapi-fetch`, wraps it via `openapi-react-query`, and export hooks like `useAuthQuery` or `useUpdateProfileMutation` inside `packages/business-logic` so apps only deal with domain hooks.[^oafetch][^oarq][^tanstack]
**When to use:** Auth/user flows (PKG-05/06), eventually CRUD features after Phase 04.

### Anti-Patterns to Avoid
- **Manual axios + handwritten interfaces:** invites drift instantly; rely on generated types + openapi-fetch.
- **Duplicating Zod schemas per app:** one source in `packages/validation` avoids mismatched constraints.
- **Web-only UI components:** breaks PKG-08; React Native Web primitives keep parity.
- **Storing generated `.ts` files out of git:** DX-03 requires diffing generated artifacts; commit them.

## Don't Hand-Roll
| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Typed HTTP client | Custom fetch wrapper | openapi-fetch | Already enforces schema-based URLs/params and ships 6 kB bundle w/ higher throughput.[^oafetch] |
| React Query bindings | Manually typed `useQuery` hooks | openapi-react-query | Auto-infers request/response from spec so hooks never desync.[^oarq] |
| Form validation | Custom validators | Zod + `@hookform/resolvers` | Declarative schemas provide `.safeParse` results and direct binding into forms.[^zod][^rhf] |
| Cross-platform primitives | Separate web/mobile component sets | react-native-web aliasing | Official alias pipeline ensures identical JSX renders across platforms without forks.[^rnw] |

**Key insight:** The OpenAPI schema + shared packages are the contract—every custom wrapper invites drift, so lean on proven libraries that already integrate with TypeScript and React Query ecosystems.

## Common Pitfalls

### Pitfall 1: Stale OpenAPI snapshot
**What goes wrong:** Backend controllers update but `apps/api/schema/openapi.json` and generated types stay old, so api-client returns wrong shapes.
**Why it happens:** No automated export + typegen step in `pnpm generate:types`.
**How to avoid:** Add a turbo pipeline that curls `/api/openapi.json` (or runs `ninja_schema`) and reruns `openapi-typescript`, failing CI when diffs appear.[^django-docs][^oats-intro]
**Warning signs:** `packages/api-client/src/gen` untouched in recent PR even though backend changed.

### Pitfall 2: Missing `noUncheckedIndexedAccess` / type-check gate
**What goes wrong:** Consumers treat optional response properties as guaranteed, causing runtime crashes.
**Why it happens:** TS compiler not run with recommended flags and `tsc --noEmit` script absent.[^oats-intro][^oafetch]
**How to avoid:** Add `tsconfig` flag and a `pnpm test:ts` (tsc --noEmit) step that runs alongside lint/test.
**Warning signs:** CI lacks type-check job; developer uses `as` casts around API data.

### Pitfall 3: React Native Web alias gaps
**What goes wrong:** `packages/ui` works in Expo but fails in Next.js because bundlers resolve `react-native` to Node-specific shims.
**Why it happens:** Missing alias/module-alias config described in RNW docs.
**How to avoid:** Update webpack, Babel, Jest, and Node entry points per RNW setup guide before shipping `packages/ui`.[^rnw]
**Warning signs:** Web build errors complaining about `react-native/Libraries/...` or CSS injection issues.

### Pitfall 4: Throwing on validation failures
**What goes wrong:** Shared forms crash mobile/web clients because Zod `.parse` throws and errors aren’t surfaced inline.
**Why it happens:** Teams forget `.safeParse` pattern React Hook Form expects.[^zod][^rhf]
**How to avoid:** Wrap validation in `safeParse`/`zodResolver` and return field errors to UI packages.
**Warning signs:** Multiple try/catch blocks in forms instead of `formState.errors`.

## Code Examples

### Type generation CLI (tracked artifact)
```bash
# Source: https://openapi-ts.dev/introduction
npx openapi-typescript ./apps/api/schema/openapi.json -o packages/api-client/src/gen/v1.d.ts
```

### Typed fetch + React Query hook
```ts
// Source: https://openapi-ts.dev/openapi-fetch/
import createClient from "openapi-fetch";
import createRQClient from "openapi-react-query";
import type { paths } from "@repo/api-client/gen/v1";

const fetchClient = createClient<paths>({ baseUrl: "https://api.local/v1" });
export const api = createRQClient(fetchClient);

export function useCurrentUser() {
  return api.useQuery("get", "/users/me");
}
```

### Shared Zod schema + React Hook Form
```ts
// Source: https://zod.dev/basics + https://react-hook-form.com/get-started#SchemaValidation
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export function useLoginForm() {
  return useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
  });
}
```

## State of the Art
| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| axios + handwritten DTOs | openapi-fetch + openapi-typescript | 2024 (openapi-ts 7.x release) | Shrinks bundle, enforces spec-accurate params/responses.[^oafetch][^oats-intro] |
| Separate web & mobile component libraries | React Native Web primitives via aliasing | RNW 0.21 docs (Oct 2024) | One UI package feeds both Next.js + Expo with zero forks.[^rnw] |
| Ad-hoc validators or Yup-only forms | Zod + React Hook Form + `zodResolver` | RHF schema validation guide (2024) | Shared schemas infer TS types and plug into both apps, reducing drift.[^zod][^rhf] |

**Deprecated/outdated:** Manual fetch wrappers, web-only UI packages, and validation libs without TS inference.

## Open Questions
1. **Spec export command standardization**
   - What we know: Django Ninja exposes `/openapi.json`, but there’s no repo-level script yet.
   - What’s unclear: Should we add a custom `manage.py` command (e.g., `ninja_schema --output ...`) or rely on curling the endpoint each time?
   - Recommendation: Decide during planning so CI + turbo task know which command to run.
2. **Package build tooling**
   - What we know: Packages currently ship TS source; no bundler is configured.
   - What’s unclear: Should we adopt `tsup` or another builder for `packages/api-client` and `packages/business-logic` to emit both ESM and CJS for downstream template consumers?
   - Recommendation: Planner should pick a builder (tsup or swc) and wire it into turborepo tasks so published packages stay tree-shakeable.

## Sources

### Primary (HIGH confidence)
- Django Ninja Docs – API docs + OpenAPI endpoints (https://django-ninja.dev/guides/api-docs/)
- openapi-typescript Docs – Introduction & CLI guidance (https://openapi-ts.dev/introduction)
- openapi-fetch Docs – Typed client usage + benchmarks (https://openapi-ts.dev/openapi-fetch/)
- openapi-react-query Docs – Hook layer usage (https://openapi-ts.dev/openapi-react-query/)
- TanStack Query Docs – React overview (https://tanstack.com/query/latest/docs/framework/react/overview)
- Zod Docs – Basic usage + safeParse (https://zod.dev/basics)
- React Hook Form Docs – Schema validation + Zod resolver (https://react-hook-form.com/get-started#SchemaValidation)
- React Native Web Docs – Setup/alias instructions (https://necolas.github.io/react-native-web/docs/setup/)

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | All libraries documented via current official docs with version checks. |
| Architecture | MEDIUM-HIGH | Patterns derive from official docs but still need repo-specific scripting decisions. |
| Pitfalls | MEDIUM | Rooted in documented behavior, but enforcement depends on future CI work. |

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (refresh once backend contracts or tooling versions shift)

[^django-docs]: https://django-ninja.dev/guides/api-docs/
[^oats-intro]: https://openapi-ts.dev/introduction
[^oafetch]: https://openapi-ts.dev/openapi-fetch/
[^oarq]: https://openapi-ts.dev/openapi-react-query/
[^tanstack]: https://tanstack.com/query/latest/docs/framework/react/overview
[^zod]: https://zod.dev/basics
[^rhf]: https://react-hook-form.com/get-started#SchemaValidation
[^rnw]: https://necolas.github.io/react-native-web/docs/setup/
