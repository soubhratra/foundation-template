---
phase: 08-cli-scaffolder
plan: 01
subsystem: cli-scaffolder
tags: [cli, tooling, prompts, validation]
dependencies:
  requires: []
  provides: [cli-package, interactive-prompts, input-validation]
  affects: [monorepo-packages]
tech-stack:
  added: [@clack/prompts, validate-npm-package-name, fs-extra, picocolors]
  patterns: [interactive-cli, input-validation, error-handling]
key-files:
  created:
    - packages/create-foundation-app/package.json
    - packages/create-foundation-app/tsconfig.json
    - packages/create-foundation-app/bin/cli.js
    - packages/create-foundation-app/src/index.ts
    - packages/create-foundation-app/src/prompts.ts
    - packages/create-foundation-app/src/validate.ts
    - packages/create-foundation-app/src/utils.ts
    - packages/create-foundation-app/eslint.config.js
    - eslint.config.js
  modified:
    - pnpm-lock.yaml
decisions:
  - Re-prompt on validation errors instead of exiting CLI
  - All platforms checked by default in feature selection
  - Strict npm package name validation (validForNewPackages)
  - Empty directory validation prevents overwriting existing files
  - Root ESLint config added to support monorepo package linting
metrics:
  duration: 5
  tasks_completed: 2
  files_created: 9
  files_modified: 1
  lines_added: ~450
  completed: 2026-02-17
---

# Phase 08 Plan 01: CLI Package Scaffold with Interactive Prompts Summary

**One-liner:** Interactive CLI with @clack/prompts, strict npm package validation, and empty directory checks for safe project scaffolding

## What Was Built

Created the `@repo/create-foundation-app` package as a new workspace package with:

1. **CLI Infrastructure**
   - Executable `bin/cli.js` shebang entry point
   - TypeScript build pipeline with NodeNext module resolution
   - ESLint config for pre-commit hook compliance
   - Logger utilities using picocolors for consistent output

2. **Interactive Prompts**
   - `promptProjectName()`: Text input with inline npm package name validation
   - `promptFeatures()`: Multi-select with all platforms (web, mobile, landing, ai) checked by default
   - `promptOutputDir()`: Path validation ensuring empty or non-existent directories

3. **Validation Logic**
   - `validateProjectName()`: Uses `validate-npm-package-name` in strict mode (validForNewPackages)
   - `validateOutputDir()`: Checks directory exists and is empty, provides clear error messages
   - Re-prompting on invalid input instead of exiting (user-friendly behavior)

4. **Type Safety**
   - `ProjectConfig` interface exports collected configuration
   - `SelectedFeatures` type for feature selection
   - Full TypeScript compilation with declarations

## Key Decisions

### Re-prompt on Validation Errors

**Decision:** When user enters invalid input, re-prompt instead of exiting CLI
**Rationale:** Better UX - users can correct mistakes without restarting
**Impact:** All prompt functions use while loops with inline validation

### All Platforms Checked by Default

**Decision:** Feature selection defaults to all platforms checked
**Rationale:** Per user decision in CONTEXT.md - most users want full stack
**Impact:** `initialValues: ['web', 'mobile', 'landing', 'ai']` in promptFeatures()

### Root ESLint Config Added

**Decision:** Created root `eslint.config.js` for monorepo
**Rationale:** lint-staged runs from root and needs config to find package-level configs
**Impact:** All packages can now use ESLint in pre-commit hooks without config discovery issues

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] Added root ESLint config**

- **Found during:** Task 1 commit
- **Issue:** Pre-commit hook failed - eslint couldn't find config when run from root by lint-staged
- **Fix:** Created `eslint.config.js` at monorepo root extending baseConfig
- **Files modified:** `eslint.config.js` (new)
- **Commit:** c583829

**2. [Rule 3 - Blocking Issue] Added @repo/config-eslint dependency**

- **Found during:** Task 1 commit
- **Issue:** Pre-commit hook required ESLint config but package.json lacked config-eslint dependency
- **Fix:** Added `@repo/config-eslint: "workspace:*"` to devDependencies
- **Files modified:** `packages/create-foundation-app/package.json`
- **Commit:** c583829

**3. [Rule 3 - Blocking Issue] Added noEmit override to tsconfig**

- **Found during:** Task 1 verification
- **Issue:** TypeScript didn't emit dist/ files because base config has `noEmit: true`
- **Fix:** Added `"noEmit": false` to tsconfig.json compilerOptions
- **Files modified:** `packages/create-foundation-app/tsconfig.json`
- **Commit:** c583829

## Requirements Fulfilled

- **CLI-01:** Interactive prompts implemented (project name, features, output dir)
- **CLI-02:** Input validation with npm package rules and directory checks

## Testing Notes

**Manual verification performed:**

- CLI starts and shows intro message ✓
- Project name prompt appears with placeholder ✓
- Invalid names (spaces, uppercase) rejected with clear errors ✓
- Feature multi-select shows all 4 platforms checked by default ✓
- Output directory validation works for non-empty directories ✓
- TypeScript compiles without errors ✓
- Type-check passes ✓

**Validation test results:**

- `validateProjectName('my-saas-app')` → valid ✓
- `validateProjectName('My App')` → invalid (URL-friendly, no capitals) ✓
- `validateProjectName('MyApp')` → invalid (no capitals) ✓
- `validateOutputDir('./new-project')` → valid (non-existent) ✓
- `validateOutputDir('./src')` → invalid (not empty) ✓

## Next Steps

**Wave 2 (Plan 08-02):** Template generation

- Implement file copying from template directory
- Apply feature-based exclusions (AI module optional)
- Token replacement for project name
- Git initialization

**Wave 3 (Plan 08-03):** Post-generation setup

- Dependency installation (pnpm install)
- Database initialization
- Environment file generation
- Success message with next steps

## Self-Check

Verifying all claimed artifacts exist and commits are recorded:

**Files created:**

- packages/create-foundation-app/package.json: ✓
- packages/create-foundation-app/tsconfig.json: ✓
- packages/create-foundation-app/bin/cli.js: ✓
- packages/create-foundation-app/src/index.ts: ✓
- packages/create-foundation-app/src/prompts.ts: ✓
- packages/create-foundation-app/src/validate.ts: ✓
- packages/create-foundation-app/src/utils.ts: ✓
- packages/create-foundation-app/eslint.config.js: ✓
- eslint.config.js: ✓

**Commits verified:**

- c583829: Task 1 (CLI package scaffold) ✓
- 6d92132: Task 2 (Interactive prompts) ✓

## Self-Check: PASSED
