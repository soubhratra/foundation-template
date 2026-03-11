---
phase: 08-cli-scaffolder
plan: 02
subsystem: cli-scaffolder
tags: [cli, file-operations, transformation, secrets]
dependencies:
  requires: [cli-package, interactive-prompts]
  provides: [template-copy, placeholder-replacement, secret-generation]
  affects: [all-generated-projects]
tech-stack:
  added: []
  patterns: [file-filtering, regex-replacement, cryptographic-random]
key-files:
  created:
    - packages/create-foundation-app/src/copy.ts
    - packages/create-foundation-app/src/transform.ts
    - packages/create-foundation-app/src/secrets.ts
  modified:
    - packages/create-foundation-app/src/index.ts
decisions:
  - Use ignore package for file exclusion patterns
  - Transform all text files including tsconfig.json, Dockerfiles, and .json files
  - Include dot-directories (.github/) in transformation
  - Generate 50-character Django SECRET_KEY using crypto.randomBytes
  - Generate 32-character hex database passwords
  - Exclude cache directories (.npm-cache, .aider, .coverage) from template copy
metrics:
  duration: 8
  tasks_completed: 3
  files_created: 3
  files_modified: 1
  lines_added: ~300
  completed: 2026-02-17
---

# Phase 08 Plan 02: Template Generation Engine Summary

**One-liner:** Complete template transformation pipeline with file copying, placeholder replacement, and cryptographic secret generation

## What Was Built

Implemented the full template generation engine that transforms the foundation-template monorepo into a user's project:

1. **File Copying with Exclusions (copy.ts)**
   - `copyTemplate()` copies template to output directory
   - `getTemplateDir()` helper using import.meta.url for ESM compatibility
   - Excludes build artifacts (node_modules, dist, .next, **pycache**, .turbo, coverage)
   - Excludes version control (.git)
   - Excludes template-specific directories (.planning/, packages/create-foundation-app/)
   - Excludes cache directories (.npm-cache, .coverage, .aider.tags.cache.v4)
   - Validates output directory is empty before copying

2. **Placeholder Replacement (transform.ts)**
   - `getReplacementMap()` builds transformation mappings:
     - `foundation-template` → user's project name
     - `foundation-api` → `{project}-api`
     - `@repo/` → `@{project}/`
     - `Foundation Template` → Title Case project name
   - `replaceInFiles()` transforms all text files using regex
   - `toTitleCase()` helper for display name conversion
   - Supports package.json, tsconfig.json, pyproject.toml, source code, markdown, YAML, Dockerfiles, and all .json files
   - Includes dotfiles and dot-directories (.github/)

3. **Secret Generation (secrets.ts)**
   - `generateDjangoSecretKey()` creates 50-character random key using crypto.randomBytes
   - `generateDatabasePassword()` creates 32-character hex password
   - `writeEnvFile()` generates .env with:
     - Unique Django SECRET_KEY
     - Project-specific DATABASE_URL
     - Development defaults (DEBUG, CORS, API URLs)
     - Redis configuration for Celery
     - Commented OpenAI key placeholder

4. **Full CLI Flow (index.ts)**
   - Integrated copy → transform → secrets pipeline
   - Spinner feedback for each step
   - Success message with next steps (pnpm install, docker compose, pnpm dev)

## Key Decisions

### File Filtering Strategy

**Decision:** Use ignore package for exclusion patterns with comprehensive artifact list
**Rationale:** ignore package is standard for .gitignore-style patterns and handles edge cases
**Impact:** Generated projects start clean without build artifacts or cache files

### Transformation Scope

**Decision:** Transform all text files including config files (tsconfig.json, Dockerfiles, .json)
**Rationale:** Template references appear in many file types beyond just source code
**Impact:** Complete transformation requires `dot: true` in globby and comprehensive pattern list

### Secret Generation

**Decision:** Use crypto.randomBytes for Django SECRET_KEY with 50-character output
**Rationale:** Follows Django documentation recommendations and provides cryptographic security
**Impact:** Each generated project has unique, secure secrets

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added tsconfig.json, _.json, _.js to transformation patterns**

- **Found during:** Task 2 verification
- **Issue:** tsconfig.json files with `"extends": "@repo/config-ts"` weren't being transformed
- **Fix:** Added `**/tsconfig.json`, `**/*.json`, `**/*.js` to glob patterns
- **Files modified:** `packages/create-foundation-app/src/transform.ts`
- **Commit:** ff66f1d

**2. [Rule 1 - Bug] Added dot:true to globby options**

- **Found during:** Task 2 verification
- **Issue:** .github/workflows/ci.yml with `@repo/web` references wasn't being found
- **Fix:** Added `dot: true` to globby options to include dotfiles and dot-directories
- **Files modified:** `packages/create-foundation-app/src/transform.ts`
- **Commit:** ff66f1d

**3. [Rule 1 - Bug] Added Dockerfile patterns to transformation**

- **Found during:** Task 3 verification
- **Issue:** apps/web/Dockerfile with `@repo/web` wasn't being transformed
- **Fix:** Added `**/Dockerfile`, `**/Dockerfile.*` to glob patterns
- **Files modified:** `packages/create-foundation-app/src/transform.ts`
- **Commit:** ff66f1d

**4. [Rule 1 - Bug] Excluded cache directories from copy**

- **Found during:** Task 3 verification
- **Issue:** .npm-cache, .coverage, .aider cache copied to generated projects
- **Fix:** Added `.npm-cache`, `.coverage`, `.aider.tags.cache.v4` to exclusion list
- **Files modified:** `packages/create-foundation-app/src/copy.ts`
- **Commit:** ff66f1d

## Requirements Fulfilled

- **CLI-02:** Template copying with exclusions ✓
- **CLI-03:** Placeholder replacement across all file types ✓
- **CLI-04:** Secret generation for Django and database ✓

## Testing Notes

**Manual verification performed:**

- Full CLI flow executes without errors ✓
- Template files copied to output directory ✓
- Build artifacts (.git, node_modules, .planning/) excluded ✓
- Cache directories (.npm-cache, .coverage) excluded ✓
- All @repo/ references replaced with @{project}/ ✓
- All foundation-template references replaced ✓
- Unique Django SECRET_KEY generated (50 chars) ✓
- .env file created with project-specific DATABASE_URL ✓
- TypeScript compiles without errors ✓
- Type-check passes ✓

**Success criteria verified:**

```bash
# Generated project with test-app name:
grep -r "@repo/" . --exclude-dir=openspec --exclude-dir=node_modules
# Result: No matches ✓

grep -r "foundation-template" . --exclude-dir=openspec --exclude-dir=node_modules
# Result: No matches ✓

cat .env | grep SECRET_KEY
# Result: Unique 50-character key ✓

cat apps/web/package.json | grep "@test-app/"
# Result: Dependencies use @test-app/ scope ✓

cat apps/api/pyproject.toml | grep test-app-api
# Result: Package name is test-app-api ✓
```

## Next Steps

**Wave 3 (Plan 08-03):** Feature-based file removal and post-generation setup

- Implement feature removal (exclude AI module if user unchecks)
- Remove apps/mobile/ if mobile excluded
- Remove apps/landing/ if landing excluded
- Git initialization (git init && git add . && git commit -m "Initial commit from Foundation Template")
- Success message with feature-specific instructions

## Commits

- `0eccf56`: Task 1 - Implement file copying with exclusions
- `31c0c3d`: Task 2 - Implement placeholder replacement across all file types
- `ff66f1d`: Task 3 - Implement secret generation and wire up full CLI flow (includes bug fixes)

## Self-Check

Verifying all claimed artifacts exist and commits are recorded:

**Files created:**

- packages/create-foundation-app/src/copy.ts: ✓
- packages/create-foundation-app/src/transform.ts: ✓
- packages/create-foundation-app/src/secrets.ts: ✓

**Files modified:**

- packages/create-foundation-app/src/index.ts: ✓

**Commits verified:**

- 0eccf56: Task 1 (file copying) ✓
- 31c0c3d: Task 2 (placeholder replacement) ✓
- ff66f1d: Task 3 (secret generation + bug fixes) ✓

## Self-Check: PASSED
