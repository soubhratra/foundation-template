# Phase 8: CLI Scaffolder - Research

**Researched:** 2026-02-17
**Domain:** Interactive CLI project generator
**Confidence:** MEDIUM (modern CLI patterns verified, specific library versions need npm registry check)

## Summary

CLI scaffolder implementation requires four core capabilities: interactive prompts, file system operations with exclusion patterns, template placeholder replacement, and post-generation validation. The Node.js ecosystem provides mature, well-tested libraries for each capability.

**Key findings:**

- **@clack/prompts** is the modern alternative to inquirer for interactive prompts, with better UX and simpler API
- **fs-extra** with filter functions handles directory copying while excluding node_modules, .git, etc.
- Template engines (Handlebars, Mustache) are overkill for simple placeholder replacement; regex-based string replacement is sufficient and more transparent
- **execa** provides robust child process execution for running validation commands (lint, type-check)
- **validate-npm-package-name** is the official npm package for validating project names
- Django SECRET_KEY generation uses Python's `secrets` module or `django.core.management.utils.get_random_secret_key`
- Filesystem transaction-style rollback requires manual cleanup since transactional filesystems (like Windows TxF) are platform-specific

**Primary recommendation:** Build a standalone Node.js CLI using @clack/prompts for UX, fs-extra for file operations, and execa for validation. Implement manual rollback on error (simpler and more cross-platform than transaction libraries).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Prompting Flow:**

- Hybrid approach — Ask project name first, then show multi-select feature menu
- Require explicit project name (no default)
- Features default to "all included" — user unchecks what they don't want
- Re-prompt with clear error message on invalid input (don't exit CLI)

**Project Naming and Transformation:**

- Prompt for output directory path during flow (don't assume current dir or auto-create)

**Feature Selection Granularity:**

- Platform-level toggles — user can include/exclude: web app, mobile app, landing page, AI module
- All features included by default (web ✓, mobile ✓, landing ✓, AI ✓) — user unchecks to exclude
- Complete removal when platform excluded — delete directories, remove from workspaces, strip dependencies (no empty scaffolds)

**Generation Validation and Rollback:**

- Run full quality gates on generated project — lint (ruff, eslint, prettier) + type-check (mypy, tsc) + tests (pytest, vitest)

### Claude's Discretion

**Prompting Flow:**

- Validation rules for project names (what characters allowed, length limits)

**Project Naming and Transformation:**

- Case transformation strategy (auto-detect and transform vs single canonical form)
- Template replacement mechanism (placeholder markers vs hardcoded string search)
- What gets renamed vs what keeps template references (foundation specs, app names, package names)

**Feature Selection Granularity:**

- Feature dependency handling (auto-enable dependencies vs block incompatible selections)

**Generation Validation and Rollback:**

- When to run validation (after generation completes vs incremental during generation)
- Validation failure handling (leave project with errors vs rollback vs ask user)
- Partial generation failure handling (automatic rollback vs leave for debugging)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID     | Description                                                                     | Research Support                                                                                     |
| ------ | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| CLI-01 | Interactive CLI asks project name and optional features (include AI module?)    | @clack/prompts provides text input, multi-select, and confirm prompts with validation                |
| CLI-02 | Generates new project directory with all configs renamed and updated            | fs-extra copy with filter, string replacement for placeholders in package.json, pyproject.toml       |
| CLI-03 | Generates unique Django SECRET_KEY and other secrets                            | Node.js crypto.randomBytes or call Python script using get_random_secret_key                         |
| CLI-04 | Updates package names across all package.json, pyproject.toml, and config files | Recursive file scanning + regex/string replacement for "foundation-template" and "@repo/" references |
| CLI-05 | Generated project passes all linting and type checks out of the box             | execa runs pnpm turbo lint, pnpm turbo type-check, cd apps/api && ruff check, etc.                   |
| AI-07  | CLI scaffolder can exclude AI module when generating new project                | AI module removal pattern from Phase 6 (delete apps/api/apps/ai/, remove deps from pyproject.toml)   |

</phase_requirements>

## Standard Stack

### Core Libraries

| Library                   | Version | Purpose                          | Why Standard                                                                                          |
| ------------------------- | ------- | -------------------------------- | ----------------------------------------------------------------------------------------------------- |
| @clack/prompts            | ^0.9.x  | Interactive CLI prompts          | Modern alternative to inquirer; better UX, simpler API, used by major tools (PNPM, Astro, Svelte Kit) |
| fs-extra                  | ^11.x   | Enhanced file system operations  | Industry standard for recursive copy, mkdir -p, remove with filter functions                          |
| execa                     | ^9.x    | Process execution for validation | Modern child_process wrapper with better error handling, used by 40M+ downloads/week                  |
| validate-npm-package-name | ^6.x    | NPM package name validation      | Official npm package for validation rules, ensures compatibility                                      |
| picocolors                | ^1.x    | Console colors                   | 14x smaller than chalk, 2x faster, zero dependencies, used by PostCSS/Vite                            |

### Supporting Libraries

| Library | Version | Purpose                      | When to Use                                                 |
| ------- | ------- | ---------------------------- | ----------------------------------------------------------- |
| ignore  | ^6.x    | .gitignore pattern matching  | Exclude files during copy (node_modules, .git, .next, etc.) |
| globby  | ^14.x   | Cross-platform glob matching | Find files to transform (all package.json, pyproject.toml)  |

### Alternatives Considered

| Instead of         | Could Use                     | Tradeoff                                                                                                    |
| ------------------ | ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| @clack/prompts     | inquirer or @inquirer/prompts | Inquirer is legacy (being rewritten); new API is verbose; @clack has better defaults                        |
| String replacement | Handlebars/Mustache/Nunjucks  | Template engines add complexity for simple {{ placeholder }} replacement; regex is transparent              |
| execa              | child_process directly        | child_process lacks promise API, better error handling, and cross-platform path resolution                  |
| Manual rollback    | fs-transaction libs           | Transactional filesystems are platform-specific (Windows TxF); manual cleanup is simpler and cross-platform |

**Installation:**

```bash
# In CLI scaffolder package/directory
pnpm add @clack/prompts fs-extra execa validate-npm-package-name picocolors ignore globby
pnpm add -D @types/fs-extra @types/validate-npm-package-name
```

## Architecture Patterns

### Recommended CLI Structure

```
bin/
├── cli.js                  # Executable entry point (#!/usr/bin/env node)
└── ...

src/
├── index.ts                # Main CLI logic orchestration
├── prompts.ts              # All interactive prompts (project name, features, output dir)
├── validate.ts             # Project name validation, output dir checks
├── copy.ts                 # File copying with exclusions
├── transform.ts            # Placeholder replacement in files
├── remove.ts               # Feature removal logic (AI module, mobile, etc.)
├── secrets.ts              # Generate Django SECRET_KEY and other secrets
├── validation-runner.ts    # Run lint/type-check/tests after generation
├── rollback.ts             # Cleanup on error
└── utils.ts                # Shared utilities (logging, error handling)
```

### Pattern 1: Interactive Prompts with Validation

**What:** Use @clack/prompts for all user input with inline validation and re-prompting on errors

**When to use:** All user-facing prompts (project name, features, output directory)

**Example:**

```typescript
// Source: @clack/prompts documentation + create-next-app pattern
import * as p from "@clack/prompts";
import { validateNpmPackageName } from "validate-npm-package-name";
import picocolors from "picocolors";

async function promptProjectName(): Promise<string> {
  const projectName = await p.text({
    message: "What is your project name?",
    placeholder: "my-saas-app",
    validate: (value) => {
      if (!value) return "Project name is required";

      const validation = validateNpmPackageName(value);
      if (!validation.validForNewPackages) {
        const errors = [...(validation.errors || []), ...(validation.warnings || [])];
        return `Invalid package name: ${errors.join(", ")}`;
      }

      return undefined; // Valid
    },
  });

  if (p.isCancel(projectName)) {
    p.cancel("Operation cancelled");
    process.exit(0);
  }

  return projectName as string;
}

async function promptFeatures(): Promise<string[]> {
  const features = await p.multiselect({
    message: "Select platforms to include:",
    options: [
      { value: "web", label: "Web Application (Next.js)", hint: "Recommended" },
      { value: "mobile", label: "Mobile Application (Expo)" },
      { value: "landing", label: "Landing Page (Static Next.js)" },
      { value: "ai", label: "AI Module (LangGraph + PGVector)" },
    ],
    initialValues: ["web", "mobile", "landing", "ai"], // All checked by default
    required: false, // Allow deselecting all (validation happens later)
  });

  if (p.isCancel(features)) {
    p.cancel("Operation cancelled");
    process.exit(0);
  }

  return features as string[];
}
```

### Pattern 2: File Copying with Exclusions

**What:** Copy template directory while excluding build artifacts, node_modules, .git, etc.

**When to use:** Initial project generation step

**Example:**

```typescript
// Source: fs-extra documentation + ignore package
import fs from "fs-extra";
import ignore from "ignore";
import path from "path";

async function copyTemplate(templateDir: string, outputDir: string): Promise<void> {
  // Load .gitignore patterns to exclude
  const ig = ignore();

  // Always exclude these patterns
  ig.add([
    ".git",
    "node_modules",
    ".next",
    "__pycache__",
    "*.pyc",
    ".venv",
    "venv",
    ".env",
    ".env.local",
    "dist",
    "build",
    ".turbo",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
  ]);

  await fs.copy(templateDir, outputDir, {
    filter: (src) => {
      const relativePath = path.relative(templateDir, src);

      // Always copy root directory
      if (relativePath === "") return true;

      // Exclude based on ignore patterns
      return !ig.ignores(relativePath);
    },
  });
}
```

### Pattern 3: Placeholder Replacement

**What:** Replace template placeholders in package.json, pyproject.toml, README, etc.

**When to use:** After copying template files, before feature removal

**Example:**

```typescript
// Source: Common scaffolder pattern (no specific library needed)
import fs from "fs-extra";
import { globby } from "globby";

interface ReplacementMap {
  [key: string]: string;
}

async function replaceInFiles(outputDir: string, replacements: ReplacementMap): Promise<void> {
  // Find all files that need transformation
  const files = await globby(
    ["**/{package.json,pyproject.toml,README.md,.env.example}", "apps/api/config/settings/**/*.py"],
    {
      cwd: outputDir,
      absolute: true,
    },
  );

  for (const file of files) {
    let content = await fs.readFile(file, "utf-8");

    // Apply all replacements
    for (const [placeholder, value] of Object.entries(replacements)) {
      // Use regex with global flag to replace all occurrences
      const regex = new RegExp(escapeRegex(placeholder), "g");
      content = content.replace(regex, value);
    }

    await fs.writeFile(file, content, "utf-8");
  }
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Usage
const replacements = {
  "foundation-template": projectName,
  "foundation-api": `${projectName}-api`,
  "@repo/": `@${projectName}/`,
};
```

### Pattern 4: Feature Removal

**What:** Remove optional features (AI module, mobile app, landing page) when user opts out

**When to use:** After placeholder replacement, based on user's feature selections

**Example:**

```typescript
// Source: Phase 6 AI module removal pattern
import fs from "fs-extra";
import path from "path";

async function removeAIModule(outputDir: string): Promise<void> {
  // Delete AI module directory
  await fs.remove(path.join(outputDir, "apps/api/apps/ai"));

  // Remove AI dependencies from pyproject.toml
  const pyprojectPath = path.join(outputDir, "apps/api/pyproject.toml");
  let pyproject = await fs.readFile(pyprojectPath, "utf-8");

  // Remove specific AI dependencies
  const aiDeps = [
    "pgvector",
    "openai",
    "langgraph",
    "langchain-core",
    "langchain-openai",
    "tiktoken",
    "celery",
  ];
  for (const dep of aiDeps) {
    const depRegex = new RegExp(`^\\s*"${dep}.*",?\\n`, "gm");
    pyproject = pyproject.replace(depRegex, "");
  }

  await fs.writeFile(pyprojectPath, pyproject, "utf-8");

  // Remove AI routes from Django URL configuration
  const urlsPath = path.join(outputDir, "apps/api/config/urls.py");
  let urls = await fs.readFile(urlsPath, "utf-8");

  urls = urls.replace(/from apps\.ai import.*\n/, "");
  urls = urls.replace(/path\(['"]ai\/.*\),?\n/g, "");

  await fs.writeFile(urlsPath, urls, "utf-8");
}

async function removeMobileApp(outputDir: string): Promise<void> {
  // Delete mobile directory
  await fs.remove(path.join(outputDir, "apps/mobile"));

  // Update pnpm-workspace.yaml to remove apps/mobile
  const workspacePath = path.join(outputDir, "pnpm-workspace.yaml");
  let workspace = await fs.readFile(workspacePath, "utf-8");

  // Remove apps/mobile entry (keep apps/* pattern but document that mobile is excluded)
  // Or switch from apps/* to explicit list: apps/web, apps/landing
  // Safer: explicit list to avoid accidentally including future apps
  workspace = workspace.replace(
    /packages:\s*\n\s*- "apps\/\*"/,
    'packages:\n  - "apps/web"\n  - "apps/landing"',
  );

  await fs.writeFile(workspacePath, workspace, "utf-8");
}
```

### Pattern 5: Secret Generation

**What:** Generate cryptographically secure secrets (Django SECRET_KEY, etc.)

**When to use:** After file copying and placeholder replacement, before writing .env file

**Example:**

```typescript
// Source: Django SECRET_KEY generation + Node.js crypto
import crypto from "crypto";

function generateDjangoSecretKey(): string {
  // Django SECRET_KEY: 50 random characters, URL-safe
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)";
  const length = 50;

  const bytes = crypto.randomBytes(length);
  let key = "";

  for (let i = 0; i < length; i++) {
    key += chars[bytes[i] % chars.length];
  }

  return key;
}

function generateDatabasePassword(): string {
  // 32-character alphanumeric password
  return crypto.randomBytes(16).toString("hex");
}

async function writeEnvFile(outputDir: string, projectName: string): Promise<void> {
  const secretKey = generateDjangoSecretKey();
  const dbPassword = generateDatabasePassword();

  const envContent = `# Django
SECRET_KEY=${secretKey}
DEBUG=True
DATABASE_URL=postgres://${projectName}:${dbPassword}@localhost:5432/${projectName}
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
`;

  await fs.writeFile(path.join(outputDir, ".env"), envContent, "utf-8");
}
```

### Pattern 6: Post-Generation Validation

**What:** Run lint, type-check, and tests to ensure generated project is valid

**When to use:** Final step before success message

**Example:**

```typescript
// Source: execa documentation + standard validation commands
import { execa } from "execa";
import picocolors from "picocolors";
import * as p from "@clack/prompts";

async function runValidation(outputDir: string): Promise<void> {
  const spinner = p.spinner();

  try {
    // Install dependencies first
    spinner.start("Installing dependencies...");
    await execa("pnpm", ["install"], { cwd: outputDir });
    spinner.stop("Dependencies installed");

    spinner.start("Installing Python dependencies...");
    await execa("uv", ["sync", "--directory", "apps/api"], { cwd: outputDir });
    spinner.stop("Python dependencies installed");

    // Run linting
    spinner.start("Running linters...");
    await execa("pnpm", ["turbo", "lint"], { cwd: outputDir });
    await execa("ruff", ["check", "."], { cwd: path.join(outputDir, "apps/api") });
    spinner.stop("Linting passed");

    // Run type checking
    spinner.start("Running type checks...");
    await execa("pnpm", ["turbo", "type-check"], { cwd: outputDir });
    await execa("mypy", ["."], { cwd: path.join(outputDir, "apps/api") });
    spinner.stop("Type checking passed");

    // Run tests
    spinner.start("Running tests...");
    await execa("pnpm", ["turbo", "test"], { cwd: outputDir });
    await execa("pytest", [], { cwd: path.join(outputDir, "apps/api") });
    spinner.stop("All tests passed");

    p.log.success(picocolors.green("✓ Generated project passed all validation checks"));
  } catch (error) {
    spinner.stop("Validation failed");

    const execaError = error as { stderr?: string; stdout?: string };
    p.log.error(picocolors.red("✗ Validation failed:"));
    if (execaError.stderr) {
      console.error(execaError.stderr);
    }

    throw error;
  }
}
```

### Pattern 7: Error Rollback

**What:** Clean up partially generated project on error

**When to use:** Catch all errors during generation and rollback

**Example:**

```typescript
// Source: Manual cleanup pattern (cross-platform)
async function generateProject(config: ProjectConfig): Promise<void> {
  const { outputDir } = config;

  try {
    // 1. Copy template
    await copyTemplate(TEMPLATE_DIR, outputDir);

    // 2. Replace placeholders
    await replaceInFiles(outputDir, getReplacements(config));

    // 3. Remove excluded features
    if (!config.features.includes("ai")) {
      await removeAIModule(outputDir);
    }
    if (!config.features.includes("mobile")) {
      await removeMobileApp(outputDir);
    }

    // 4. Generate secrets
    await writeEnvFile(outputDir, config.projectName);

    // 5. Validate
    await runValidation(outputDir);

    // Success!
    p.outro(picocolors.green(`✓ Project "${config.projectName}" created successfully!`));
  } catch (error) {
    // Rollback: delete output directory
    p.log.error("Error during generation. Rolling back...");

    try {
      await fs.remove(outputDir);
      p.log.info("Cleanup complete");
    } catch (cleanupError) {
      p.log.warn("Failed to clean up output directory. You may need to delete it manually.");
    }

    p.cancel("Project generation failed");
    process.exit(1);
  }
}
```

### Anti-Patterns to Avoid

- **Don't use template engines for simple replacement:** Handlebars/Mustache add parsing overhead and error-prone syntax for simple string replacement. Regex is transparent and predictable.
- **Don't shell out to git clone:** Use degit or direct fs.copy to avoid .git history. Cleaner and faster.
- **Don't validate after every file operation:** Batch validation at the end. Individual file validation is slow and provides no benefit.
- **Don't use transactional filesystem libraries:** Platform-specific (Windows TxF not available on Linux/macOS). Manual rollback with fs.remove is simpler and cross-platform.
- **Don't modify files in place during copy:** Copy first, then transform. Easier to debug and safer if errors occur mid-copy.

## Don't Hand-Roll

| Problem                     | Don't Build                               | Use Instead               | Why                                                                                                              |
| --------------------------- | ----------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| NPM package name validation | Custom regex for npm naming rules         | validate-npm-package-name | NPM's rules change over time (scoped packages, length limits, reserved names); official package tracks updates   |
| Process execution           | Manual child_process.spawn with callbacks | execa                     | Handles promise API, stdio buffering, cross-platform path resolution, and better error messages                  |
| .gitignore parsing          | Custom pattern matching                   | ignore package            | .gitignore spec has edge cases (negation, directory-only patterns, trailing slash); ignore implements full spec  |
| Interactive prompts         | Raw readline or inquirer from scratch     | @clack/prompts            | Handles terminal state, cursor positioning, validation, cancellation; building from scratch is hundreds of lines |
| Directory traversal         | Manual recursive fs.readdir               | globby                    | Cross-platform glob patterns, negation, multiple patterns, gitignore integration                                 |

**Key insight:** CLI tooling has deceptively complex edge cases (terminal state management, cross-platform paths, process stdio buffering). Use battle-tested libraries; don't reinvent.

## Common Pitfalls

### Pitfall 1: Output Directory Already Exists

**What goes wrong:** CLI tries to create output directory but it already exists with files, causing copy to fail or merge with existing content

**Why it happens:** User provides existing directory path, or previously failed generation left partial files

**How to avoid:**

- Check if output directory exists before starting generation
- Prompt user: overwrite, choose different path, or cancel
- If overwriting, ensure directory is empty or prompt for confirmation

**Warning signs:** fs.copy throws EEXIST error, or generated project has mixed old/new content

### Pitfall 2: Placeholder Replacement Misses Files

**What goes wrong:** Some files still contain "foundation-template" or "@repo/" after generation

**Why it happens:** Glob pattern doesn't match all file types that need transformation, or binary files are transformed (corrupting them)

**How to avoid:**

- Explicitly list file patterns to transform (package.json, .ts, .tsx, .py, .md, .yml)
- Exclude binary files (.png, .jpg, .woff, .woff2, node_modules)
- Test generated project thoroughly to find missed files

**Warning signs:** Generated project has template name in import paths, workspace references fail

### Pitfall 3: Validation Runs Before Dependencies Installed

**What goes wrong:** pnpm turbo lint fails because node_modules doesn't exist yet

**Why it happens:** Validation runs immediately after file copy, skipping dependency installation

**How to avoid:**

- Always run `pnpm install` and `uv sync` before validation
- Show clear spinner/progress indicator so user knows dependencies are installing
- Validation order: install → lint → type-check → test

**Warning signs:** Execa errors like "command not found: eslint" or "Cannot find module"

### Pitfall 4: Feature Removal Leaves Orphaned References

**What goes wrong:** Removing AI module leaves import statements in other files, causing type errors or runtime errors

**Why it happens:** Feature removal deletes directories but doesn't scan for cross-references in other files

**How to avoid:**

- For each removed feature, explicitly remove imports and references in other files
- Run full validation after removal to catch orphaned references
- Document feature dependencies (e.g., web app may import from AI module)

**Warning signs:** Type errors after generation, import statements pointing to deleted directories

### Pitfall 5: Cross-Platform Path Separators

**What goes wrong:** Generated project works on developer's OS (e.g., macOS) but fails on Windows due to hardcoded / in paths

**Why it happens:** String replacement uses hardcoded / instead of path.sep or path.join

**How to avoid:**

- Always use path.join for file paths
- Use path.relative for relative paths
- Avoid string concatenation with / or \\

**Warning signs:** Generated project fails on Windows CI but passes locally on macOS/Linux

### Pitfall 6: Validation Timeout on Slow Machines

**What goes wrong:** Validation step times out on slower machines or CI environments

**Why it happens:** Default execa timeout is too short for large monorepo type-checking

**How to avoid:**

- Set generous timeouts for validation commands (5-10 minutes)
- Show progress indicator so user knows it's still running
- Consider making full validation optional (--skip-validation flag)

**Warning signs:** Execa throws timeout error during type-check or test step

## Code Examples

Verified patterns from official sources:

### NPM Package Name Validation

```typescript
// Source: validate-npm-package-name npm package
import validateNpmPackageName from "validate-npm-package-name";

function isValidProjectName(name: string): { valid: boolean; errors: string[] } {
  const result = validateNpmPackageName(name);

  if (result.validForNewPackages) {
    return { valid: true, errors: [] };
  }

  const errors = [...(result.errors || []), ...(result.warnings || [])];

  return { valid: false, errors };
}
```

### Interactive Multi-Select with Default All Selected

```typescript
// Source: @clack/prompts documentation
import * as p from "@clack/prompts";

const features = await p.multiselect({
  message: "Select platforms to include:",
  options: [
    { value: "web", label: "Web Application" },
    { value: "mobile", label: "Mobile Application" },
    { value: "landing", label: "Landing Page" },
    { value: "ai", label: "AI Module" },
  ],
  initialValues: ["web", "mobile", "landing", "ai"], // All selected by default
  required: false, // Allow deselecting
});
```

### Copy Directory with Exclusions

```typescript
// Source: fs-extra + ignore package documentation
import fs from "fs-extra";
import ignore from "ignore";
import path from "path";

const ig = ignore().add([".git", "node_modules", ".next", "__pycache__", ".venv"]);

await fs.copy(templateDir, outputDir, {
  filter: (src) => {
    const relative = path.relative(templateDir, src);
    return relative === "" || !ig.ignores(relative);
  },
});
```

### Run Command with Output Streaming

```typescript
// Source: execa documentation
import { execa } from "execa";

try {
  await execa("pnpm", ["install"], {
    cwd: outputDir,
    stdio: "inherit", // Stream output to console
    timeout: 300000, // 5 minutes
  });
} catch (error) {
  console.error("Installation failed:", error.message);
  throw error;
}
```

## State of the Art

| Old Approach                  | Current Approach                    | When Changed            | Impact                                                                                                                |
| ----------------------------- | ----------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------- |
| inquirer (legacy)             | @inquirer/prompts or @clack/prompts | 2024-2025               | inquirer rewrote to modular @inquirer/prompts; @clack/prompts emerged as modern alternative with better UX            |
| chalk for colors              | picocolors                          | 2021-present            | picocolors is 14x smaller, 2x faster; chalk still works but unnecessary weight for simple use cases                   |
| Template engines (Handlebars) | String replacement with regex       | N/A (context-dependent) | For simple {{ var }} replacement, template engines are overkill; regex is faster and more transparent                 |
| child_process                 | execa                               | 2018-present            | execa provides promises, better error handling, stdio buffering; now standard in modern CLIs                          |
| degit for template download   | Direct fs.copy from local template  | N/A (context-dependent) | For local-first templates (not downloading from GitHub), fs.copy is simpler; degit useful if template hosted remotely |

**Deprecated/outdated:**

- **inquirer legacy API:** Use @inquirer/prompts or @clack/prompts instead
- **chalk for lightweight CLIs:** Use picocolors (smaller, faster)
- **Manual child_process.spawn:** Use execa (promise API, better errors)

## Open Questions

1. **Where should the CLI live?**
   - **What we know:** Could be standalone package (cli/) or workspace package (packages/create-foundation-app)
   - **What's unclear:** Whether to publish to npm or keep local-only
   - **Recommendation:** Start as workspace package (packages/create-foundation-app), publish to npm later if needed

2. **Should validation be optional?**
   - **What we know:** Full validation (lint + type-check + tests) can take 5-10 minutes on slow machines
   - **What's unclear:** Whether to provide --skip-validation flag or always run validation
   - **Recommendation:** Always run lint + type-check (fast, catches critical errors); make test suite optional with --skip-tests flag

3. **How to handle case transformation?**
   - **What we know:** Project names can be kebab-case (my-app), snake_case (my_app), or PascalCase (MyApp)
   - **What's unclear:** Should CLI accept any case and auto-transform, or enforce kebab-case only?
   - **Recommendation:** Enforce kebab-case for npm compatibility; auto-transform to PascalCase for display name (e.g., README title)

4. **Should CLI support remote template URLs?**
   - **What we know:** degit can download templates from GitHub
   - **What's unclear:** Whether to support `npx create-foundation-app --template https://github.com/user/custom-template`
   - **Recommendation:** Start with local template only; add remote template support in v2 if needed

## Sources

### Primary (HIGH confidence)

- [validate-npm-package-name (npm)](https://www.npmjs.com/package/validate-npm-package-name) - Official npm package for name validation
- [fs-extra (GitHub)](https://github.com/jprichardson/node-fs-extra) - File system operations with filter support
- [execa (npm)](https://www.npmjs.com/package/execa) - Process execution for humans
- [@clack/prompts documentation](https://www.clack.cc/) - Interactive CLI prompts
- [Django SECRET_KEY generation (Gist)](https://gist.github.com/ndarville/3452907) - Secure SECRET_KEY generation pattern

### Secondary (MEDIUM confidence)

- [create-next-app CLI (Next.js docs)](https://nextjs.org/docs/app/api-reference/cli/create-next-app) - Interactive prompt flow reference
- [picocolors (npm)](https://www.npmjs.com/package/picocolors) - Lightweight console colors
- [ignore package (GitHub)](https://github.com/kaelzhang/node-ignore) - .gitignore pattern matching
- [Elevate Your CLI Tools with @clack/prompts](https://www.blacksrc.com/blog/elevate-your-cli-tools-with-clack-prompts) - Modern CLI patterns

### Tertiary (LOW confidence - needs verification)

- [Transactional NTFS (Wikipedia)](https://en.wikipedia.org/wiki/Transactional_NTFS) - Platform-specific filesystem transactions
- [degit usage](https://medium.com/@ramu.narasinga_61050/use-degit-to-download-a-template-in-your-cli-tool-6d2b628ac933) - Template downloading without git history

## Metadata

**Confidence breakdown:**

- Standard stack: MEDIUM - Library recommendations based on ecosystem trends; versions need npm registry verification
- Architecture: HIGH - Patterns verified from official docs and real-world CLI implementations (create-next-app, create-react-app)
- Pitfalls: HIGH - Common issues documented across multiple sources and GitHub issues

**Research date:** 2026-02-17
**Valid until:** 30 days (CLI patterns are stable; library versions may update monthly)

---

_Research complete for Phase 8: CLI Scaffolder_
_Ready for planning phase_
