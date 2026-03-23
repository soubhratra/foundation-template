# Critique Task: Validation Report

> **Deliverable:** `phase-1/validation-report.md`
> **Eval file:** `eval-templates/eval-validation-report.json`
> **Phase:** 1 — Validation
> **Pass threshold:** 75% (6/8 assertions)

## Instructions

You are critiquing the validation report deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-1/validation-report.md` (the deliverable)
- Read `eval-templates/eval-validation-report.json` (the assertions)
- Also read `phase-1/competitor-matrix.md` and `phase-1/market-sizing.md` (needed for assertions VR-06 and VR-07)

### Step 2: Score Each Assertion

| ID    | Assertion                                                                                       | Result | Justification |
| ----- | ----------------------------------------------------------------------------------------------- | ------ | ------------- |
| VR-01 | Contains a clear go/no-go recommendation with stated confidence level                           |        |               |
| VR-02 | Lists the 3 riskiest assumptions and how each was tested                                        |        |               |
| VR-03 | Customer discovery plan specifies who to talk to (job title, company type) and sample questions |        |               |
| VR-04 | Kill criteria are defined with specific thresholds (not vague conditions)                       |        |               |
| VR-05 | Each kill criterion is evaluated against actual findings from research                          |        |               |
| VR-06 | Positioning statement differentiates from competitors found in the competitor matrix            |        |               |
| VR-07 | References specific data from the competitor matrix and market sizing (not standalone)          |        |               |
| VR-08 | Identifies at least one risk that could kill the startup post-launch                            |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Would a co-founder trust this report enough to commit 6 months of their life to this idea?"

### Step 4: Calculate Score

- Passed: [count] / 8
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-validation-report.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Validation Report — Iteration [N]

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
