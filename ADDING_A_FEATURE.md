# How to Add a New Feature

This guide documents the end-to-end workflow for adding any significant new feature
to this repo using **Claude Code**, **GSD**, and **OpenSpec** together.

Follow these steps in order. Each tool has a specific role:

| Tool            | Role                                                       |
| --------------- | ---------------------------------------------------------- |
| **OpenSpec**    | Defines WHAT to build — specs, requirements, API contracts |
| **GSD**         | Defines HOW to build it — research, phase plans, execution |
| **Claude Code** | The bridge — reads both, enforces consistency, runs agents |

---

## Step 1: Close the Current Milestone

If a milestone is already complete (all phases done), archive it first.

```
/gsd:complete-milestone
```

This archives the completed milestone and clears ROADMAP.md for the next cycle.
Skip this step if you are mid-milestone or starting fresh.

---

## Step 2: Start a New Milestone

```
/gsd:new-milestone
```

GSD will ask about the milestone goal, scope, and constraints, then produce a
fresh ROADMAP.md with phases for the new feature area.

---

## Step 3: Write the Feature Spec (OpenSpec)

Before any planning or code, define WHAT you are building.

```
/opsx:new [feature-name]
```

Examples:

```
/opsx:new payment-handling
/opsx:new notifications
/opsx:new multi-tenancy
```

If requirements are still fuzzy, explore first:

```
/opsx:explore
```

This creates a change proposal in `openspec/changes/[feature-name]/specs/` with
delta specs capturing the requirements, data models, and API contracts.

> **Rule from CLAUDE.md:** Before writing specs, read `.planning/foundation/STACK.md`,
> `ARCHITECTURE.md`, `CONVENTIONS.md`, and `TESTING.md` to stay consistent with
> approved decisions.

---

## Step 4: Plan Each Phase (GSD)

For each phase in your ROADMAP.md, run the discuss → plan cycle:

```
/gsd:discuss-phase N      # gather context, clarify approach (recommended)
/gsd:plan-phase N         # produce PLAN.md (max 3 tasks per plan)
```

> **Rule from CLAUDE.md:** Before planning, read `openspec/changes/[feature-name]/specs/`
> so phase plans are grounded in the specs from Step 3.

---

## Step 5: Execute Each Phase

```
/gsd:execute-phase N
```

Subagents implement the tasks, commit their work, and produce SUMMARY.md files.
Each task runs in a fresh 200k-token context window.

---

## Step 6: Verify Each Phase

```
/gsd:verify-work N
```

Conversational user acceptance testing. If gaps are found, GSD routes you to
gap-fix plans automatically.

---

## Step 7: Sync Implementation Decisions Back to OpenSpec

After all phases are complete, sync what was actually built back into the
permanent specs (Rule 5 from CLAUDE.md).

```
/opsx:new gsd-milestone-N-sync
```

Then create delta specs in `openspec/changes/[id]/specs/` documenting:

- New patterns introduced
- Tool/version decisions made
- Architecture decisions taken
- Any deviations from the original plan and why

Then archive to merge delta specs into the main specs:

```
/opsx:archive gsd-milestone-N-sync
```

---

## Step 8: Complete the Milestone

```
/gsd:complete-milestone
```

Archives the milestone. Optionally audit first:

```
/gsd:audit-milestone
```

---

## Step 9: Merge the Feature Branch

```
git checkout develop
git merge feat/[feature-name]
git checkout main
git merge develop
```

Use squash merge at milestone completion per the Git conventions in CLAUDE.md.

---

## Quick Reference Table

| Step                          | Tool     | Command                                            |
| ----------------------------- | -------- | -------------------------------------------------- |
| 1. Archive previous milestone | GSD      | `/gsd:complete-milestone`                          |
| 2. Define new milestone       | GSD      | `/gsd:new-milestone`                               |
| 3. Write feature spec         | OpenSpec | `/opsx:new [feature-name]`                         |
| 4. Plan phases                | GSD      | `/gsd:discuss-phase N` → `/gsd:plan-phase N`       |
| 5. Build                      | GSD      | `/gsd:execute-phase N`                             |
| 6. Test                       | GSD      | `/gsd:verify-work N`                               |
| 7. Sync specs                 | OpenSpec | `/opsx:new gsd-milestone-N-sync` → `/opsx:archive` |
| 8. Close milestone            | GSD      | `/gsd:complete-milestone`                          |
| 9. Merge branch               | Git      | `git merge feat/[feature-name]`                    |

---

## Branch Strategy

Always work on a dedicated feature branch:

```bash
git checkout develop
git checkout -b feat/[feature-name]
```

Merge back through `develop` → `main` when the milestone is complete.

---

## When to Use `/gsd:quick` Instead

For small changes touching fewer than 3 files, skip the full workflow:

```
/gsd:quick "description of the small change"
```

Use the full workflow above for anything that spans multiple files, apps, or
introduces new data models, API endpoints, or infrastructure.

---

## Key Files to Read Before Starting

| Need to understand... | Read                                        |
| --------------------- | ------------------------------------------- |
| Tech stack decisions  | `openspec/specs/foundation/stack.md`        |
| Architecture patterns | `openspec/specs/foundation/architecture.md` |
| Coding conventions    | `openspec/specs/foundation/conventions.md`  |
| Current roadmap       | `.planning/ROADMAP.md`                      |
| Current state         | `.planning/STATE.md`                        |
