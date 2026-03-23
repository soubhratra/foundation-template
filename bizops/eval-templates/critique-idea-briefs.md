# Critique Task: Idea Briefs

> **Deliverable:** `phase-0/idea-briefs.md`
> **Eval file:** `eval-templates/eval-idea-briefs.json`
> **Phase:** 0 — Ideation
> **Pass threshold:** 75% (6/8 assertions)

## Instructions

You are critiquing the idea briefs deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-0/idea-briefs.md` (the deliverable)
- Read `eval-templates/eval-idea-briefs.json` (the assertions)

### Step 2: Score Each Assertion

For each assertion, output TRUE or FALSE with a one-line justification:

| ID    | Assertion                                                                                      | Result | Justification |
| ----- | ---------------------------------------------------------------------------------------------- | ------ | ------------- |
| ID-01 | Each idea has a clearly stated problem affecting a specific, named customer segment            |        |               |
| ID-02 | Each idea has a revenue model with pricing range and payment trigger                           |        |               |
| ID-03 | Market size estimates cite specific data sources (reports, databases, public filings)          |        |               |
| ID-04 | Founder-fit scoring references specific founder skills/experience, not generic traits          |        |               |
| ID-05 | At least one idea leverages AI as a core differentiator, not just a feature                    |        |               |
| ID-06 | Each idea identifies at least 2 existing alternatives and explains why they're insufficient    |        |               |
| ID-07 | Time-to-revenue estimate includes specific assumptions (team size, stack, integrations needed) |        |               |
| ID-08 | Recommendation includes explicit reasoning for why rejected ideas were ranked lower            |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Could a seed-stage investor read this and understand why this opportunity is worth pursuing?"

### Step 4: Calculate Score

- Passed: [count] / 8
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-idea-briefs.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Idea Briefs — Iteration [N]

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
