# Startup Execution Pipeline v2.0

**Purpose**: An autonomous, self-improving system for taking a SaaS startup from idea to operating business. Every agent learns, every deliverable is critiqued, every decision is traceable, and the system gets sharper with each execution cycle.

**Architecture principle**: The founder is the board. The Co-CEO runs the company. The system has an immune system — built-in quality gates, critique loops, and binary assertions that catch problems before the founder ever sees them.

**What changed from v1.0**: v1.0 was a linear pipeline with human gates. v2.0 adds three layers:

1. **Nervous System** — Per-agent memory that persists learnings across sessions
2. **Immune System** — Critique loops and binary assertions on every deliverable before it reaches a gate
3. **Evolution System** — Self-improving skill loops that optimize agent performance overnight

**Structural changes from v1.0**:

- **Single monorepo**: `bizops/` is added to the existing foundation-template monorepo alongside `apps/`, `packages/`, `docs/`, etc. No separate repos. Clone once via the CLI tool, everything's there.
- **Per-startup Slack channels**: Each startup gets its own channel set (`[name]-gates`, `[name]-build`, `[name]-quality`). No cross-talk between startups.

---

## Monorepo Structure

The foundation-template is already a working monorepo with engineering code. We add `bizops/` as a new top-level folder for all business operations — the Co-CEO's workspace. Everything else stays where it is.

```
[startup-name]/                     # ← Cloned from foundation-template via CLI
│
│── STARTUP.md                      # State machine — the single source of truth
│── CLAUDE.md                       # (existing) Project-level Claude Code instructions
│── AGENTS.md                       # (existing) Agent team definitions
│── ADDING_A_FEATURE.md             # (existing) Engineering workflow docs
│── DEV_SETUP.md                    # (existing) Developer setup guide
│── DEV_LOGS.md                     # (existing) Development logs
│── README.md                       # (existing) Repo readme
│
├── apps/                           # (existing) Engineering code
│   ├── api/                        # Django Ninja Extra backend
│   ├── web/                        # Next.js + Shadcn/ui frontend
│   ├── mobile/                     # Expo / React Native
│   └── e2e/                        # End-to-end tests
│
├── packages/                       # (existing) Shared packages
├── docs/                           # (existing) Technical documentation
│   ├── architecture.md             # System architecture (populated Phase 3)
│   ├── api-spec.md                 # API specification
│   ├── decisions/                  # ADRs
│   ├── eval-architecture.json      # Architecture quality assertions
│   ├── eval-deploy.json            # Deployment quality assertions
│   └── eval-engineering-sprint.json # Per-sprint quality assertions
│
├── openspec/                       # (existing) OpenAPI specs
│   ├── AGENTS.md
│   ├── config.yaml
│   ├── changes/
│   └── specs/
│
├── scripts/                        # (existing) Build/deploy scripts
│   ├── critique.sh                 # NEW: Headless critique script
│   ├── overnight-improve.sh        # NEW: Nightly skill optimization
│   └── cross-check.sh              # NEW: Cross-document consistency checker
│
├── .claude/                        # (existing or new) Claude Code agent config
│   ├── skills/                     # Project-specific SME agent skills
│   │   └── [sme-skill]/
│   │       ├── SKILL.md
│   │       └── eval.json           # Skill-specific assertions for improvement loops
│   └── commands/
│       ├── sprint.md               # /sprint — plan next sprint
│       ├── build-report.md         # /build-report — post to Slack
│       ├── deploy.md               # /deploy — run deployment checklist
│       ├── critique.md             # /critique — run critique loop on any deliverable
│       └── improve.md              # /improve — run skill improvement loop
│
├── bizops/                         # NEW — Cowork points here
│   ├── .claude-instructions        # Co-CEO persona + critique loop protocol for Cowork
│   ├── context/                    # Context engineering outputs (populated Phase 2)
│   │   ├── about-founder.md
│   │   ├── brand-voice.md
│   │   ├── ideal-customer.md
│   │   ├── product-info.md
│   │   ├── voice-dna.md
│   │   └── working-preferences.md
│   ├── memory/                     # Per-startup agent memories
│   │   ├── co-ceo-memory.md        # Strategic decisions for THIS startup
│   │   ├── engineering-memory.md   # Technical decisions, debt tracking
│   │   ├── validation-memory.md    # Market research learnings
│   │   ├── gtm-memory.md           # Marketing learnings, channel performance
│   │   ├── product-memory.md       # User feedback patterns, feature outcomes
│   │   ├── chief-of-staff-memory.md # Operational patterns
│   │   └── [sme-agent]-memory.md   # Domain-specific learnings per SME
│   ├── global-memory/              # Cross-startup learnings (portable between repos)
│   │   ├── co-ceo-global-memory.md
│   │   ├── chief-of-staff-global-memory.md
│   │   └── skill-improvement-log.md
│   ├── eval-templates/             # Standard assertion templates (reusable)
│   │   ├── eval-idea-briefs.json
│   │   ├── eval-competitor-matrix.json
│   │   ├── eval-market-sizing.json
│   │   ├── eval-validation-report.json
│   │   ├── eval-context.json
│   │   ├── eval-prd.json
│   │   ├── eval-gtm.json
│   │   ├── eval-copy.json
│   │   └── eval-tech-feasibility.json
│   ├── phase-0/                    # Ideation outputs
│   │   ├── program.md
│   │   └── .gitkeep
│   ├── phase-1/                    # Validation outputs
│   │   ├── program.md
│   │   └── .gitkeep
│   ├── phase-3/                    # Spec + GTM outputs
│   │   ├── program.md
│   │   └── .gitkeep
│   ├── marketing/                  # Ongoing marketing assets
│   ├── finance/                    # Financial models, projections
│   ├── investors/                  # Pitch deck, updates, data room
│   └── operations/                 # Sprint reports, decision logs
│
├── docker-compose.yml              # (existing)
├── docker-compose.prod.yml         # (existing)
├── package.json                    # (existing)
├── pnpm-workspace.yaml             # (existing)
├── pnpm-lock.yaml                  # (existing)
├── turbo.json                      # (existing)
├── ruff.toml                       # (existing)
├── eslint.config.js                # (existing)
└── .gitignore
```

**Key design decisions:**

- `bizops/` sits alongside `apps/`, `packages/`, `docs/` as a peer folder in the monorepo. It's the Co-CEO's workspace. Cowork points at `bizops/`.
- Claude Code works at the monorepo root (as it already does). It has access to everything — `apps/`, `docs/`, `bizops/`, `.claude/`.
- `STARTUP.md` lives at the monorepo root next to `CLAUDE.md` and `AGENTS.md`. Both Cowork and Claude Code read it.
- All agent memories live in `bizops/memory/` — including `engineering-memory.md`. This centralizes memory in one place rather than scattering it across `docs/` and `bizops/`.
- `bizops/global-memory/` holds cross-startup learnings. When you clone the template for Startup #3, you copy over the latest global memory files from your previous startup.
- Engineering eval files (`eval-architecture.json`, `eval-deploy.json`, `eval-engineering-sprint.json`) live in `docs/` because they're documentation about the codebase. Business eval templates live in `bizops/eval-templates/`.
- New scripts (`critique.sh`, `overnight-improve.sh`, `cross-check.sh`) go in the existing `scripts/` folder.
- New Claude Code commands go in `.claude/commands/` alongside any existing commands.

---

## Per-Startup Slack Channels

Each startup gets its own set of three Slack channels. No shared channels, no cross-talk.

| Channel Pattern  | Purpose                                                        | Who Posts          | Who Reads                |
| ---------------- | -------------------------------------------------------------- | ------------------ | ------------------------ |
| `[name]-gates`   | Gate decisions, escalations, founder approvals                 | Co-CEO, agents     | Founder                  |
| `[name]-build`   | Daily build summaries, sprint progress                         | Claude Code agents | Founder (skim daily)     |
| `[name]-quality` | Critique scores, skill improvement results, assertion failures | Automated posts    | Founder (weekly), Co-CEO |

**Channel configuration lives in STARTUP.md:**

```yaml
## Slack Channels
- gates: acme-gates
- build: acme-build
- quality: acme-quality
```

Every agent prompt references `STARTUP.md` for channel names. When the Co-CEO posts a gate summary, it reads the channel name from STARTUP.md — not from a hardcoded value. This means you can rename channels, split channels, or add custom channels per-startup without touching any skill files.

**Why per-startup channels work with Cowork**: Cowork's Slack MCP connector can post to any channel by name or ID. The agent prompt includes `Post gate summary to Slack channel: [read from STARTUP.md → slack.gates]`. Cowork resolves the channel name at runtime. No special configuration needed beyond having the Slack MCP connector active.

**Setup per startup** (30 seconds in Slack):

1. Create `[name]-gates`, `[name]-build`, `[name]-quality` channels
2. Update the `Slack Channels` section in STARTUP.md with the channel names
3. Done — all agents will post to the right place

---

## Core Architecture: The Three Systems

### System 1: The Nervous System (Per-Agent Memory)

Every agent maintains its own `memory.md`. This is not shared memory — each agent learns domain-specific lessons from its own executions. The Co-CEO's memory tracks strategic patterns. The QA agent's memory tracks recurring bug patterns. The GTM agent's memory tracks what messaging resonated.

**Two-tier memory hierarchy:**

```
[startup-repo]/
├── bizops/memory/                 # Per-startup memories (ALL agents)
│   ├── co-ceo-memory.md           # Strategic decisions for THIS startup
│   ├── engineering-memory.md      # Technical decisions, debt tracking
│   ├── validation-memory.md       # Market research learnings
│   ├── gtm-memory.md              # Marketing learnings, channel performance
│   ├── product-memory.md          # User feedback patterns, feature outcomes
│   ├── chief-of-staff-memory.md   # Operational patterns
│   └── [sme-agent]-memory.md      # Domain-specific learnings per SME
│
└── bizops/global-memory/          # Cross-startup learnings (portable)
    ├── co-ceo-global-memory.md    # Strategic patterns across ALL startups
    ├── chief-of-staff-global-memory.md
    └── skill-improvement-log.md
```

**Tier 1 (per-startup)**: Lives in `bizops/memory/`. Tracks decisions, learnings, and anti-patterns specific to this project. Created fresh when you clone the template.

**Tier 2 (global/cross-startup)**: Lives in `bizops/global-memory/`. Portable files that travel between startups. When you start Startup #3, you copy the latest global memory from your previous startup. The Co-CEO reads both tiers at session start — "here's what I learned about THIS startup" + "here's what I've learned about startups in general."

**Read-Execute-Write Protocol** (every agent, every session):

```
┌─────────────────────────────────────────────┐
│  1. READ                                    │
│     → Own memory.md from bizops/memory/     │
│     → Global memory from bizops/global-     │
│       memory/ (cross-startup learnings)     │
│     → STARTUP.md (current state + config)   │
│     → Relevant bizops/context/ files        │
│     → Last session's critique scores        │
│                                             │
│  2. EXECUTE                                 │
│     → Perform assigned tasks                │
│     → Apply learnings from memory           │
│     → Avoid past mistakes (anti-patterns)   │
│                                             │
│  3. WRITE-BACK                              │
│     → Update own memory.md with:            │
│       - Decisions made + rationale          │
│       - Surprises / unexpected findings     │
│       - Quality scores from critique        │
│       - Anti-patterns to avoid next time    │
│       - Process improvements discovered     │
│     → Update STARTUP.md with phase outputs  │
│     → Flag context file updates if needed   │
│     → Flag global memory updates if the     │
│       learning applies cross-startup        │
└─────────────────────────────────────────────┘
```

**Memory entry format** (all agents use this):

```markdown
## [YYYY-MM-DD] Session: [brief description]

### Decisions

- [Decision] — [rationale] — [confidence: high/med/low]

### Learnings

- [What happened] → [What it means] → [What to do differently]

### Quality Scores

- Deliverable: [name] — Score: [X/Y] — Pass rate: [%]
- Failed assertions: [list specific failures]

### Anti-Patterns Discovered

- [Pattern to avoid] — [Why it fails] — [What to do instead]

### Process Improvements

- [Current process step] → [Proposed improvement] — [Evidence]
```

---

### System 2: The Immune System (Critique Loops + Binary Assertions)

**The core problem v1.0 didn't solve**: An agent produces a deliverable → posts to founder → founder discovers it's 70% quality → sends back for revision → wasted cycle.

**v2.0 solution**: Every deliverable runs through a Critique Loop before it reaches a gate. A separate critique prompt (not the same agent that produced the work) scores the deliverable against Binary Assertions — objective, measurable, true/false checks. Only deliverables that pass the assertion threshold advance to the gate.

#### The Three-File Architecture (per deliverable)

Adapted from the Karpathy auto-research pattern. Every significant deliverable has three files:

```
bizops/phase-X/
├── program.md       # What the agent was told to produce (the task spec)
├── [deliverable]    # The actual output (competitor-matrix.md, prd.md, etc.)
└── eval.json        # Binary assertions + scores for quality verification
```

**program.md** = The executive directive. What to produce, constraints, acceptance criteria.
**deliverable** = The output. The thing being critiqued.
**eval.json** = The ground truth. Binary assertions that can be machine-evaluated.

#### Binary Assertion Framework

Every deliverable type has a standard set of binary assertions. These are TRUE/FALSE checks — no subjective "is it good?" evaluation.

**Example: Competitor Matrix (Phase 1)**

```json
{
  "deliverable": "competitor-matrix.md",
  "assertions": [
    { "id": "CM-01", "check": "Contains at least 5 direct competitors", "type": "structural" },
    {
      "id": "CM-02",
      "check": "Each competitor has pricing data with specific numbers, not ranges",
      "type": "completeness"
    },
    {
      "id": "CM-03",
      "check": "Each competitor has at least 3 cited weaknesses from real user reviews",
      "type": "evidence"
    },
    {
      "id": "CM-04",
      "check": "Matrix includes a clear 'our advantage' column with differentiation",
      "type": "strategic"
    },
    {
      "id": "CM-05",
      "check": "All data points have source URLs or citations from the last 12 months",
      "type": "recency"
    },
    {
      "id": "CM-06",
      "check": "Contains at least 1 indirect competitor or substitute category",
      "type": "completeness"
    },
    {
      "id": "CM-07",
      "check": "Feature comparison uses binary (has/doesn't have) not subjective ratings",
      "type": "objectivity"
    },
    {
      "id": "CM-08",
      "check": "Includes market share or funding data where publicly available",
      "type": "completeness"
    }
  ],
  "pass_threshold": 0.75,
  "meta_assertion": "Would a first-time reader understand the competitive landscape well enough to make a go/no-go decision?",
  "run_count": 1,
  "history": []
}
```

**Example: PRD (Phase 3)**

```json
{
  "deliverable": "prd.md",
  "assertions": [
    {
      "id": "PRD-01",
      "check": "Contains user stories in 'As a [user], I want [action], so that [benefit]' format",
      "type": "structural"
    },
    {
      "id": "PRD-02",
      "check": "Each user story has measurable acceptance criteria",
      "type": "completeness"
    },
    {
      "id": "PRD-03",
      "check": "MVP scope is explicitly defined with 'in scope' and 'out of scope' sections",
      "type": "scope"
    },
    { "id": "PRD-04", "check": "Total MVP user stories number 15 or fewer", "type": "scope" },
    {
      "id": "PRD-05",
      "check": "Contains a data model or entity list with relationships",
      "type": "technical"
    },
    {
      "id": "PRD-06",
      "check": "Non-functional requirements (performance, security, scalability) are stated",
      "type": "completeness"
    },
    {
      "id": "PRD-07",
      "check": "Success metrics are defined with specific numbers (not 'improve retention')",
      "type": "measurability"
    },
    {
      "id": "PRD-08",
      "check": "Each feature maps to a validated customer need from Phase 1",
      "type": "traceability"
    },
    {
      "id": "PRD-09",
      "check": "No feature exists that wasn't validated in customer discovery",
      "type": "discipline"
    },
    {
      "id": "PRD-10",
      "check": "Contains a prioritized backlog beyond MVP (what comes next)",
      "type": "strategic"
    }
  ],
  "pass_threshold": 0.8,
  "meta_assertion": "Could an engineering team build an MVP from this PRD without asking clarifying questions?",
  "history": []
}
```

#### The Critique Loop Protocol

```
┌──────────────────────────────────────────────────────────┐
│                    CRITIQUE LOOP                         │
│                                                          │
│  1. PRODUCE                                              │
│     Agent creates deliverable using its skill + memory   │
│                                                          │
│  2. SELF-REVIEW (same agent, different prompt)           │
│     "Review your own output against these assertions.    │
│      Score each TRUE or FALSE. Be ruthlessly honest."    │
│     → Produces initial score                             │
│                                                          │
│  3. PEER-REVIEW (different agent or fresh context)       │
│     "You are a critic. Score this deliverable against    │
│      these assertions. You did NOT produce this work.    │
│      Find every flaw."                                   │
│     → Produces independent score                         │
│                                                          │
│  4. RECONCILE                                            │
│     If self-review and peer-review disagree on any       │
│     assertion, the FAILING score wins (conservative).    │
│     → Produces final score                               │
│                                                          │
│  5. GATE CHECK                                           │
│     If final score >= pass_threshold:                    │
│       → PASS: Advance to founder gate                    │
│     If final score < pass_threshold:                     │
│       → REVISE: Agent gets failure list, rewrites,       │
│         re-enters critique loop (max 3 iterations)       │
│     If 3 iterations and still failing:                   │
│       → ESCALATE: Post to Slack [name]-gates with        │
│         failure report, ask founder for guidance          │
│                                                          │
│  6. LOG                                                  │
│     Write scores + failures to eval.json history         │
│     Write learnings to agent's memory.md                 │
│     Update STARTUP.md with quality metadata              │
└──────────────────────────────────────────────────────────┘
```

**Implementation in Cowork** (task prompt for critique):

```
You are a deliverable critic. You did NOT produce the work below.

## Your Task
Score the following deliverable against each binary assertion.
For each assertion, answer ONLY "TRUE" or "FALSE" with a one-line justification.
Then answer the meta-assertion with a YES or NO.

## Deliverable
[contents of the deliverable file]

## Assertions
[contents of eval.json assertions array]

## Meta-Assertion
[contents of eval.json meta_assertion]

## Output Format
| ID | Result | Justification |
|----|--------|--------------|
| XX-01 | TRUE/FALSE | [one line] |

Meta: YES/NO — [one line justification]

Final Score: [passed]/[total] = [percentage]%
Pass Threshold: [threshold from eval.json]
Verdict: PASS / REVISE / ESCALATE
```

**Implementation in Claude Code** (headless sniper script for engineering critiques):

```bash
#!/bin/bash
# scripts/critique.sh — Headless critique loop for code deliverables
# Uses claude -p (headless mode) for speed and cost efficiency

DELIVERABLE=$1
EVAL_FILE=$2

claude -p \
  --system-prompt "You are a code reviewer. Score against assertions only. No praise. No hedging." \
  "Review this deliverable against these assertions:

   DELIVERABLE: $(cat $DELIVERABLE)

   ASSERTIONS: $(cat $EVAL_FILE)

   Output: JSON with {assertion_id, result: true/false, justification} for each."
```

---

### System 3: The Evolution System (Self-Improving Skill Loops)

Adapted from the Karpathy "Auto Research" pattern. Agents don't just execute — they improve their own skills over time through autonomous optimization cycles.

#### When Self-Improvement Runs

- **After every critique loop**: If assertions consistently fail, the agent's skill instructions may need refinement
- **Weekly scheduled maintenance**: Cowork scheduled task runs optimization cycles on underperforming skills
- **Overnight cycles**: Claude Code runs `claude -p` headless loops to optimize engineering skills

#### The Self-Improvement Loop

```
┌──────────────────────────────────────────────────────┐
│              SKILL IMPROVEMENT LOOP                   │
│                                                       │
│  Input: A skill that's scoring below target           │
│                                                       │
│  1. ANALYZE FAILURES                                  │
│     Read the eval.json history for this skill          │
│     Identify which assertions fail most often          │
│     Look for patterns in failure justifications        │
│                                                       │
│  2. HYPOTHESIZE                                       │
│     "Assertion CM-03 fails 60% of the time because    │
│      the skill instructions don't specify to cite      │
│      user reviews specifically."                      │
│                                                       │
│  3. MUTATE                                            │
│     Make ONE specific change to the skill.md           │
│     (Single variable experiment — never change         │
│      multiple things at once)                          │
│                                                       │
│  4. TEST                                              │
│     Re-run the skill against the eval suite            │
│     Run 3x minimum (distribution testing — LLMs       │
│     are non-deterministic, 1 run means nothing)        │
│                                                       │
│  5. SCORE                                             │
│     Compare median score across 3 runs vs baseline     │
│     If improved: git commit the skill change           │
│     If regressed: git reset to last stable version     │
│     If neutral: revert and try different mutation      │
│                                                       │
│  6. LOG                                               │
│     Write to bizops/global-memory/                     │
│     skill-improvement-log.md:                          │
│     - What was changed                                │
│     - Why (hypothesis)                                │
│     - Result (improved/regressed/neutral)              │
│     - New baseline score                              │
│                                                       │
│  7. REPEAT until target score reached or               │
│     max iterations (10) exhausted                      │
└──────────────────────────────────────────────────────┘
```

#### Skill Improvement Log Format

```markdown
# Skill Improvement Log: [skill-name]

## Baseline

- Initial pass rate: [X%]
- Target pass rate: [Y%]
- Current pass rate: [Z%]

## Iteration History

### Iteration 1 — [date]

- **Hypothesis**: [What we think is causing failures]
- **Mutation**: [Exact change made to SKILL.md]
- **Test results**: Run 1: [X%], Run 2: [Y%], Run 3: [Z%], Median: [M%]
- **Baseline delta**: [+/-N%]
- **Action**: committed / reverted
- **New baseline**: [score if committed]

### Iteration 2 — [date]

...
```

#### The Meta-Assertion Guard

To prevent "teaching to the test" (the agent optimizes for assertion pass rates but produces useless output), every eval.json includes a **meta-assertion** — a high-level check that the output actually serves its purpose. The meta-assertion is evaluated by a separate prompt that does NOT see the individual assertions, only the deliverable and its stated purpose.

```
You are evaluating whether this deliverable achieves its stated goal.
You do NOT know what specific structural checks were run.
You are ONLY assessing: does this deliverable do what it's supposed to do?

Goal: [meta_assertion from eval.json]
Deliverable: [contents]

Answer: YES or NO, with a 2-sentence justification.
```

If the meta-assertion fails but individual assertions pass, this signals **overfitting** — the agent needs its assertions redesigned, not its skill.

---

## Tool Roles

| Tool                         | Role                                                     | Points At                 | v2.0 Addition                                                                                      |
| ---------------------------- | -------------------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| **Cowork**                   | Co-CEO's brain. Business work, critique loops, strategy. | `[repo]/bizops/`          | Runs critique loops on all business deliverables. Maintains agent memories in `bizops/memory/`.    |
| **Claude Code**              | Engineering workforce + headless sniper agents.          | `[repo]/` (monorepo root) | Runs headless critique scripts (`claude -p`). Overnight skill improvement loops. Full repo access. |
| **Slack** (`[name]-gates`)   | Gate decisions + escalations. Per startup.               | —                         | Quality scores with every gate post. Escalations include failure reports.                          |
| **Slack** (`[name]-build`)   | Daily build summaries. Per startup.                      | —                         | Sprint-level assertion scores included.                                                            |
| **Slack** (`[name]-quality`) | Quality monitoring. Per startup.                         | —                         | Critique scores, skill improvement results, assertion failures.                                    |
| **Dispatch** (mobile)        | Founder's remote control for Cowork.                     | —                         | Can view critique scores and quality trends.                                                       |
| **Remote Control** (mobile)  | Founder's remote control for Claude Code.                | —                         | Can monitor overnight improvement loops.                                                           |
| **Claude.ai Chat**           | The boardroom. Strategic conversations only.             | —                         | Where founder and Co-CEO review quality trends and refine assertions.                              |

---

## Shared State: STARTUP.md

Lives at the monorepo root alongside `CLAUDE.md` and `AGENTS.md`. Both Cowork and Claude Code read/write it. This is the single source of truth.

```markdown
# [Startup Name]

## Config

- Repo: [git URL]
- Cowork path: bizops/
- Claude Code path: . (monorepo root)

## Slack Channels

- gates: [name]-gates
- build: [name]-build
- quality: [name]-quality

## Current State

- Phase: [0-6]
- Gate: [pending/approved/blocked]
- Status: [active/paused/killed]
- Last Updated: [timestamp]
- System Health: [green/yellow/red] — based on aggregate quality scores

## Quality Dashboard

- Phase 0 deliverables: [X/Y passed] — avg score [Z%]
- Phase 1 deliverables: [X/Y passed] — avg score [Z%]
- Skills below target: [list skills with pass rate < 75%]
- Improvement loops running: [list]
- Last overnight cycle: [date] — [results summary]

## Decisions Log

- [date]: [decision] — [rationale] — [quality score of supporting deliverable] — [approved by]

## Open Questions

- [question] — [assigned to] — [deadline]

## Phase Outputs

### Phase 0: Ideation

- Shortlist: [link] — critique score: [X%]
- Selected idea: [name]
- Gate 1 status: [pending/approved]
- Gate 1 quality: [aggregate assertion score]

### Phase 1: Validation

- Research report: [link] — critique score: [X%]
- Competitor matrix: [link] — critique score: [X%]
- Kill criteria assessment: [link] — critique score: [X%]
- Tech feasibility: [link] — critique score: [X%]
- Gate 2 status: [pending/approved]
- Gate 2 quality: [aggregate assertion score]

[...continues for each phase]
```

---

## The Pipeline

### Phase 0: Ideation

**Who runs it**: Co-CEO in Cowork (pointing at `bizops/`)
**Founder involvement**: Seed input only
**Quality layer**: Critique loop on idea briefs + recommendation before gate

**What the Co-CEO does autonomously**:

1. **READ**: Load `bizops/memory/co-ceo-memory.md` + `bizops/global-memory/co-ceo-global-memory.md` for cross-project learnings
2. Takes founder's rough ideas or domain interest
3. Runs market research via web search
4. Generates 5-10 idea variations with founder-fit scoring
5. Ranks by: market size, founder-fit, defensibility, time-to-revenue, AI-native advantage
6. Shortlists top 3-5 with one-page briefs
7. Writes recommendation with reasoning for #1 pick
8. **CRITIQUE LOOP**: Runs idea briefs through assertions (see below)
9. If critique passes: Posts gate summary to Slack `[name]-gates` WITH quality scores
10. **WRITE-BACK**: Updates `bizops/memory/co-ceo-memory.md` with research learnings; flags global memory updates if cross-startup learnings emerged

**Phase 0 Assertions** (eval-phase-0.json):

```json
{
  "deliverable": "idea-briefs.md",
  "assertions": [
    {
      "id": "ID-01",
      "check": "Each idea has a clearly stated problem affecting a specific, named customer segment",
      "type": "clarity"
    },
    {
      "id": "ID-02",
      "check": "Each idea has a revenue model with pricing range and payment trigger",
      "type": "business"
    },
    {
      "id": "ID-03",
      "check": "Market size estimates cite specific data sources (reports, databases, public filings)",
      "type": "evidence"
    },
    {
      "id": "ID-04",
      "check": "Founder-fit scoring references specific founder skills/experience, not generic traits",
      "type": "specificity"
    },
    {
      "id": "ID-05",
      "check": "At least one idea leverages AI as a core differentiator, not just a feature",
      "type": "strategic"
    },
    {
      "id": "ID-06",
      "check": "Each idea identifies at least 2 existing alternatives and explains why they're insufficient",
      "type": "competitive"
    },
    {
      "id": "ID-07",
      "check": "Time-to-revenue estimate includes specific assumptions (team size, stack, integrations needed)",
      "type": "feasibility"
    },
    {
      "id": "ID-08",
      "check": "Recommendation includes explicit reasoning for why rejected ideas were ranked lower",
      "type": "rigor"
    }
  ],
  "pass_threshold": 0.75,
  "meta_assertion": "Could a seed-stage investor read this and understand why this opportunity is worth pursuing?",
  "history": []
}
```

**Enhanced Gate 1 Post** (to `[name]-gates`):

```
🚪 GATE 1 READY: [ProjectName] ideation complete.

Top pick: [name] — [one-line summary]

📊 Quality Report:
- Idea briefs: 7/8 assertions passed (87.5%) ✅
- Failed: ID-04 (founder-fit scoring too generic — noted in memory for next time)
- Meta-assertion: PASS
- Critique iterations: 2 (first pass scored 5/8, revised and passed)

Full briefs: bizops/phase-0/
Quality details: bizops/phase-0/eval-phase-0.json

Reply: ✅ approve [idea name] | 🔄 redirect [notes] | ❌ kill
```

---

### Phase 1: Validation

**Who runs it**: Co-CEO in Cowork (`bizops/`) + Claude Code (monorepo root) for tech feasibility
**Founder involvement**: Gate approval only
**Quality layer**: Critique loops on competitor matrix, market sizing, validation report, tech feasibility — each independently scored

**What the Co-CEO does autonomously**:

1. **READ**: Load `bizops/memory/co-ceo-memory.md` + `bizops/memory/validation-memory.md` + `bizops/global-memory/co-ceo-global-memory.md`
2. Runs startup-validation skill Phases 1-4
3. Builds competitor matrix → **CRITIQUE LOOP** (eval-competitor-matrix.json)
4. Runs TAM/SAM/SOM analysis → **CRITIQUE LOOP** (eval-market-sizing.json)
5. Identifies and tests riskiest assumptions
6. Creates customer discovery plan
7. Runs kill-criteria checklist
8. Produces validation report → **CRITIQUE LOOP** (eval-validation-report.json)
9. **CROSS-CHECK**: Validation report assertions tested against competitor matrix
10. Posts gate summary with all quality scores to `[name]-gates`

**Claude Code (parallel):**

1. **READ**: Load `bizops/memory/engineering-memory.md`
2. Assesses technical feasibility (can this be built with our monorepo stack?)
3. **CRITIQUE LOOP** on tech-feasibility.md (eval-tech-feasibility.json)
4. Saves assessment to `bizops/phase-1/tech-feasibility.md`
5. **WRITE-BACK**: Update `bizops/memory/engineering-memory.md` with stack learnings, API risk patterns

**Phase 1 Cross-Check Protocol** (the immune system's "second opinion"):

After all Phase 1 deliverables are individually critiqued, a synthesis check runs:

```
You are a startup due-diligence analyst. You have FOUR deliverables from a validation phase.
Your job is to find CONTRADICTIONS between them.

1. Competitor Matrix: [contents from bizops/phase-1/competitor-matrix.md]
2. Market Sizing: [contents from bizops/phase-1/market-sizing.md]
3. Tech Feasibility: [contents from bizops/phase-1/tech-feasibility.md]
4. Validation Report: [contents from bizops/phase-1/validation-report.md]

Find any contradictions, unsupported claims, or logical gaps BETWEEN these documents.
Examples of what you're looking for:
- Market sizing claims $X TAM but competitor matrix shows only 3 players generating $Y total
- Validation report claims differentiation on feature Z but competitor matrix shows 2 competitors already have it
- Tech feasibility says 4 sprint MVP but PRD-like scope in validation report implies 8+ sprints
- Kill criteria threshold not actually tested against findings

Output: List each contradiction with document references and severity (critical/warning/minor).
If no contradictions found, explicitly state the analysis is internally consistent.
```

**Gate 2 now includes**: Individual deliverable scores + cross-check results.

---

### Phase 2: Context Capture + Agent Hiring

**Who runs it**: Co-CEO in Cowork (`bizops/`) + Claude Code (monorepo root) for agent skill creation
**Founder involvement**: Answer interview questions (~30 min async via `[name]-gates` Slack)
**Quality layer**: Context completeness assertions + skill activation testing

**Enhanced process**:

1. Co-CEO runs context-engineering interview (sends questions to `[name]-gates`, founder answers async)
2. Builds `bizops/context/` folder
3. **CRITIQUE LOOP on context**: Assertions check completeness, internal consistency, and actionability
4. Identifies domain SME agents needed
5. Writes SKILL.md for each SME into `.claude/skills/`
6. **SKILL ACTIVATION TEST**: Each new skill is tested against 3 sample prompts to verify it triggers correctly and produces useful output
7. Creates Team Manifest, updates `AGENTS.md` with new domain SME agents
8. **WRITE-BACK**: Updates `bizops/memory/` with domain calibration learnings

**Context Quality Assertions** (eval-context.json):

```json
{
  "deliverable": "context/",
  "assertions": [
    {
      "id": "CTX-01",
      "check": "about-founder.md contains specific technical skills, not just 'experienced developer'",
      "type": "specificity"
    },
    {
      "id": "CTX-02",
      "check": "ideal-customer.md names a specific job title, company size, and pain point",
      "type": "specificity"
    },
    {
      "id": "CTX-03",
      "check": "brand-voice.md includes at least 3 'do' examples and 3 'don't' examples",
      "type": "actionability"
    },
    {
      "id": "CTX-04",
      "check": "product-info.md references validated needs from Phase 1, not assumptions",
      "type": "traceability"
    },
    {
      "id": "CTX-05",
      "check": "No context file contradicts another context file",
      "type": "consistency"
    },
    {
      "id": "CTX-06",
      "check": "Every context file is usable by an agent that has NEVER seen the startup before",
      "type": "standalone"
    }
  ],
  "pass_threshold": 0.83,
  "meta_assertion": "Could a new agent read only the context/ folder and produce on-brand, on-target work for this startup?"
}
```

**Skill Activation Test Protocol**:

For each new SKILL.md created, run this test in Claude Code before deploying:

```bash
# Test 1: Does the skill trigger on relevant prompts?
echo "Should trigger:"
claude -p --append-system-prompt "$(cat .claude/skills/[skill]/SKILL.md)" "Help me with [domain-specific task]"

# Test 2: Does the skill NOT trigger on irrelevant prompts?
echo "Should NOT trigger:"
claude -p --append-system-prompt "$(cat .claude/skills/[skill]/SKILL.md)" "Help me write a grocery list"

# Test 3: Does the skill produce useful output?
echo "Quality check:"
claude -p --append-system-prompt "$(cat .claude/skills/[skill]/SKILL.md)" "[realistic task prompt]" | \
  claude -p --system-prompt "Rate this output 1-5 on usefulness. Only output the number."
```

---

### Phase 3: Spec + Design + GTM Plan

**Who runs it**: Co-CEO in Cowork (`bizops/`) + Claude Code (monorepo root)
**Founder involvement**: Gate approval only
**Quality layer**: Heavy critique — this is the highest-stakes phase before code starts

**Cowork deliverables** (saved to `bizops/phase-3/`) with critique loops:

1. PRD → **CRITIQUE LOOP** (eval-prd.json — 10 assertions, 80% threshold)
2. GTM Plan → **CRITIQUE LOOP** (eval-gtm.json)
3. Landing page copy → **CRITIQUE LOOP** (eval-copy.json)

**Claude Code deliverables** (saved to `docs/`) with critique loops:

1. Architecture design → **CRITIQUE LOOP** (docs/eval-architecture.json)
2. ADRs → **CRITIQUE LOOP** (docs/decisions/)
3. Database schema → **CRITIQUE LOOP** (docs/eval-schema.json)

**Phase 3 Cross-Check Protocol** (critical — most expensive to fix if wrong):

```
You are a startup CTO reviewing a spec package before engineering begins.
You have: PRD (bizops/phase-3/prd.md), GTM Plan (bizops/phase-3/gtm-plan.md),
System Architecture (docs/architecture.md), Database Schema, ADRs (docs/decisions/).

Find any contradictions, scope mismatches, or missing pieces BETWEEN these documents:
- Does the architecture support every user story in the PRD?
- Does the database schema cover every entity implied by the PRD?
- Does the GTM plan's launch timeline match the engineering effort estimate?
- Do the ADRs justify their choices against alternatives?
- Is there a feature in the GTM messaging that isn't in the PRD?
- Is there a PRD feature that has no architecture component?

Output: Issue list with severity and affected documents.
```

**Gate 4 now includes**: Individual scores + cross-check + aggregate "readiness to build" score. Posted to `[name]-gates`.

---

### Phase 4: Build MVP

**Who runs it**: Claude Code (monorepo root — `apps/`, `packages/`) + Cowork (`bizops/`) for launch prep
**Founder involvement**: Monitor `[name]-build` daily
**Quality layer**: Per-sprint critique loops + continuous assertion testing

**Enhanced engineering process**:

1. Claude Code decomposes PRD into sprint tasks
2. Each sprint has its own eval criteria derived from PRD acceptance criteria
3. Agent teams build features in `apps/api/`, `apps/web/`, `apps/mobile/` with TDD
4. **Per-sprint critique loop**:
   - Code review assertions (security-auditor skill patterns)
   - Feature completeness assertions (derived from PRD user stories)
   - Integration test results (from `apps/e2e/`)
5. Daily build summaries posted to `[name]-build` include quality scores
6. **WRITE-BACK**: `bizops/memory/engineering-memory.md` updated with patterns, debt decisions, what worked

**Engineering Critique Assertions** (run per sprint):

```json
{
  "assertions": [
    {
      "id": "ENG-01",
      "check": "All new endpoints have corresponding test coverage",
      "type": "quality"
    },
    {
      "id": "ENG-02",
      "check": "No hardcoded secrets, API keys, or credentials in codebase",
      "type": "security"
    },
    {
      "id": "ENG-03",
      "check": "All user-facing strings are parameterized (i18n-ready)",
      "type": "maintainability"
    },
    { "id": "ENG-04", "check": "Database migrations are reversible", "type": "safety" },
    {
      "id": "ENG-05",
      "check": "API responses match the schema defined in docs/api-spec.md",
      "type": "contract"
    },
    { "id": "ENG-06", "check": "No N+1 query patterns in new ORM code", "type": "performance" },
    {
      "id": "ENG-07",
      "check": "Error handling returns user-friendly messages, not stack traces",
      "type": "ux"
    },
    {
      "id": "ENG-08",
      "check": "Sprint tasks map 1:1 to PRD user stories (no scope creep)",
      "type": "discipline"
    }
  ],
  "pass_threshold": 0.875
}
```

**Parallel Cowork launch prep** (saved to `bizops/marketing/`) gets its own critique:

- Landing page copy assertions (messaging clarity, CTA presence, ICP alignment)
- Content calendar assertions (cadence consistency, channel coverage)
- Analytics plan assertions (every KPI from GTM plan has a tracking event)

---

### Phase 5: Deploy + Launch

**Who runs it**: Claude Code (monorepo root) + Cowork (`bizops/`)
**Founder involvement**: Push the button
**Quality layer**: Deployment checklist assertions + launch readiness score

**Deployment Assertions** (docs/eval-deploy.json):

```json
{
  "assertions": [
    { "id": "DEP-01", "check": "SSL certificates are configured and verified", "type": "security" },
    {
      "id": "DEP-02",
      "check": "Environment variables are set from secrets manager, not hardcoded",
      "type": "security"
    },
    {
      "id": "DEP-03",
      "check": "Database backups are configured and tested with a restore",
      "type": "safety"
    },
    {
      "id": "DEP-04",
      "check": "Monitoring and alerting is active (uptime, error rate, latency)",
      "type": "ops"
    },
    {
      "id": "DEP-05",
      "check": "Staging environment matches production configuration",
      "type": "parity"
    },
    {
      "id": "DEP-06",
      "check": "Smoke tests pass on staging with real-world data patterns",
      "type": "readiness"
    },
    { "id": "DEP-07", "check": "Rollback procedure documented and tested", "type": "safety" },
    { "id": "DEP-08", "check": "Rate limiting and DDoS protection configured", "type": "security" }
  ],
  "pass_threshold": 1.0,
  "meta_assertion": "Is this deployment safe to put in front of paying customers?"
}
```

Note: Deployment has a **100% pass threshold**. No exceptions. If any assertion fails, deployment is blocked.

**Gate 6**: Posted to `[name]-gates`. Founder pushes the button. Co-CEO executes launch playbook.

---

### Phase 6: Operate + Iterate (Enhanced with Overnight Loops)

**Who runs it**: Both tools on scheduled cadences + overnight improvement cycles
**Founder involvement**: Weekly 15-min review + monthly quality review

**Cowork scheduled tasks (same as v1.0 plus)**:

- Daily: Slack briefing to `[name]-build`, basic metrics check
- Weekly: KPI report to `[name]-gates`, competitor scan, content publishing
- Weekly: Run skill improvement loops on any skill with < 75% pass rate
- Bi-weekly: Investor update draft (if fundraising)
- Monthly: Full assertion suite review — add/remove/modify assertions based on learnings
- Monthly: Cross-startup memory synthesis — update `bizops/global-memory/` files

**Claude Code scheduled tasks (same as v1.0 plus)**:

- Nightly: Headless skill improvement loops on engineering skills (`claude -p` in loop mode)
- Weekly: Assertion coverage analysis — are there deliverable types without assertions?
- Per-sprint: Feature development from prioritized backlog
- Per-sprint: Memory consolidation — archive old entries, surface patterns

**The Overnight Improvement Cycle** (Claude Code):

```bash
#!/bin/bash
# scripts/overnight-improve.sh
# Runs skill improvement loops on underperforming skills
# Scheduled via cron: 0 2 * * * (2 AM daily)
# Run from monorepo root

REPO_ROOT=$(git rev-parse --show-toplevel)
SKILLS_DIR="$REPO_ROOT/.claude/skills"
STARTUP_MD="$REPO_ROOT/STARTUP.md"
GLOBAL_LOG="$REPO_ROOT/bizops/global-memory/skill-improvement-log.md"
THRESHOLD=75

# Read quality channel from STARTUP.md
QUALITY_CHANNEL=$(grep 'quality:' $STARTUP_MD | awk '{print $2}')

for skill_dir in $SKILLS_DIR/*/; do
  skill_name=$(basename $skill_dir)
  eval_file="$skill_dir/eval.json"

  if [ -f "$eval_file" ]; then
    pass_rate=$(jq '.history[-1].pass_rate // 0' $eval_file)

    if (( $(echo "$pass_rate < $THRESHOLD" | bc -l) )); then
      echo "[$skill_name] Below threshold ($pass_rate% < $THRESHOLD%). Starting improvement loop..."

      # Run improvement loop (max 5 iterations)
      for i in {1..5}; do
        # Snapshot current state
        git stash

        # Mutate skill
        claude -p \
          --system-prompt "You are a skill optimizer. Make ONE specific improvement to this skill based on its failure patterns." \
          "Skill: $(cat $skill_dir/SKILL.md)
           Recent failures: $(jq '.history[-1].failures' $eval_file)
           Make exactly ONE change. Output the full updated SKILL.md."  \
          > /tmp/improved_skill.md

        cp /tmp/improved_skill.md $skill_dir/SKILL.md

        # Test 3x (distribution testing)
        total=0
        for run in {1..3}; do
          score=$(claude -p \
            --system-prompt "$(cat $skill_dir/SKILL.md)" \
            "$(jq -r '.test_prompt' $eval_file)" | \
            claude -p --tools '[]' \
            --system-prompt "Score this output against these assertions. Return only a number (passed count)." \
            "Output: $(cat /dev/stdin) Assertions: $(jq '.assertions' $eval_file)")
          total=$((total + score))
        done
        median_score=$((total / 3))

        # Compare to baseline
        baseline=$(jq '.history[-1].score // 0' $eval_file)
        if [ $median_score -gt $baseline ]; then
          git add $skill_dir/SKILL.md
          git commit -m "skill-improve: $skill_name iteration $i — $baseline% → $median_score%"
          echo "  Iteration $i: Improved $baseline% → $median_score%"
        else
          git checkout -- $skill_dir/SKILL.md
          echo "  Iteration $i: Regressed. Reverted."
        fi
      done
    fi
  fi
done

# Log results to global memory
echo "## [$(date +%Y-%m-%d)] Overnight Improvement Cycle" >> $GLOBAL_LOG
echo "Skills checked: $(ls -d $SKILLS_DIR/*/ 2>/dev/null | wc -l)" >> $GLOBAL_LOG
echo "---" >> $GLOBAL_LOG
```

**Founder weekly ritual** (15 min):

1. Check `[name]-gates` for any pending approvals
2. Review weekly KPI report (posted to `[name]-gates` by Cowork)
3. Skim `[name]-build` for sprint progress
4. Glance at `[name]-quality` for system health trends
5. Approve/redirect next sprint priorities
6. Optional: Open Claude.ai Chat for deeper strategic thinking

---

## The Checks and Balances Matrix

| Layer                      | Check                                   | Balance                                                | Failure Mode                                               |
| -------------------------- | --------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------- |
| **Deliverable production** | Binary assertions (eval.json)           | Must pass threshold before advancing                   | Agent revises up to 3x, then escalates to `[name]-gates`   |
| **Self-review**            | Agent scores own work                   | Conservative — ties go to FAIL                         | Prevents obvious errors from reaching critique             |
| **Peer-review**            | Independent critique prompt             | Disagreements default to FAIL                          | Catches self-review blind spots                            |
| **Cross-check**            | Inter-document consistency              | Finds contradictions between deliverables              | Prevents internally inconsistent phase outputs             |
| **Meta-assertion**         | Does the deliverable serve its purpose? | Checked by prompt that can't see individual assertions | Prevents overfitting to structural checks                  |
| **Per-startup memory**     | Anti-patterns from previous sessions    | Agent reads before executing                           | Prevents repeating known mistakes                          |
| **Global memory**          | Cross-startup learnings                 | Co-CEO reads global memory at session start            | Prevents making the same strategic mistake across startups |
| **Skill improvement**      | Automated optimization loops            | Git commit/revert based on scores                      | Skills get better or stay stable, never degrade            |
| **Gate quality scores**    | Founder sees assertion results          | Can't approve a phase with red quality flags           | Founder has objective data, not just vibes                 |
| **Per-startup isolation**  | Separate Slack channels per startup     | No cross-talk between startups                         | Clean signal, clear accountability                         |

---

## Notification Flow

```
Agent produces deliverable
    → Self-review (binary assertions)
    → Peer-review (independent critique)
    → Cross-check (if multi-deliverable phase)

If PASS:
    → Posts to [name]-gates with quality scores
    → Posts to [name]-quality with detailed assertion results
    → Founder reviews gate with objective data

If FAIL (after 3 revision attempts):
    → Posts to [name]-gates as ESCALATION
    → Includes failure report: which assertions, why, what was tried
    → Founder decides: lower threshold, provide guidance, or kill

Daily build updates:
    → Posts to [name]-build
    → Sprint progress + quality scores

Overnight improvement results:
    → Posts to [name]-quality daily summary
    → "3 skills improved overnight: [names] — avg +12% pass rate"

Weekly quality digest:
    → Posts to [name]-quality
    → Aggregate quality trends across all phases and skills
```

---

## Setup Checklist

### One-Time (Portfolio-Level)

- [x] Slack workspace created
- [x] Slack MCP connector configured in both Cowork and Claude Code
- [x] Gmail MCP connector configured in Cowork
- [x] Google Calendar MCP connector configured in Cowork
- [x] `bizops/` folder added to foundation-template with full structure (see monorepo structure above)
- [x] `STARTUP.md` template added to foundation-template root
- [x] All eval template JSONs in `bizops/eval-templates/` reviewed and customized
- [x] All eval template JSONs in `docs/` reviewed and customized
- [ ] Claude Code global `~/.claude/CLAUDE.md` configured with Read-Execute-Write protocol
- [x] Cowork global instructions updated with Co-CEO persona + critique loop protocol
- [ ] Critique prompt templates saved as Cowork task templates
- [ ] CLI tool updated to include `bizops/` folder in clone output
- [ ] All skills installed
- [ ] Dispatch paired between phone and desktop
- [ ] Remote Control configured for Claude Code

### Per-Startup (When Starting a New Project)

- [ ] Clone foundation-template via CLI → `[startup-name]`
- [ ] Update `STARTUP.md` with startup name, Phase: 0, Status: active
- [ ] Create Slack channels: `[name]-gates`, `[name]-build`, `[name]-quality`
- [ ] Update `STARTUP.md` Slack Channels section with channel names
- [ ] Copy latest `bizops/global-memory/` files from previous startup (skip for first)
- [ ] Point Cowork at `[repo]/bizops/`
- [ ] Ensure Claude Code is at monorepo root
- [ ] Tell Co-CEO: "Starting Phase 0 for [idea/domain]. Here's my initial thinking: [seed input]"
- [ ] Walk away. Check `[name]-gates` when Gate 1 posts.

---

## Skill → Phase → Assertion Mapping

| Phase       | Skills Used                                                       | Key Deliverables                      | Assertion File                       | Pass Threshold              |
| ----------- | ----------------------------------------------------------------- | ------------------------------------- | ------------------------------------ | --------------------------- |
| 0: Ideate   | product-strategy, startup-validation                              | bizops/phase-0/idea-briefs.md         | eval-idea-briefs.json                | 75%                         |
| 1: Validate | startup-validation, saas-metrics, growth-marketing                | bizops/phase-1/\*.md                  | eval-\*.json (4 files) + cross-check | 75% per + cross-check clean |
| 2: Context  | context-engineering, co-ceo-orchestration, skill-creator          | bizops/context/\*.md, .claude/skills/ | eval-context.json + activation tests | 83% + all skills activate   |
| 3: Spec     | pm-execution, growth-marketing, django-ninja-extra, nextjs-shadcn | bizops/phase-3/_.md + docs/_.md       | eval-\*.json (6 files) + cross-check | 80% per + cross-check clean |
| 4: Build    | All engineering skills, tdd-testing, security-auditor             | apps/api + apps/web + apps/e2e        | docs/eval-engineering-sprint.json    | 87.5%                       |
| 5: Deploy   | devops-deploy, fullstack-integration                              | Production deployment                 | docs/eval-deploy.json                | 100%                        |
| 6: Operate  | chief-of-staff, saas-metrics, all skills                          | KPI reports, sprint outputs           | Continuous assertion monitoring      | Varies                      |

---

## How to Start a New Startup (v2.0)

```bash
# 1. Clone the foundation-template via your CLI tool
your-cli create acme-saas
cd acme-saas

# 2. Initialize STARTUP.md
# Edit STARTUP.md: set name "Acme SaaS", Phase: 0, Status: active

# 3. Create Slack channels (30 seconds in Slack UI)
# acme-gates, acme-build, acme-quality
# Update STARTUP.md Slack Channels section

# 4. Copy global memory from your portfolio (skip for first startup)
cp /path/to/previous-startup/bizops/global-memory/*.md bizops/global-memory/

# 5. Point your tools
# Cowork → bizops/
# Claude Code → . (monorepo root, already there)

# 6. Go
# Tell Co-CEO: "Starting Phase 0 for [idea]. Here's my thinking: [seed]"

# 7. Walk away
# Check acme-gates when Gate 1 posts — it will include quality scores.
```

**The difference from v1.0**: When Gate 1 posts to `acme-gates`, you don't just see the recommendation. You see that the briefs scored 87.5% on quality assertions, that the critique loop caught two weak spots and the agent fixed them, and that the meta-assertion confirms an investor could read this and understand the opportunity. Your decision is now informed by objective quality data, not just vibes.

**Portability**: Because everything is one monorepo, you can clone it to any machine or VM. Point Cowork at `bizops/`, Claude Code is already at root, set up the Slack channels, and you're running. No environment-specific paths, no symlinks, no shared filesystem dependencies.

---

## Design Principles Summary

1. **Glass box, not black box.** Every decision is traceable. Every critique is logged. Every score is recorded. You can audit any agent's work at any time.

2. **Conservative by default.** When self-review and peer-review disagree, the failing score wins. Deployment requires 100% assertion pass. The system is biased toward catching problems, not shipping fast.

3. **Agents learn, skills evolve.** Memory persists across sessions. Skills improve overnight. The system that runs Startup #3 is sharper than the one that ran Startup #1.

4. **Objective over subjective.** Binary assertions replace "does this feel good?" Every quality check is TRUE/FALSE, measurable, and auditable.

5. **Redundancy is the immune system.** Self-review + peer-review + cross-check + meta-assertion = four layers of quality verification. Expensive? Yes. Cheaper than shipping bad work to customers.

6. **The founder sees scores, not sausage-making.** Gate posts include aggregate quality data. The founder can drill into critique logs if they want, but they don't have to. The system has already done the due diligence.

7. **One monorepo, one startup.** Everything — business ops, engineering code, memory, eval templates, context, agent skills — lives in one git repo cloned from foundation-template. Your CLI tool handles creation. Clone it anywhere, point your tools at it, and go.

8. **Per-startup isolation.** Separate Slack channels, separate memory files, separate eval histories. Startups don't leak into each other. Global learnings are explicitly promoted via `bizops/global-memory/`.
