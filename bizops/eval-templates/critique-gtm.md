# Critique Task: GTM Plan

> **Deliverable:** `phase-3/gtm-plan.md`
> **Eval file:** `eval-templates/eval-gtm.json`
> **Phase:** 3 — Spec + GTM
> **Pass threshold:** 75% (6/8 assertions)

## Instructions

You are critiquing the GTM plan deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-3/gtm-plan.md` (the deliverable)
- Read `eval-templates/eval-gtm.json` (the assertions)
- Also read `context/ideal-customer.md` (needed for GTM-02) and `phase-1/competitor-matrix.md` (needed for GTM-08)

### Step 2: Score Each Assertion

| ID     | Assertion                                                                                                    | Result | Justification |
| ------ | ------------------------------------------------------------------------------------------------------------ | ------ | ------------- |
| GTM-01 | Positioning statement follows the format: For [ICP] who [need], [product] is a [category] that [key benefit] |        |               |
| GTM-02 | ICP in GTM plan matches the ICP defined in context/ideal-customer.md                                         |        |               |
| GTM-03 | At least 3 acquisition channels are identified with expected cost per lead                                   |        |               |
| GTM-04 | Launch timeline includes specific dates or sprint references, not 'soon'                                     |        |               |
| GTM-05 | Success metrics for first 90 days are defined with specific numbers                                          |        |               |
| GTM-06 | Content calendar covers at least 4 weeks of pre-launch content                                               |        |               |
| GTM-07 | Messaging framework includes headline, subhead, and 3 benefit statements                                     |        |               |
| GTM-08 | Competitive differentiation in messaging aligns with competitor matrix findings                              |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Could a marketing contractor execute this plan without additional strategic guidance?"

### Step 4: Calculate Score

- Passed: [count] / 8
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-gtm.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: GTM Plan — Iteration [N]

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
