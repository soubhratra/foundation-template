# Critique Task: Context Folder

> **Deliverable:** `context/` (all 6 files)
> **Eval file:** `eval-templates/eval-context.json`
> **Phase:** 2 — Context + Agents
> **Pass threshold:** 83% (5/6 assertions)

## Instructions

You are critiquing the context folder as a complete unit. You did NOT write these files. Your job is to score them ruthlessly against the assertions below, with no praise and no hedging.

### Step 1: Load Files

- Read all files in `context/`:
  - `context/about-founder.md`
  - `context/brand-voice.md`
  - `context/ideal-customer.md`
  - `context/product-info.md`
  - `context/voice-dna.md`
  - `context/working-preferences.md`
- Read `eval-templates/eval-context.json` (the assertions)

### Step 2: Score Each Assertion

| ID     | Assertion                                                                             | Result | Justification |
| ------ | ------------------------------------------------------------------------------------- | ------ | ------------- |
| CTX-01 | about-founder.md contains specific technical skills, not just 'experienced developer' |        |               |
| CTX-02 | ideal-customer.md names a specific job title, company size, and pain point            |        |               |
| CTX-03 | brand-voice.md includes at least 3 'do' examples and 3 'don't' examples               |        |               |
| CTX-04 | product-info.md references validated needs from Phase 1, not assumptions              |        |               |
| CTX-05 | No context file contradicts another context file                                      |        |               |
| CTX-06 | Every context file is usable by an agent that has NEVER seen the startup before       |        |               |

### Step 3: Meta-Assertion

Answer YES or NO:

> "Could a new agent read only the context/ folder and produce on-brand, on-target work for this startup?"

### Step 4: Calculate Score

- Passed: [count] / 6
- Pass rate: [%]
- Threshold: 83%
- **Result: PASS / FAIL**

### Step 5: Decision

- If **PASS** → Log scores to `eval-context.json` history. Update `memory/co-ceo-memory.md` with learnings. Proceed to gate post.
- If **FAIL** → List the specific failures. Revise the specific context files targeting ONLY the failed assertions. Re-run this critique (max 3 iterations total).
- If **3 iterations FAIL** → Post to gates channel as ESCALATION with the failure report. Do not ship.

### Output Format

```
## Critique Report: Context Folder — Iteration [N]

**Score:** [X]/6 ([Y]%) — [PASS/FAIL]
**Meta-assertion:** [YES/NO]
**Threshold:** 83%

### Assertion Results
[table from Step 2]

### Failed Assertions (revision targets)
- [ID]: [which context file] — [what specifically needs to change]

### Cross-File Consistency Notes
- [any contradictions or gaps found between context files]

### Learnings
- [what this critique revealed about the context quality]
```
