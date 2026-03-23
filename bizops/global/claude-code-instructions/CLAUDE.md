# Startup Execution Protocol — Claude Code Addendum

> **How to use this file:** Append the section below to the root `CLAUDE.md` when initializing a new startup from the foundation template. This bridges Claude Code into the bizops system (phase gates, critique loops, memory) without duplicating the engineering rules already in the root CLAUDE.md.
>
> The root `CLAUDE.md` already handles: tech stack, architecture rules, coding conventions, OpenSpec/GSD tool coordination, testing, and monorepo structure. This addendum adds: startup phase awareness, the Read-Execute-Write session protocol, critique loop for engineering deliverables, and memory persistence.
>
> **Do NOT use this as `~/.claude/CLAUDE.md`.** It belongs appended to the project-level CLAUDE.md at the monorepo root.

---

## Startup Execution Protocol

This project follows the Startup Execution Pipeline. Business operations live in `bizops/`. Claude Code owns engineering deliverables; Cowork (the AI Co-CEO) owns business deliverables. Both agents read `bizops/STARTUP.md` as the single source of truth for phase, gate status, and quality scores.

### Session Protocol: Read-Execute-Write

**Every session, follow this protocol in addition to the tool coordination rules above:**

#### 1. READ (before doing anything)

- Read `bizops/STARTUP.md` — know the current phase, gate status, and system health
- Read `bizops/memory/engineering-memory.md` — your accumulated learnings and anti-patterns
- Read `bizops/global/memory/co-ceo-global-memory.md` — cross-startup patterns
- If in Phase 3+, read `bizops/phase-3/prd.md` — feature requirements driving implementation
- Check `bizops/context/product-info.md` for scope boundaries
- Then proceed with normal OpenSpec/GSD reads per the Tool Coordination Rules above

#### 2. EXECUTE (do the work)

- Apply learnings from memory — especially anti-patterns and past sprint failures
- Follow OpenSpec/GSD workflow for all implementation (specs → plans → code)
- Run the Critique Loop (below) on engineering deliverables before marking phases complete
- Post updates to the build channel defined in `bizops/STARTUP.md`
- Surface cross-domain impacts unprompted (e.g., "this architecture choice adds 2 sprints to the GTM timeline")

#### 3. WRITE-BACK (before ending)

- Update `bizops/memory/engineering-memory.md` with decisions, learnings, quality scores
- Update `bizops/STARTUP.md` with engineering phase outputs (sprint scores, test coverage, deployment status)
- Flag any learnings that apply cross-startup → update `bizops/global/memory/co-ceo-global-memory.md`
- Sync implementation decisions to OpenSpec per Rule 5 (after milestone completion)

### Critique Loop for Engineering Deliverables

Before marking ANY engineering deliverable complete, run this loop:

1. **Self-review**: Load the eval JSON for that deliverable type (see table below). Score your output against every assertion — TRUE or FALSE. Be ruthlessly honest.
2. **Peer-review**: Re-read the deliverable as if you didn't write it. Score each assertion independently. Disagreements between self and peer default to FAIL.
3. **Check threshold**: If pass rate >= `pass_threshold`, mark complete. If below, revise and re-score. Maximum 3 iterations.
4. **Log results**: Append scores to the eval JSON `history` array. Write learnings to `bizops/memory/engineering-memory.md`.
5. **Escalate if stuck**: If 3 iterations fail, post to the gates channel as an ESCALATION — don't silently ship sub-threshold work.

#### Engineering Eval Files

| Deliverable       | Eval file                                  | Phase | Threshold             |
| ----------------- | ------------------------------------------ | ----- | --------------------- |
| Architecture doc  | `bizops/docs/eval-architecture.json`       | 3     | 80%                   |
| Sprint output     | `bizops/docs/eval-engineering-sprint.json` | 4     | 87.5%                 |
| Production deploy | `bizops/docs/eval-deploy.json`             | 5     | 100% (non-negotiable) |

Each eval JSON contains `assertions[]` (binary TRUE/FALSE checks), `pass_threshold`, `meta_assertion` (overall quality question), and `history[]` (append scores here).

### Cross-Check Protocol (Phase 3)

After your architecture critique passes, run a cross-check against business deliverables:

```bash
bizops/scripts/cross-check.sh 3
```

This checks `bizops/phase-3/prd.md` + `bizops/phase-3/gtm-plan.md` + your architecture doc for contradictions, scope mismatches, and timeline conflicts. Critical contradictions must be resolved before posting the gate summary.

### Available bizops Scripts

| Script                                                 | Purpose                           |
| ------------------------------------------------------ | --------------------------------- |
| `bizops/scripts/critique.sh <deliverable> <eval-json>` | Headless critique loop            |
| `bizops/scripts/cross-check.sh <phase>`                | Cross-document consistency check  |
| `bizops/scripts/overnight-improve.sh`                  | Nightly skill optimization (cron) |

### Gate Post Format (Engineering)

When posting to the startup's gates or build channel:

```
🚪 GATE [N] READY: [ProjectName] — engineering [phase] complete.

[Key output summary — 1-2 lines]

📊 Quality Report:
- [Deliverable]: [X/Y] assertions passed ([Z]%) [✅/⚠️/❌]
- Failed: [list specific failures]
- Meta-assertion: [PASS/FAIL]
- Critique iterations: [N]
- Test coverage: [X]%
- Spec traceability: [X] requirements covered / [Y] total

Full outputs: bizops/phase-[N]/ + relevant code in apps/
Reply: ✅ approve | 🔄 redirect [notes] | ❌ kill
```

### Startup-Specific File Reference

| Need to understand...              | Read                                           |
| ---------------------------------- | ---------------------------------------------- |
| Current startup phase & status     | `bizops/STARTUP.md`                            |
| Engineering memory & anti-patterns | `bizops/memory/engineering-memory.md`          |
| Cross-startup learnings            | `bizops/global/memory/co-ceo-global-memory.md` |
| Product scope & boundaries         | `bizops/context/product-info.md`               |
| ICP (who we're building for)       | `bizops/context/ideal-customer.md`             |
| PRD & feature requirements         | `bizops/phase-3/prd.md`                        |
| Architecture eval assertions       | `bizops/docs/eval-architecture.json`           |
| Sprint eval assertions             | `bizops/docs/eval-engineering-sprint.json`     |
| Deployment eval assertions         | `bizops/docs/eval-deploy.json`                 |
