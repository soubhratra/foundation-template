# Critique Task: Competitor Matrix

> **Deliverable:** `phase-1/competitor-matrix.md`
> **Eval file:** `eval-templates/eval-competitor-matrix.json`
> **Phase:** 1 — Validation
> **Pass threshold:** 75% (6/8 assertions)

## Instructions

You are critiquing the competitor matrix deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-1/competitor-matrix.md` (the deliverable)
- Read `eval-templates/eval-competitor-matrix.json` (the assertions)

### Step 2: Score Each Assertion

| ID    | Assertion                                                                | Result | Justification |
| ----- | ------------------------------------------------------------------------ | ------ | ------------- |
| CM-01 | Contains at least 5 direct competitors                                   |        |               |
| CM-02 | Each competitor has pricing data with specific numbers, not ranges       |        |               |
| CM-03 | Each competitor has at least 3 cited weaknesses from real user reviews   |        |               |
| CM-04 | Matrix includes a clear 'our advantage' column with differentiation      |        |               |
| CM-05 | All data points have source URLs or citations from the last 12 months    |        |               |
| CM-06 | Contains at least 1 indirect competitor or substitute category           |        |               |
| CM-07 | Feature comparison uses binary (has/doesn't have) not subjective ratings |        |               |
| CM-08 | Includes market share or funding data where publicly available           |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Would a first-time reader understand the competitive landscape well enough to make a go/no-go decision?"

### Step 4: Calculate Score

- Passed: [count] / 8
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-competitor-matrix.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Competitor Matrix — Iteration [N]

**Score:** [X]/8 ([Y]%) — [PASS/FAIL]
**Meta-assertion:** [YES/NO]
**Threshold:** 75%

### Assertion Results
[table from Step 2]

### Failed Assertions (revision targets)
- [ID]: [what specifically needs to change]

### Learnings
- [what this critique revealed about the deliverable quality]
```
