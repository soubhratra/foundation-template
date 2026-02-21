# UX Design Workflow Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

Design is not a polish step applied at the end of development. It is an upfront decision-making process that determines whether a product is usable before a single line of UI code is written. Retrofitting poor information architecture, mismatched visual language, or inconsistent token choices after implementation is substantially more expensive than resolving them in design artifacts.

This spec establishes the UX Design Workflow as a foundation-level competency — required for all products built from this template, not optional. It defines the phased process, the tooling defaults at each phase, and the intensity gates that determine which phases apply to a given effort.

**Relationship to adjacent skills:**

- This spec defines the design process: what to produce, in what order, with what tools, and why.
- The `frontend-design` skill is the executor of Phase 7 (Design → Code). It takes Figma outputs produced by this workflow and converts them to production components.
- The `ux-design-workflow` personal skill is the executable procedure aligned to this spec. This spec is the authority; the personal skill is the operator.

---

## Specifications

### Two Modes

Every UI effort — new product, major overhaul, feature addition, or change request — is classified into one of two modes before any design work begins.

#### Comprehensive Mode

**Applies when:** A new product, a new user-facing domain, or a major overhaul of an existing experience (substantial screen additions, navigation restructuring, brand refresh).

**Process:** Phase 0 → intensity-gated phases 1–7.

**Rationale:** Comprehensive efforts introduce enough new design surface that incremental checklists are insufficient. They require personality alignment (Phase 1), reference grounding (Phase 2), and token decisions (Phase 3) before any wireframes are drawn — because these upstream decisions constrain every downstream artifact. Skipping them produces wireframes that cannot be implemented coherently: no agreed visual language, no token system, no reference baseline.

**Rejected alternative:** Applying due-diligence mode to all efforts regardless of scope. Due-diligence is fast and appropriate for small features, but it does not establish the design system foundations that larger efforts require. Using it for a new product produces a series of individually-checked features with no shared visual identity.

#### Due-Diligence Mode

**Applies when:** Adding a feature to an existing product, implementing a change request (CR), or modifying a screen or flow where the design system is already established.

**Process:** 5-question checklist (see Due-Diligence Checklist section). Score determines whether a mini design sprint is warranted or work proceeds directly.

**Rationale:** Most feature additions do not require a full personality workshop or reference mining session — the design system already answers those questions. What matters is whether the new feature introduces novel UX patterns, significant new information architecture, or user-journey branches that have not been resolved. The checklist surfaces those cases without requiring the full workflow for routine additions.

**Rejected alternative:** Applying full comprehensive mode to all feature additions. This creates excessive overhead for changes like "add a filter dropdown to an existing list view" where the component system, token set, and visual language are already established.

---

### Phase 0: UI/UX Role and Criticality Assessment

Phase 0 is mandatory and always the first step, regardless of mode. No design work begins without completing this assessment.

**Output:** A written intensity classification (High / Medium / Low) with documented rationale, and a list of which subsequent phases apply.

#### Three Assessment Dimensions

**1. User-Facing Surface Area**
How much of the product's value is delivered through the interface itself, as opposed to backend processing, integrations, or data pipelines? A dashboard product where users spend hours daily has high surface area. An API product with a minimal admin UI has low surface area.

**2. Competitive UX Baseline**
What do users already expect from comparable products? Markets with strong UX incumbents (project management, consumer finance, e-commerce) raise the baseline. Niche B2B tools with captive users have lower competitive UX pressure. A product entering a market with strong UX incumbents cannot survive with mediocre design.

**3. Conversion and Trust Dependency**
How directly does UX quality affect business outcomes? If poor UX causes users to abandon signup, drop off mid-onboarding, or distrust the product during a trial, the cost is direct revenue loss. Internal tools used by locked-in employees have lower stakes than consumer-facing acquisition flows.

#### Intensity Classification Table

| Intensity  | Trigger Criteria                                                                                                        | Phases Applied                                      | Rationale                                                                                                                                                                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **High**   | Two or more of: consumer-facing, strong UX competitors, conversion-critical flows, new user-facing domain               | Phases 1 → 7 (all)                                  | Full workflow is required when all three dimensions are elevated. Skipping hi-fi screens or Figma-to-code handoff at this intensity introduces implementation ambiguity at exactly the moment precision matters most.    |
| **Medium** | One of the above, or: internal tool with moderate complexity, B2B with multiple user roles                              | Phases 1 → 5 (skip hi-fi and Figma MCP)             | IA and a design system bootstrap are required to maintain coherence. Hi-fi screens and Figma MCP handoff are not cost-effective — engineering can implement from the design system and wireframes.                       |
| **Low**    | None of the above: internal tooling, admin screens, single-user utilities, data entry forms with no competitive context | Phases 1 → 3 (personality, references, tokens only) | The visual language must still be intentional. Skipping tokens and personality entirely produces inconsistent products even at low intensity. But full IA, wireframes, and design system artifacts are disproportionate. |

#### Why Skipping Phase 0 Is Harmful

Phase 0 is not a bureaucratic gate. It determines which subsequent phases are worth the investment. Without it, teams either over-design low-stakes screens (wasting time) or under-design high-stakes flows (paying with user churn). Both errors are observable and expensive. Phase 0 takes 15–30 minutes and prevents both failure modes.

---

### Phase 1: Personality Workshop

**Output:** A written personality document capturing 3–5 adjective pairs (e.g., "precise but warm", "powerful but approachable"), a primary emotional target (what the user should feel after a session), and two or three anti-patterns to actively avoid in design decisions.

**What:** A structured conversation — between the product owner and AI, or within a design team — that articulates the product's intended character before any visual or structural decisions are made. Adjective pairs name the tension the design must hold. Anti-patterns make exclusions explicit.

**Why personality before tokens:** Token decisions (color palette, typography, radius, spacing) are implementations of personality. A personality described as "clinical and precise" leads to tight radius, cool neutrals, and monospace data typography. "Warm and approachable" leads to generous radius, warm neutrals, and humanist sans-serif fonts. Making token decisions without an agreed personality produces arbitrary choices that feel inconsistent in aggregate — different screens reflect different implied personalities because each was designed by a different person (or AI session) without a shared reference.

**Rejected alternative:** Skipping the personality workshop and going directly to visual references or token decisions. This produces a "vision by accumulation" problem: each reference added looks good individually, but the collection has no coherent identity. Token decisions made without personality alignment drift toward personal preferences rather than product character.

---

### Phase 2: Reference Mining

**Output:** A curated set of 10–20 annotated screenshots from real, shipped applications that exemplify specific aspects of the desired personality and interaction patterns. Annotations call out what is being captured (not just "this looks good" but "generous whitespace creates perceived premium", "destructive actions use outlined buttons not filled to reduce anxiety").

**Default tool:** Mobbin (mobbin.com). Mobbin provides a searchable database of real app screens organized by category, platform, and interaction pattern.

**Alternatives considered:**

- **Dribbble / Behance:** Design portfolio sites, not product references. They show highly stylized concept work optimized for visual impressiveness, not real-world usability. The gap between portfolio aesthetics and implemented product quality is wide. Rejected because they train the wrong instincts.
- **Screenlane / Scrnshts:** Comparable to Mobbin. Acceptable substitutes if Mobbin access is unavailable.
- **Manual screenshots from competitor apps:** Valid, especially for direct competitors. Capture directly from production apps on device.

**Why real app references, not mockups:** Shipped applications represent design decisions that survived implementation constraints, user testing, and engineering tradeoffs. Mockups represent ideal-case thinking. References from Mobbin reflect what is actually achievable and what users have been conditioned to expect. References from Dribbble reflect what looks impressive in isolation.

**Why annotate:** Unannotated references are a collection of images. Annotated references are a design brief. Annotations force the reviewer to articulate what is being captured, which surfaces disagreements early and creates a shared vocabulary for subsequent phases.

---

### Phase 3: Token Decisions

**Output:** A resolved token set covering: primary and secondary color palette, neutral scale, semantic colors (success, warning, error, info), typography scale (font family, size scale, weight scale), border radius, spacing scale, and shadow system.

**Default tool:** tweakcn.com — a visual theme editor for shadcn/ui that generates a CSS variable token set compatible with Tailwind CSS and shadcn/ui components.

**Decision order:**

1. **Primary brand color** (informed by personality — cool/warm, saturated/muted)
2. **Neutral scale** (derived from primary — slightly warm or cool tinted neutrals, not pure grey)
3. **Semantic colors** (success/warning/error — ensure WCAG AA contrast on both light and dark backgrounds)
4. **Typography** (font family first, scale second; Google Fonts or system fonts unless custom licensed)
5. **Radius** (small=2px, medium=6px, large=12px for "precise"; medium=8px, large=16px for "friendly")
6. **Spacing scale** (4px base, 8-point grid)
7. **Shadows** (flat → subtle → pronounced; match elevation model to personality)

**Why tweakcn.com:** The template stack uses shadcn/ui as the UI component library (see `openspec/specs/foundation/stack.md`). tweakcn.com generates a token set in exactly the format shadcn/ui expects — CSS variables consumed by Tailwind CSS. Using it eliminates the translation step between "decided token values" and "tokens in code". The output is copy-pasteable into the project's `globals.css`.

**Why this order:** Color decisions inform neutrals (warm vs cool tint). Neutrals inform typography legibility judgments. Typography scale informs spacing (line height, paragraph rhythm). This cascade means reversing the order requires rework — choosing a tight radius before deciding on a warm color palette may produce a mismatch that sends the team back to step 1.

**Rejected alternative:** Picking tokens directly in Figma styles without a structured editor. Figma color pickers produce disconnected HSL values that must be manually converted to CSS variables and Tailwind config. This creates a synchronization burden — Figma styles diverge from the codebase within weeks of launch as one is updated and the other is not.

**Constraint:** tweakcn.com assumes shadcn/ui. Projects using a different component system must substitute an equivalent tool that targets their component library's token format, or define tokens manually as CSS variables following the same decision order.

---

### Phase 4: Information Architecture and Wireframes

**Applies to:** Medium and High intensity efforts only.

**Output:** A site/app map (navigational IA) and low-fidelity wireframes for all primary flows. Wireframes use greyscale, placeholder typography, and no brand tokens — layout, hierarchy, and interaction logic only.

**Default tool:** Figma. IA maps as connected frames with auto-layout. Wireframes using Figma's built-in wireframe component kit or a minimal wire kit.

**Alternatives considered:**

- **FigJam:** Appropriate for IA mapping only. Switch to Figma proper for wireframes.
- **Whimsical:** Acceptable for teams without Figma access. Export and annotate before Phase 5.
- **Paper/whiteboard:** Valid for early exploration. Must be digitized before Phase 5 handoff.

**Why IA before design:** Navigation structure and page hierarchy are architectural decisions. Getting them wrong means screens designed in Phase 5 (design system) or Phase 6 (hi-fi) must be restructured — which invalidates the component hierarchy. IA decisions are cheap to change as boxes on a map. They are expensive to change as built screens.

**Why lo-fi wireframes, not hi-fi:** Hi-fi wireframes create premature attachment to visual details that are not yet decided (tokens are set but design system components are not yet built). Reviewers — including non-designers — fixate on color and typography instead of evaluating layout and flow logic. Lo-fi wireframes force feedback on structure, which is what Phase 4 is designed to validate.

---

### Phase 5: Design System Bootstrap

**Applies to:** Medium and High intensity efforts only.

**Output:** A Figma component library containing the core component set: Button (all variants), Input, Select, Checkbox, Radio, Toggle, Badge, Card, Modal/Dialog, Alert/Toast, Navigation (sidebar or top bar), and Data Display (table or list). All components use published Figma variables mapped to the token set from Phase 3.

**Default tool:** Figma with Variables (not Styles — Variables support theming and dark mode).

**Alternatives considered:**

- **Storybook-first (build in code, not Figma):** Valid for engineering-led teams. Risk: the visual decision layer is collapsed into implementation, making design review harder for non-engineers. Acceptable if the team is comfortable evaluating design in a browser.
- **Zeroheight or Supernova:** Documentation tools, not design system builders. Use for publishing after the system is built, not during creation.

**Why at this stage, before hi-fi:** The design system is the vocabulary for hi-fi screens. Building hi-fi screens without a system produces components that are inconsistent across screens — the same button appears in three slightly different sizes, the same card shadow appears in two variants. Establishing the system first means hi-fi screens are assembled from validated building blocks, not drawn from scratch.

**Why Figma Variables, not Styles:** Figma Styles are static values. Variables support scoping by mode (light/dark) and can be aliased (brand-primary → color-primary-500). Aliased variables make global token changes — changing the primary hue — propagate to all components automatically. Styles require manual updates per component.

---

### Phase 6: High-Fidelity Key Screens

**Applies to:** High intensity efforts only.

**Output:** Pixel-resolved Figma frames for the 5–8 screens that carry the highest design risk. Typically: the primary value screen (the "aha" moment), the onboarding entry point, the primary data entry flow, the empty state, and the error/recovery state.

**Default tool:** Figma, using the component library from Phase 5. No new components introduced in hi-fi — if a design requires a component not in the Phase 5 library, pause and add it to the library first.

**Why only High intensity:** At Medium intensity, the design system and wireframes provide sufficient fidelity for engineering to implement correctly. Hi-fi is cost-effective only when: (a) the product is consumer-facing and visual differentiation matters, (b) there are ambiguous interaction patterns that engineering cannot resolve from wireframes alone, or (c) stakeholder approval requires visual fidelity. None of those conditions are routinely present in Medium intensity efforts.

**Why only key screens, not all screens:** Full hi-fi coverage for every screen is rarely cost-effective. Most screens — settings pages, secondary flows, data tables — can be implemented from the design system and wireframes without ambiguity. Key screens are those where the design decision is non-obvious, where visual differentiation creates competitive advantage, or where misimplementation would directly harm user trust.

---

### Phase 7: Design to Code

**Applies to:** High intensity efforts only.

**Output:** Production-ready React/React Native components implemented from the Phase 6 Figma frames, with Tailwind CSS classes derived from the Phase 3 token set.

**Default tool:** Figma MCP (Model Context Protocol integration for Figma). The Figma MCP exposes design file structure and computed styles to AI coding agents, enabling precise translation of Figma frames to component code without manual inspection.

**Alternatives considered:**

- **Manual implementation from Figma inspect:** Valid and the historical standard. Slower — requires the developer to read Figma properties and translate to Tailwind classes by hand. Acceptable when Figma MCP is unavailable or the developer prefers direct control.
- **Anima / Builder.io / Locofy (auto-code generators):** These tools generate code directly from Figma frames without a development agent in the loop. They produce structurally correct code but with unreadable class names, no semantic component boundaries, and no accommodation for the project's existing component system. The output requires as much cleanup as writing from scratch. Rejected.
- **Figma Dev Mode (manual inspect):** The standard Figma developer handoff mode. Adequate for Medium intensity where engineering implements from wireframes and the design system. At High intensity, the precision requirement justifies MCP over manual inspection.

**Why Figma MCP:** The Figma MCP gives AI coding agents (Claude Code, Cursor) access to exact design values — computed pixel sizes, resolved variable values, layer hierarchy — without the agent having to infer values from screenshots. Screenshot-based implementation (having the agent look at a PNG) produces approximations. MCP-based implementation produces exact matches. At High intensity, exactness is required.

**Executor:** The `frontend-design` skill handles Phase 7 execution. This spec defines what to hand off (Phase 6 frames, Phase 3 tokens, Phase 5 component library). The `frontend-design` skill defines how to execute the translation.

---

### Due-Diligence Checklist

For every feature addition or change request in an established product, answer the following five questions before beginning implementation. This check takes 5 minutes. It is non-optional.

**The 5 Questions:**

1. Does this feature introduce a user flow that does not exist anywhere in the current product? (New navigation paths, new modal sequences, new multi-step processes)
2. Does this feature introduce a new information hierarchy — new data types displayed to users, new grouping or categorization patterns not in the existing IA?
3. Does this feature affect a conversion-critical or trust-critical surface? (Onboarding, checkout, data input in high-stakes contexts)
4. Does this feature require a new UI component type not covered by the existing design system?
5. Does this feature change user expectations set by the existing design? (Changing a flow users already know, repurposing a gesture, changing a visual signifier)

**Scoring:**

- **3 or more "yes" answers:** Run a mini design sprint. This is a compressed Phase 0 → Phase 2 → Phase 4 sequence. No personality workshop needed (already established). Conduct reference mining for the new pattern, wireframe the flow, validate, then implement. Estimated time: 2–4 hours before coding begins.
- **2 or fewer "yes" answers:** Proceed to implementation using the existing design system and wireframes as needed.

**Why due-diligence is non-optional even for small features:** "Small" features routinely introduce large UX debt when the design check is skipped. A filter panel added without checking IA impact may duplicate functionality that already exists elsewhere. A new data display added without a reference check may use a pattern inconsistent with every other data display in the product. The 5-minute check prevents compounding inconsistency. Inconsistency is the primary source of UX debt in mature products.

---

## Constraints

1. **Phase 0 is mandatory before all other phases.** No design work begins — no personality workshop, no references, no wireframes — without a documented intensity classification. The classification determines every subsequent phase selection.

2. **Tooling decisions are made at phase boundaries, not upfront.** Do not select the full tool stack at project start. Decide the Phase 1 tool at Phase 1, the Phase 2 tool at Phase 2, and so on. Tooling selected upfront is optimized for the wrong questions — the actual bottleneck at Phase 4 (IA) may differ from what was predicted at project kickoff.

3. **Intensity gates phases strictly.** Low intensity: Phases 1–3 only. Medium intensity: Phases 1–5 only. High intensity: Phases 1–7. Phases 6 and 7 MUST NOT be applied to Medium or Low efforts regardless of preference. They are cost-effective only at High intensity.

4. **The `frontend-design` skill is Phase 7's executor.** This spec defines the design handoff requirements. The `frontend-design` skill defines the implementation execution. Do not conflate design production (this spec) with code production (frontend-design skill).

5. **Due-diligence is non-optional for all UI feature additions.** Every PR that touches user-facing screens in an established product must include a documented due-diligence check. Skipping it is not a time-saving measure; it is deferred UX debt with compound interest.

6. **tweakcn.com as token tool assumes shadcn/ui.** This template uses shadcn/ui as the default UI component library. tweakcn.com targets shadcn/ui's CSS variable schema. If a project substitutes a different component library, substitute an equivalent token tool targeting that library's format, or define tokens manually as CSS custom properties following the Phase 3 decision order.

## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
