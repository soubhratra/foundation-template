# Critique Task: Landing Page Copy

> **Deliverable:** `phase-3/landing-page-copy.md`
> **Eval file:** `eval-templates/eval-copy.json`
> **Phase:** 3 — Spec + GTM
> **Pass threshold:** 75% (6/7 assertions)

## Instructions

You are critiquing the landing page copy deliverable. You did NOT write this document. Your job is to score it ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read `phase-3/landing-page-copy.md` (the deliverable)
- Read `eval-templates/eval-copy.json` (the assertions)
- Also read `context/ideal-customer.md` (needed for CP-04) and `context/brand-voice.md` (needed for CP-05)

### Step 2: Score Each Assertion

| ID    | Assertion                                                                                                | Result | Justification |
| ----- | -------------------------------------------------------------------------------------------------------- | ------ | ------------- |
| CP-01 | Headline communicates the core value proposition in under 10 words                                       |        |               |
| CP-02 | Subheadline explains what the product does for whom                                                      |        |               |
| CP-03 | At least one clear CTA (call-to-action) is present with specific action text                             |        |               |
| CP-04 | Copy addresses the ICP's primary pain point from context/ideal-customer.md                               |        |               |
| CP-05 | Tone matches brand-voice.md guidelines                                                                   |        |               |
| CP-06 | Features section uses benefits language (what the user gets) not feature language (what the product has) |        |               |
| CP-07 | Social proof section is planned (even if placeholder for testimonials/logos)                             |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Would the target ICP understand what this product does and want to try it within 10 seconds of landing on this page?"

### Step 4: Calculate Score

- Passed: [count] / 7
- Pass rate: [%]
- Threshold: 75%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-copy.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the deliverable targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Landing Page Copy — Iteration [N]

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
