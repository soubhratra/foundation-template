# Critique Task: Market Sizing

> **Deliverable:** `phase-1/market-sizing.md`
> **Eval file:** `eval-templates/eval-market-sizing.json`
> **Phase:** 1 — Validation
> **Pass threshold:** 75% (6/7 assertions)

## Instructions

You are critiquing the market sizing deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-1/market-sizing.md` (the deliverable)
- Read `eval-templates/eval-market-sizing.json` (the assertions)

### Step 2: Score Each Assertion

| ID    | Assertion                                                                        | Result | Justification |
| ----- | -------------------------------------------------------------------------------- | ------ | ------------- |
| MS-01 | TAM, SAM, and SOM are each explicitly defined with dollar amounts                |        |               |
| MS-02 | TAM calculation cites at least 2 independent data sources                        |        |               |
| MS-03 | SAM narrows from TAM with explicit filtering criteria (geography, segment, etc.) |        |               |
| MS-04 | SOM includes a realistic capture rate assumption with justification              |        |               |
| MS-05 | Bottom-up calculation is included alongside top-down (# customers x ARPU)        |        |               |
| MS-06 | Growth rate projections cite industry reports or observable trends               |        |               |
| MS-07 | Assumptions are explicitly listed and labeled as assumptions                     |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Would an analyst trust these numbers enough to include them in an investment memo?"

### Step 4: Calculate Score

- Passed: [count] / 7
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-market-sizing.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Market Sizing — Iteration [N]

**Score:** [X]/7 ([Y]%) — [PASS/FAIL]
**Meta-assertion:** [YES/NO]
**Threshold:** 75%

### Assertion Results
[table from Step 2]

### Failed Assertions (revision targets)
- [ID]: [what specifically needs to change]

### Learnings
- [what this critique revealed about the deliverable quality]
```
