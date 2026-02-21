# UX Design Workflow Integration — Design Document

**Date:** 2026-02-21
**Status:** Approved

## Problem

The foundation template provides strong technical competencies (Django, Next.js, Expo, PGVector, CI/CD) but no design competency. There is no workflow for making UI/UX decisions before coding begins. The result: agents start implementing UI using `frontend-design` with no established personality, tokens, or reference system — producing inconsistent aesthetics across features.

## Goal

Integrate a design-before-coding workflow into Claude Code, GSD, and OpenSpec such that:

- New projects always assess design criticality and establish a design system before any UI is built
- Features and CRs get a lightweight due-diligence check before planning
- The workflow transfers to every new product scaffolded from this template

## Design Principles

- **Tool-agnostic, recommended tools**: Phases define outcomes. Default tools are named as recommendations; alternatives are accepted at phase boundaries.
- **Intensity-gated**: Phase 0 classifies design criticality. The classification gates which phases run — a developer tool should not spend time on Figma high-fidelity screens.
- **Tooling decisions at phase boundaries**: Each phase that needs a specific tool surfaces a one-question checkpoint before starting. This documents tooling decisions in context and prevents tool lock-in upfront.
- **Complementary to `frontend-design`**: This workflow feeds `frontend-design`. Once personality, tokens, and references are established, `frontend-design` generates code consistent with those decisions rather than inventing its own aesthetic.

## What Gets Built

### 1. Skill: `ux-design-workflow`

**Location:** `~/.claude/skills/ux-design-workflow/SKILL.md`
**Invocation:** `/ux-design-workflow` or via Skill tool from CLAUDE.md Rule 7

A process-facilitating skill with two modes:

#### Comprehensive Mode (new project or major overhaul)

| Phase | Name                                | Output                                     | Tooling Checkpoint                                                |
| ----- | ----------------------------------- | ------------------------------------------ | ----------------------------------------------------------------- |
| 0     | UI/UX Role & Criticality Assessment | Intensity classification (High/Medium/Low) | —                                                                 |
| 1     | Personality Workshop                | 5–7 adjectives, tone, anti-patterns doc    | —                                                                 |
| 2     | Reference Mining                    | 10–15 annotated screenshots                | "Default: Mobbin + Figma plugin. Alternative?"                    |
| 3     | Token Decisions                     | Color, typography, radius, spacing         | "Default: tweakcn.com. Alternative?"                              |
| 4     | IA + Wireframes                     | Page/screen inventory, lo-fi structure     | "Default: Figma lo-fi frames. Alternative?"                       |
| 5     | Design System Bootstrap             | shadcn/ui configured with tokens           | "Default: Figma design system file. Alternative?"                 |
| 6     | High-Fidelity Key Screens           | Figma frames for 3–5 critical screens      | "Default: Figma. Skip if Low intensity?"                          |
| 7     | Design → Code                       | Production-ready components                | "Default: Figma MCP. Alternative: frontend-design + screenshots?" |

**Intensity classification gates which phases run:**

| Classification | Phases | Applies to                                    |
| -------------- | ------ | --------------------------------------------- |
| High           | 0 → 7  | Consumer apps, design-led B2B SaaS            |
| Medium         | 0 → 5  | Standard B2B SaaS, marketplaces               |
| Low            | 0 → 3  | Developer tools, API products, internal admin |

**Phase 0 assessment dimensions:**

1. Product type (B2C consumer / B2B SaaS / developer tool / internal tool)
2. Target user design-awareness (design-savvy consumers / enterprise users / developers)
3. Competitive differentiation (is design a primary moat or secondary?)

#### Due-Diligence Mode (feature or change request)

5-question checklist:

1. Does this feature change any visual surface?
2. Does it introduce new components or interaction patterns?
3. Are existing design tokens sufficient, or does it need new ones?
4. Would a Mobbin reference search surface anything useful?
5. Is a Figma frame needed for this feature?

**Scoring:** 3+ yes → mini design sprint before planning. 2 or fewer → proceed using existing design system.

**Tooling checkpoint format (at each relevant phase boundary):**

```
Phase N — [Phase Name]
Tooling decision: Default is [tool] ([brief reason]).
→ Use [tool], or do you have a different approach in mind?
```

Claude records the decision and adapts subsequent phase instructions accordingly (e.g., if Phase 4 uses Excalidraw instead of Figma, Phase 7 skips Figma MCP and uses `frontend-design` + screenshots).

**Skill type:** Technique (process-facilitating). Testing approach: application scenarios — can Claude correctly guide through the workflow and make mode/intensity decisions correctly.

### 2. Foundation Spec: `openspec/specs/foundation/ux-design.md`

**Location:** `openspec/specs/foundation/ux-design.md`
**Transferred to new projects:** Yes (via CLI scaffolder)

Contains:

- Overview: why design process is a foundation competency
- Two modes (comprehensive vs. due-diligence) with rationale
- Phase 0 assessment framework (dimensions + intensity table)
- Phases 1–7: output, default tool, acceptable alternatives, rationale
- Due-diligence checklist with scoring
- Constraints (Phase 0 mandatory, tooling decisions at boundaries, intensity gates, frontend-design as Phase 7 executor)
- Note on Research Files (Self-Contained Specs Rule compliance)

### 3. CLAUDE.md Rule 7

Added after Rule 6 under Tool Coordination Rules:

```
### Rule 7: UI/UX Design Workflow

Before building any user-facing UI, read `openspec/specs/foundation/ux-design.md`.

For new projects (first milestone with UI):
Invoke `ux-design-workflow` skill. Run comprehensive mode (Phase 0 → intensity-gated phases).
Do this BEFORE any GSD phase planning for UI features.

For features or change requests:
Run the due-diligence checklist from openspec/specs/foundation/ux-design.md.
If 3+ questions are yes → invoke ux-design-workflow skill (due-diligence mode) before planning.
If 2 or fewer → proceed using established design tokens and existing components.

Not applicable when:
- Feature has no visual surface (backend-only, CLI, API)
- Change is copy/content update only
- Design decision already made for this feature in the current session
```

### 4. CLI Next Steps Pointer

In `packages/create-foundation-app/src/index.ts`, the `p.outro()` next steps add one line after `git init`:

```
Before coding UI:  Run /ux-design-workflow (Design DNA First — see openspec/specs/foundation/ux-design.md)
```

## Relationship to Existing Skills

- **`superpowers:brainstorming`**: Defines WHAT to build. `ux-design-workflow` defines HOW it should look and feel. Sequence: brainstorming → ux-design-workflow → writing-plans.
- **`frontend-design:frontend-design`**: Implements individual components. `ux-design-workflow` establishes the design system that `frontend-design` works within. They are complementary, not competing.
- **GSD phases**: `ux-design-workflow` runs BEFORE implementation phases are planned — it is pre-planning, not a phase itself.

## Implementation Order

1. Write skill file (`~/.claude/skills/ux-design-workflow/SKILL.md`)
2. Run baseline test (without skill) — required by writing-skills Iron Law
3. Verify skill compliance (with skill)
4. Write foundation spec (`openspec/specs/foundation/ux-design.md`)
5. Add CLAUDE.md Rule 7
6. Update CLI next steps in `index.ts`
7. Commit all changes
