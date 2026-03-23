# Critique Task: Tech Feasibility

> **Deliverable:** `phase-1/tech-feasibility.md`
> **Eval file:** `eval-templates/eval-tech-feasibility.json`
> **Phase:** 1 — Validation
> **Pass threshold:** 75% (5/6 assertions)

## Instructions

You are critiquing the technical feasibility deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-1/tech-feasibility.md` (the deliverable)
- Read `eval-templates/eval-tech-feasibility.json` (the assertions)

### Step 2: Score Each Assertion

| ID    | Assertion                                                                                                      | Result | Justification |
| ----- | -------------------------------------------------------------------------------------------------------------- | ------ | ------------- |
| TF-01 | Explicitly confirms or denies buildability with the stated stack (Next.js, Django Ninja Extra, Postgres, Expo) |        |               |
| TF-02 | Lists the top 3 hardest technical challenges with severity assessment                                          |        |               |
| TF-03 | MVP effort estimate is in sprints with stated sprint length and team assumptions                               |        |               |
| TF-04 | Third-party dependencies are listed with risk level (API stability, pricing, alternatives)                     |        |               |
| TF-05 | Identifies any features that would require technology outside the standard stack                               |        |               |
| TF-06 | Scope estimate is consistent with the validation report's feature description                                  |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Could an engineering lead read this and start sprint planning without further research?"

### Step 4: Calculate Score

- Passed: [count] / 6
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-tech-feasibility.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Tech Feasibility — Iteration [N]

**Score:** [X]/6 ([Y]%) — [PASS/FAIL]
**Meta-assertion:** [YES/NO]
**Threshold:** 75%

### Assertion Results
[table from Step 2]

### Failed Assertions (revision targets)
- [ID]: [what specifically needs to change]

### Learnings
- [what this critique revealed about the deliverable quality]
```
