# CLI Scaffolder Specification

> Baseline specification for the Foundation Template.
> This document is the source of truth. All implementations must conform to these specs.

## Overview

The CLI scaffolder (`create-foundation-app`) is an interactive command-line tool that generates new projects from the Foundation Template. It handles project name transformation, feature selection, secret generation, and post-generation validation. The goal: a developer runs one command, answers three questions, and gets a fully configured, production-ready monorepo that passes all quality checks out of the box.

## Specifications

### User Experience Flow

```
1. Project Name    →  2. Feature Selection  →  3. Output Directory  →  4. Generation
   (validated)         (multi-select)            (validated)             (with progress)
```

#### Step 1: Project Name Prompt

```
◆  What is your project name?
│  my-saas-app
│
│  ✓ Valid npm package name
└
```

**Validation Rules:**

- Must be valid npm package name (lowercase, hyphens, no spaces)
- Uses `validate-npm-package-name` package in strict mode
- On error: re-prompt with clear message (don't exit CLI)

**Decision:** Phase 08-cli-scaffolder, Phase 08-CONTEXT.md

#### Step 2: Feature Selection

```
◆  Select platforms and features to include
│  ◼ Next.js Web App (recommended)
│  ◼ Expo Mobile App (recommended)
│  ◼ Static Landing Page
│  ◼ AI Module (PGVector + LangGraph)
└  Press space to toggle, enter to confirm
```

**Default State:** All platforms checked (web, mobile, landing, AI)

**Rationale:** Most users want the full stack. Unchecking requires explicit opt-out.

**Toggles:**

- `web`: Next.js 15 web application
- `mobile`: Expo mobile application
- `landing`: Static marketing site (Next.js static export)
- `ai`: AI module with PGVector and LangGraph

**Decision:** Phase 08-cli-scaffolder

#### Step 3: Output Directory Prompt

```
◆  Where should we create your project?
│  ../my-saas-app
│
│  ✓ Directory is valid
└
```

**Validation:**

- Directory must not exist OR must be empty
- Parent directory must exist and be writable
- On error: re-prompt with clear message

**Decision:** Phase 08-CONTEXT.md

#### Step 4: Generation Process

```
◆  Creating project...
│  ● Copying template files
│  ● Transforming placeholders
│  ● Generating secrets
│  ● Removing excluded features
│  ● Running validation
└  ✓ Project created successfully!
```

**Steps:**

1. Copy template files (excluding build artifacts, caches)
2. Transform placeholders (project name replacement)
3. Generate unique secrets (Django SECRET_KEY, database passwords)
4. Remove excluded platforms (if any unchecked)
5. Run quality gates (lint + type-check + tests)

**Optional:** `--skip-validation` flag skips step 5 for faster generation during testing.

### File Operations

#### Template Copying

**Pattern:** Use `fs-extra` with `ignore` package for exclusions.

**Excluded Patterns:**

- `.git/` (version control)
- `node_modules/`, `__pycache__/`, `.venv/` (dependencies)
- `.next/`, `dist/`, `build/`, `.turbo/` (build artifacts)
- `.env`, `.env.local` (secrets)
- `coverage/`, `.pytest_cache/` (test artifacts)
- `.planning/` (GSD artifacts - not for generated projects)
- `packages/create-foundation-app/` (don't copy CLI into generated project)

**Include Dot-Directories:** `.github/` (CI workflows) using `dot:true` option.

**Implementation:**

```typescript
import { copy } from "fs-extra";
import ignore from "ignore";

const ig = ignore().add([
  ".git",
  "node_modules",
  "__pycache__",
  ".venv",
  ".next",
  "dist",
  "build",
  ".turbo",
  ".env",
  ".env.local",
  "coverage",
  ".pytest_cache",
  ".planning",
  "packages/create-foundation-app",
]);

await copy(templateDir, outputDir, {
  filter: (src) => !ig.ignores(src),
});
```

**Decision:** Phase 08-02

#### Placeholder Transformation

**Pattern:** Regex-based replacement on all text files.

**Replacements:**

- `foundation-template` → `{projectName}`
- `@repo/` → `@{projectName}/`
- `foundation-api` → `{projectName}-api`

**Files Transformed:**

- `package.json` (all occurrences)
- `tsconfig.json` (extends paths)
- `pyproject.toml` (project name)
- `*.ts`, `*.tsx`, `*.js`, `*.jsx` (import statements)
- `*.py` (package references)
- `*.md` (documentation)
- `*.yml`, `*.yaml` (CI workflows)
- `Dockerfile` (image names)
- `.github/**/*` (workflow files)

**Implementation:**

```typescript
import { globby } from "globby";
import { readFile, writeFile } from "fs-extra";

const files = await globby(
  [
    "**/*.{ts,tsx,js,jsx,py,md,yml,yaml,json}",
    "**/Dockerfile",
    "**/tsconfig.json",
    "**/package.json",
    "**/pyproject.toml",
  ],
  {
    cwd: outputDir,
    dot: true, // Include .github/
    absolute: true,
    ignore: ["**/node_modules/**", "**/.venv/**"],
  },
);

for (const file of files) {
  let content = await readFile(file, "utf-8");
  content = content.replace(/foundation-template/g, projectName);
  content = content.replace(/@repo\//g, `@${projectName}/`);
  content = content.replace(/foundation-api/g, `${projectName}-api`);
  await writeFile(file, content, "utf-8");
}
```

**Decision:** Phase 08-02

### Secret Generation

#### Django SECRET_KEY

**Pattern:** Generate 50-character random key using `crypto.randomBytes`.

**Implementation:**

```typescript
import { randomBytes } from "crypto";

function generateDjangoSecretKey(): string {
  return randomBytes(50).toString("base64").slice(0, 50);
}
```

**Rationale:** Follows Django documentation standards. Provides cryptographic security. Each generated project has unique secrets.

**Decision:** Phase 08-02

#### Database Credentials

**Pattern:** Generate random passwords for PostgreSQL.

**Implementation:**

```typescript
function generateDatabasePassword(): string {
  return randomBytes(16).toString("hex"); // 32 chars
}
```

#### Environment File Creation

**Pattern:** Create `.env` file with generated secrets.

```bash
# apps/api/.env (generated)
SECRET_KEY={generated-50-char-key}
DATABASE_URL=postgresql://user:{generated-password}@localhost:5432/{project-name}
REDIS_URL=redis://localhost:6379/0
```

### Feature Removal

#### Complete Cleanup Pattern

When a platform is excluded, perform complete removal:

1. Delete directory
2. Remove from workspace files
3. Strip dependencies
4. Update configuration

**No Empty Scaffolds:** Don't leave placeholder directories or stub files.

**Decision:** Phase 08-03

#### AI Module Removal

```typescript
async function removeAIModule(outputDir: string): Promise<void> {
  // 1. Delete directory
  await remove(join(outputDir, "apps/api/apps/ai"));

  // 2. Remove Python dependencies
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  let pyproject = await readFile(pyprojectPath, "utf-8");

  const aiDeps = [
    "pgvector",
    "tiktoken",
    "celery",
    "django-celery-results",
    "openai",
    "langgraph",
    "langchain-core",
    "langchain-openai",
  ];

  for (const dep of aiDeps) {
    pyproject = pyproject.replace(new RegExp(`^${dep}.*$`, "gm"), "");
  }

  await writeFile(pyprojectPath, pyproject, "utf-8");

  // 3. Remove from INSTALLED_APPS
  const settingsPath = join(outputDir, "apps/api/config/settings/base.py");
  let settings = await readFile(settingsPath, "utf-8");
  settings = settings.replace(/^\s*"apps\.ai",?\s*$/gm, "");
  await writeFile(settingsPath, settings, "utf-8");

  // 4. Remove AI env vars from .env.example
  const envPath = join(outputDir, "apps/api/.env.example");
  let env = await readFile(envPath, "utf-8");
  env = env.replace(/^OPENAI_API_KEY=.*$/gm, "");
  env = env.replace(/^CELERY_BROKER_URL=.*$/gm, "");
  await writeFile(envPath, env, "utf-8");
}
```

**Decision:** Phase 08-03

#### Mobile App Removal

```typescript
async function removeMobileApp(outputDir: string): Promise<void> {
  // 1. Delete directory
  await remove(join(outputDir, "apps/mobile"));

  // 2. Update pnpm-workspace.yaml
  const workspacePath = join(outputDir, "pnpm-workspace.yaml");
  let workspace = await readFile(workspacePath, "utf-8");
  workspace = workspace.replace(/^\s*- 'apps\/mobile'\s*$/gm, "");
  await writeFile(workspacePath, workspace, "utf-8");
}
```

**Similar patterns for:** `removeLandingApp()`, `removeWebApp()`

**Decision:** Phase 08-03

### Post-Generation Validation

#### Quality Gates

**Commands Run:**

1. `pnpm install` (timeout: 10 minutes)
2. `uv sync` in `apps/api/` (timeout: 10 minutes)
3. `pnpm turbo lint` (timeout: 5 minutes)
4. `ruff check apps/api` (timeout: 5 minutes)
5. `pnpm turbo type-check` (timeout: 10 minutes)
6. `uv run mypy apps/api` (timeout: 10 minutes)

**Rationale:** Ensures generated project works immediately without manual fixes.

**Implementation:**

```typescript
import { execa } from "execa";

async function runValidation(outputDir: string): Promise<void> {
  const steps = [
    { cmd: "pnpm", args: ["install"], timeout: 600000 },
    { cmd: "pnpm", args: ["turbo", "lint"], timeout: 300000 },
    { cmd: "pnpm", args: ["turbo", "type-check"], timeout: 600000 },
  ];

  for (const step of steps) {
    await execa(step.cmd, step.args, {
      cwd: outputDir,
      stdio: "inherit",
      timeout: step.timeout,
    });
  }
}
```

**Decision:** Phase 08-03

#### Skip Validation Flag

**Usage:** `node bin/cli.js --skip-validation`

**When to Use:**

- Faster generation during testing
- Offline development
- CI environments where validation runs separately

**Note:** User must manually run `pnpm install` and quality checks when skipped.

**Decision:** Phase 08-03

### Error Handling

#### Automatic Rollback

**Pattern:** On any error during generation, delete entire output directory.

**Rationale:** Better UX than leaving broken projects. Users can re-run CLI without cleanup.

**Implementation:**

```typescript
async function main() {
  try {
    await generateProject(projectName, features, outputDir);
  } catch (error) {
    console.error("Generation failed:", error.message);

    // Rollback: delete output directory
    if (await pathExists(outputDir)) {
      await remove(outputDir);
      console.log("Rolled back: deleted", outputDir);
    }

    process.exit(1);
  }
}
```

**Decision:** Phase 08-03, Phase 08-CONTEXT.md

#### Re-Prompt Strategy

**Pattern:** On validation errors, re-prompt instead of exiting CLI.

**Example:**

```
◆  What is your project name?
│  My App
│
│  ✗ Invalid: npm package names cannot contain spaces
│
◆  What is your project name?
│  my-app
│
│  ✓ Valid npm package name
└
```

**Benefit:** Better UX - users can correct mistakes without restarting CLI.

**Decision:** Phase 08-cli-scaffolder

## Implementation Stack

| Component          | Technology                | Purpose                                                     |
| ------------------ | ------------------------- | ----------------------------------------------------------- |
| Interactive UI     | @clack/prompts            | Beautiful terminal prompts (modern alternative to inquirer) |
| File operations    | fs-extra                  | Copy, read, write with Promise API                          |
| Process execution  | execa                     | Run validation commands with timeouts                       |
| Package validation | validate-npm-package-name | Validate project names against npm rules                    |
| File exclusions    | ignore                    | Gitignore-style pattern matching                            |
| File globbing      | globby                    | Find files for transformation                               |
| Secret generation  | crypto (Node.js built-in) | Cryptographic random bytes                                  |

## Constraints

1. **All platforms default to checked.** Users must explicitly opt-out of features.
2. **Complete removal or nothing.** No empty directories or stub files for excluded features.
3. **Automatic rollback on errors.** Never leave partially generated projects.
4. **Secrets must be unique.** Every generated project gets new SECRET_KEY, database passwords.
5. **Quality gates enforce correctness.** Generated project must pass lint + type-check (unless --skip-validation).
6. **Re-prompt on validation errors.** Never exit CLI on invalid input.

## References

- `.planning/phases/08-cli-scaffolder/08-CONTEXT.md` -- User decisions from discuss-phase
- `.planning/phases/08-cli-scaffolder/08-RESEARCH.md` -- CLI patterns research
- `packages/create-foundation-app/README.md` -- Usage documentation
