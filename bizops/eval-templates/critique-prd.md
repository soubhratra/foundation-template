# Critique Task: PRD

> **Deliverable:** `phase-3/prd.md`
> **Eval file:** `eval-templates/eval-prd.json`
> **Phase:** 3 — Spec + GTM
> **Pass threshold:** 80% (8/10 assertions)

## Instructions

You are critiquing the PRD deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-3/prd.md` (the deliverable)
- Read `eval-templates/eval-prd.json` (the assertions)
- Also read `phase-1/validation-report.md` (needed for assertions PRD-08 and PRD-09 — feature traceability)

### Step 2: Score Each Assertion

| ID     | Assertion                                                                         | Result | Justification |
| ------ | --------------------------------------------------------------------------------- | ------ | ------------- |
| PRD-01 | Contains user stories in 'As a [user], I want [action], so that [benefit]' format |        |               |
| PRD-02 | Each user story has measurable acceptance criteria                                |        |               |
| PRD-03 | MVP scope is explicitly defined with 'in scope' and 'out of scope' sections       |        |               |
| PRD-04 | Total MVP user stories number 15 or fewer                                         |        |               |
| PRD-05 | Contains a data model or entity list with relationships                           |        |               |
| PRD-06 | Non-functional requirements (performance, security, scalability) are stated       |        |               |
| PRD-07 | Success metrics are defined with specific numbers (not 'improve retention')       |        |               |
| PRD-08 | Each feature maps to a validated customer need from Phase 1                       |        |               |
| PRD-09 | No feature exists that wasn't validated in customer discovery                     |        |               |
| PRD-10 | Contains a prioritized backlog beyond MVP (what comes next)                       |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Could an engineering team build an MVP from this PRD without asking clarifying questions?"

### Step 4: Calculate Score

- Passed: [count] / 10
- Pass rate: [%]
- Threshold: 80%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-prd.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: PRD — Iteration [N]

**Score:** [X]/10 ([Y]%) — [PASS/FAIL]
**Meta-assertion:** [YES/NO]
**Threshold:** 80%

### Assertion Results
[table from Step 2]

### Failed Assertions (revision targets)
- [ID]: [what specifically needs to change]

### Learnings
- [what this critique revealed about the deliverable quality]
```
