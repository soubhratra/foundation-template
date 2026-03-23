# Global Portfolio Knowledge

Cross-startup learnings and configuration that persists across all startups.

## How it works

1. This folder is part of bizops/ and comes with every clone of foundation-template.
2. Agents read from `global/memory/` at session start for cross-startup wisdom.
3. When a learning applies beyond the current startup, agents flag it and update these files.
4. After a startup concludes (shipped or killed), copy this `global/` folder back to the foundation-template's `bizops/global/` so the next clone inherits all accumulated learnings.

## Workflow

    Start startup #1 (clone template)
        → agents accumulate learnings
        → startup completes or is killed
        → copy bizops/global/ back to foundation-template/bizops/global/
    Start startup #2 (clone template — now includes startup #1 learnings)
        → Co-CEO reads global memory on day 1
        → doesn't repeat startup #1's mistakes

## Files

- `memory/co-ceo-global-memory.md` — Strategic patterns across all startups
- `memory/chief-of-staff-global-memory.md` — Operational patterns
- `memory/skill-improvement-log.md` — All skill optimization history
- `cowork-instructions/co-ceo-persona.md` — Master Co-CEO persona for Cowork global instructions
- `claude-code-instructions/CLAUDE.md` — Startup Execution Protocol addendum (append to root `CLAUDE.md` when initializing a new startup)
