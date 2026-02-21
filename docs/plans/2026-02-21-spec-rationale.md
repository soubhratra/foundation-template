# Spec Rationale Enrichment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make all foundation specs self-contained so rationale survives into scaffolded product repos, and codify this as a CLAUDE.md rule.

**Architecture:** Surgical edits only — add two missing rationale blocks to `architecture.md`, replace dead `.planning/` References sections in all 6 foundation specs with a self-contained note, and add a rule to `CLAUDE.md`.

**Tech Stack:** Markdown edits only. No code changes. No tests. Commit after each logical group.

---

### Task 1: Add `pnpm node-linker=hoisted` to architecture.md

**Files:**

- Modify: `openspec/specs/foundation/architecture.md`

**Context:** The `.npmrc` file in this repo contains `node-linker=hoisted`. This is required for Expo/Metro compatibility but is not documented in any spec — only in MEMORY.md. New product teams will hit silent Metro resolution failures without knowing why.

**Step 1: Find the insertion point**

The spec has a "Workspace Configuration Patterns" section with existing pattern blocks (Config Packages in Root devDependencies, Root ESLint Configuration, Expo Type Environment Alignment, Metro Workspace Package Resolution). Add the new block BEFORE the Metro block, since node-linker=hoisted is a prerequisite to Metro working at all.

**Step 2: Add the pattern block**

Find this exact text in `openspec/specs/foundation/architecture.md`:

```
#### Metro Workspace Package Resolution
```

Insert the following block immediately before it:

```markdown
#### pnpm node-linker=hoisted

**What:** `.npmrc` at repo root must contain:
```

node-linker=hoisted

```

**Why:** pnpm's default symlink strategy creates a virtual store layout where packages are symlinked rather than physically present in `node_modules/`. Metro bundler (Expo) cannot follow these symlinks during bundle resolution — it silently fails to find `@repo/*` workspace packages, producing confusing "cannot find module" errors at bundle time that don't appear in Next.js (which uses webpack and handles symlinks correctly).

The hoisted layout physically copies all packages into `node_modules/` at the workspace root, which Metro can resolve without special configuration.

**Rejected alternative:** pnpm default symlink strategy — works for Next.js and Node.js tools but silently breaks Metro. The failure is non-obvious because Next.js builds succeed while only the Expo bundler is affected.

**Decision:** Phase 01 (Monorepo Foundation)

```

**Step 3: Verify the edit looks right**

Open `openspec/specs/foundation/architecture.md` and confirm the new block appears between "Expo Type Environment Alignment" and "Metro Workspace Package Resolution" sections.

**Step 4: Commit**

```bash
git add openspec/specs/foundation/architecture.md
git commit -m "docs(specs): document pnpm node-linker=hoisted rationale in architecture spec"
```

---

### Task 2: Add Turborepo+Python pitfall note to architecture.md

**Files:**

- Modify: `openspec/specs/foundation/architecture.md`

**Context:** The constraints section already says "Django is a pnpm workspace for task orchestration only." But it doesn't explain what breaks if someone treats it as a real JS workspace. That detail only lives in `.planning/research/PITFALLS.md` which won't exist in new products.

**Step 1: Find the constraint**

In `openspec/specs/foundation/architecture.md`, find this exact text in the Constraints section:

```
2. **Django is a pnpm workspace for task orchestration only.** Python dependencies managed by uv. `apps/api/package.json` has no JS/TS dependencies — it exists solely to register scripts (`dev`, `lint`, `test`, `type-check`) so Turborepo can orchestrate them alongside JS/TS tasks.
```

**Step 2: Expand it with the pitfall note**

Replace the above with:

```markdown
2. **Django is a pnpm workspace for task orchestration only.** Python dependencies managed by uv. `apps/api/package.json` has no JS/TS dependencies — it exists solely to register scripts (`dev`, `lint`, `test`, `type-check`) so Turborepo can orchestrate them alongside JS/TS tasks.

   **What breaks if you treat it as a real JS workspace:** Turborepo hashes package.json dependency graphs for cache invalidation. A Django app with no JS dependencies appears to Turborepo as a package whose inputs never change. Result: CI caches never hit (Turborepo reports MISS every run), or the inverse — Turborepo incorrectly caches Python tasks and skips re-running tests after code changes. The fix is explicit `inputs` globs in `turbo.json` covering `**/*.py` files, which bypasses Turborepo's dependency graph for Python tasks.
```

**Step 3: Commit**

```bash
git add openspec/specs/foundation/architecture.md
git commit -m "docs(specs): add Turborepo+Python pitfall context to architecture constraint"
```

---

### Task 3: Fix References section in architecture.md

**Files:**

- Modify: `openspec/specs/foundation/architecture.md`

**Step 1: Find the References section**

At the bottom of the file:

```markdown
## References

- `.planning/research/ARCHITECTURE.md` -- Full architecture research with data flow diagrams
- `.planning/research/PITFALLS.md` -- Turborepo/Docker/Metro pitfalls and mitigations
- `.planning/research/STACK.md` -- Technology choices and configuration patterns
```

**Step 2: Replace it**

```markdown
## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
```

**Step 3: Commit**

```bash
git add openspec/specs/foundation/architecture.md
git commit -m "docs(specs): replace dead .planning/ references with self-contained note in architecture spec"
```

---

### Task 4: Fix References sections in the remaining 5 foundation specs

**Files:**

- Modify: `openspec/specs/foundation/stack.md`
- Modify: `openspec/specs/foundation/auth.md`
- Modify: `openspec/specs/foundation/api-contracts.md`
- Modify: `openspec/specs/foundation/ai-stack.md`
- Modify: `openspec/specs/foundation/conventions.md`

**Context:** Each of these specs ends with a `## References` section containing 2-3 bullet points linking to `.planning/research/*.md` files. Those files are excluded from scaffolded products. Replace all five with the same self-contained note.

**Step 1: For each file, find the References section**

Each file ends with a block like this (exact paths vary per file):

```markdown
## References

- `.planning/research/STACK.md` -- ...
- `.planning/research/PITFALLS.md` -- ...
- `.planning/research/SUMMARY.md` -- ...
```

**Step 2: Replace with the self-contained note in all five files**

Same replacement text for all five:

```markdown
## Note on Research Files

The `.planning/` directory is excluded from projects scaffolded using this template. This spec is the self-contained source of rationale — all decisions, alternatives considered, and implementation constraints are documented inline above. No external research files are required to understand or implement the decisions in this spec.
```

**Step 3: Commit all five at once**

```bash
git add \
  openspec/specs/foundation/stack.md \
  openspec/specs/foundation/auth.md \
  openspec/specs/foundation/api-contracts.md \
  openspec/specs/foundation/ai-stack.md \
  openspec/specs/foundation/conventions.md
git commit -m "docs(specs): replace dead .planning/ references with self-contained notes in all foundation specs"
```

---

### Task 5: Add self-contained specs rule to CLAUDE.md

**Files:**

- Modify: `CLAUDE.md`

**Step 1: Find the insertion point**

In `CLAUDE.md`, find the **OpenSpec Rules** section. It currently has two subsections:

- "When to Use Change Proposals vs Direct Edits"
- "Foundation Specs Inheritance"
- "Workflow Commands"

Insert the new rule AFTER "Foundation Specs Inheritance" and BEFORE "Workflow Commands".

Find this exact text:

```markdown
### Workflow Commands
```

**Step 2: Insert the new rule before it**

```markdown
### Self-Contained Specs Rule

Foundation specs (`openspec/specs/`) are copied verbatim to every new product scaffolded using this template. The `.planning/` directory is **not** copied — it is explicitly excluded by the CLI scaffolder.

**Therefore: specs must be fully self-contained.** Every spec must include:

- **What** the decision is (the rule or pattern)
- **Why** it was chosen (rationale, tradeoffs, constraints)
- **What alternatives were rejected** and why they were rejected

Never reference `.planning/` files in spec documents as a source of rationale. Any rationale worth preserving must live in the spec itself, inline with the decision it explains.

This rule applies equally to:

- Foundation specs (`openspec/specs/foundation/`) — inherited by all products
- Product-specific specs (`openspec/specs/[domain]/`) — created per product

**When writing or updating any spec**, ask: _"If a developer on a new product repo read only this spec, would they understand the decision and could they make consistent future decisions without external context?"_ If no, add the missing rationale inline.

### Workflow Commands
```

**Step 3: Verify**

Read the OpenSpec Rules section and confirm the new rule appears cleanly between "Foundation Specs Inheritance" and "Workflow Commands".

**Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(CLAUDE.md): add self-contained specs rule for foundation and product specs"
```

---

## Verification

After all tasks complete, verify the work:

```bash
# Confirm no .planning/ references remain in foundation specs
grep -r "\.planning/" openspec/specs/foundation/

# Expected output: empty (no matches)
```

```bash
# Confirm node-linker=hoisted section exists
grep -n "node-linker=hoisted" openspec/specs/foundation/architecture.md

# Expected: line number with the section header
```

```bash
# Confirm CLAUDE.md has the new rule
grep -n "Self-Contained Specs Rule" CLAUDE.md

# Expected: line number of the new section header
```
