# CLI Scaffolder — Feature Modules

> Defines the feature module layer of the `create-foundation-app` CLI: interactive prompts, file copy engine, secret generation, optional module removal (AI, email, social auth, B2B), and post-generation validation. For the complete CLI architecture and placeholder transformation pipeline, see `openspec/specs/foundation/cli-scaffolder.md`.

## Overview

The `create-foundation-app` CLI scaffolds a new product by copying the template repository and applying per-project transformations. This spec covers the feature-module selection layer:

- **Opt-out modules** (included by default, removable): Transactional Email, Social Auth, AI module. Each has a `remove*Module()` function that strips the module's files and settings fence markers.
- **Opt-in modules** (excluded by default, addable): B2B module (`--with b2b`). B2B is opt-in because most B2C products never need it; opt-out would impose the full B2B stack on the majority of scaffolds.
- **Post-generation validation**: `pnpm turbo lint` + `pnpm turbo type-check` + `manage.py check` must pass before the CLI exits successfully.

`foundation/cli-scaffolder.md` covers the placeholder transformation pipeline (`{{PROJECT_NAME}}`, `{{SECRET_KEY}}`), the full feature-removal architecture, and the validation strategy. Read that spec first for the overall design.

## Requirements

### Requirement: Interactive CLI Prompts for Project Configuration

The CLI scaffolder SHALL prompt the user for project configuration options including project name and optional AI module inclusion.

#### Scenario: CLI prompts for project name

- **WHEN** the CLI scaffolder is invoked with `create-foundation-app`
- **THEN** it MUST prompt "What is your project name?" with validation for valid package name format
- **THEN** it MUST reject names with spaces, uppercase letters, or special characters except hyphens and underscores
- **THEN** it MUST accept the validated name for use in package renaming

#### Scenario: CLI prompts for AI module inclusion

- **WHEN** the scaffolder prompts for features
- **THEN** it MUST ask "Include AI module with LLM integration and vector embeddings? (y/n)"
- **THEN** if the user selects "n", the AI module MUST be excluded from the generated project

### Requirement: File Copying and Renaming Engine

The scaffolder SHALL copy the template repository and rename package references throughout all configuration files.

#### Scenario: Template repository cloning

- **WHEN** the scaffolder starts project generation
- **THEN** it MUST copy all files from the template repository to the target directory
- **THEN** it MUST exclude `.git`, `node_modules`, `.venv`, and cache directories
- **THEN** it MUST initialize a new git repository in the target directory

#### Scenario: Package name replacement

- **WHEN** the user provides project name "my-app"
- **THEN** the scaffolder MUST replace all occurrences of template package name in:
  - `package.json` files (monorepo root and all workspaces)
  - `pyproject.toml` in `apps/api`
  - Docker Compose service names
  - README.md references
- **THEN** it MUST use the new name consistently across all files

### Requirement: Unique SECRET_KEY and Secrets Generation

The scaffolder SHALL generate cryptographically random secrets for each new project instance.

#### Scenario: SECRET_KEY generation

- **WHEN** the scaffolder creates a new project
- **THEN** it MUST generate a random 50-character SECRET_KEY using cryptographically secure random bytes
- **THEN** it MUST write the SECRET_KEY to `.env` in the project root
- **THEN** it MUST NOT reuse the template's placeholder SECRET_KEY

#### Scenario: Additional secrets generation

- **WHEN** the scaffolder creates `.env` file
- **THEN** it MUST generate unique values for database passwords if not provided
- **THEN** it MUST create `.env` from `.env.example` with generated secrets
- **THEN** `.env` MUST remain gitignored

### Requirement: AI Module Exclusion Logic

The scaffolder SHALL remove AI-related code, dependencies, and configuration when the user opts out of the AI module.

#### Scenario: AI module files removal

- **WHEN** the user selects "n" for AI module inclusion
- **THEN** the scaffolder MUST delete `apps/api/apps/ai/` directory
- **THEN** it MUST remove AI-related routes from Django URL configuration
- **THEN** it MUST remove PGVector migration files
- **THEN** it MUST remove PGVector extension from database setup

#### Scenario: AI dependency removal from pyproject.toml

- **WHEN** AI module is excluded
- **THEN** the scaffolder MUST remove `openai`, `anthropic`, and `pgvector` from dependencies in `pyproject.toml`
- **THEN** it MUST remove AI-related entries from `uv` configuration

#### Scenario: AI dependency removal from package.json

- **WHEN** AI module is excluded
- **THEN** the scaffolder MUST remove AI-related npm packages from workspace dependencies
- **THEN** it MUST remove AI-related OpenAPI schema types from `@repo/api-client`

### Requirement: Generated Project Validation

The scaffolder SHALL validate that the generated project passes all lint and type checks before completion.

#### Scenario: Post-generation validation

- **WHEN** the scaffolder completes file generation and renaming
- **THEN** it MUST run `pnpm install` to install JavaScript dependencies
- **THEN** it MUST run `uv sync --directory apps/api` to install Python dependencies
- **THEN** it MUST run `pnpm turbo lint` to verify linting passes
- **THEN** it MUST run `pnpm turbo type-check` to verify TypeScript types are valid
- **THEN** if any validation fails, it MUST report the error and exit with non-zero status

#### Scenario: Success message and next steps

- **WHEN** all validation passes
- **THEN** the scaffolder MUST display a success message with the project name
- **THEN** it MUST print next steps:
  - `cd <project-name>`
  - `cp .env.example .env` (if not already done)
  - `docker compose up -d` to start databases
  - `pnpm dev` to start development servers
- **THEN** it MUST exit with status code 0

### Requirement: B2B Module Opt-In via --with b2b

The `create-foundation-app` CLI SHALL support an opt-in `--with b2b` flag that includes the complete B2B module in the scaffolded project.

#### Scenario: B2B excluded by default

- **WHEN** the user runs `create-foundation-app` without `--with b2b`
- **THEN** the B2B module SHALL NOT be included in the generated project
- **AND** the interactive features multiselect SHALL show "B2B Module" as unchecked by default

#### Scenario: --with b2b flag includes full B2B module

- **WHEN** the user runs `create-foundation-app --with b2b`
- **THEN** the B2B module SHALL be included (apps/orgs/, apps/api_keys/, apps/webhooks/, apps/audit/)
- **AND** `django-pghistory` and `django-hijack` SHALL remain in `pyproject.toml`
- **AND** all `# B2B_START` / `# B2B_END` marker blocks SHALL be retained in Python files

#### Scenario: removeB2BModule() strips all B2B artifacts cleanly

- **WHEN** B2B is not selected during scaffolding
- **THEN** `removeB2BModule(outputDir)` SHALL:
  - Delete `apps/api/apps/orgs/`, `apps/api/apps/api_keys/`, `apps/api/apps/webhooks/`, `apps/api/apps/audit/` directories
  - Remove `django-pghistory` and `django-hijack` from `pyproject.toml` dependencies
  - Strip all `# B2B_START` / `# B2B_END` fenced blocks from all Python files
  - Collapse consecutive blank lines (max 1) in any modified file

#### Scenario: Post-removal manage.py check passes

- **WHEN** the B2B module is removed via the scaffolder
- **THEN** `manage.py check` SHALL pass with no errors
- **AND** no `# B2B_START` or `# B2B_END` markers SHALL remain in any file
- **AND** `apps.orgs`, `apps.api_keys`, `apps.webhooks`, `apps.audit` SHALL be absent from `INSTALLED_APPS`

#### Scenario: CI validates both B2B-included and B2B-excluded scaffolds

- **WHEN** the CI test suite runs
- **THEN** `test_scaffold_with_b2b` SHALL verify `manage.py check` passes with the full B2B stack
- **AND** `test_scaffold_without_b2b` SHALL verify `manage.py check` passes after removal and assert all four negative conditions (no markers, no INSTALLED_APPS entries, no directories, no pyproject.toml deps)

## Implementation Decisions

### Why --with b2b is opt-in (not opt-out like --without email)

B2B is an enterprise add-on that most solo or B2C products will never need. Making it opt-out would impose B2B complexity on the majority of scaffolded projects. The `--with b2b` opt-in matches how products deliberately choose to enable enterprise infrastructure, consistent with the "start minimal, add what you need" philosophy.

This reverses the convention used for email, social auth, and billing, which are opt-out (included by default). The distinction is intentional: the default experience should be a B2C SaaS app; B2B is a deliberate escalation.

### Why B2B_START/B2B_END markers (not a separate B2B branch or overlay)

A separate branch or overlay would require merge maintenance as the template evolves. Inline markers let B2B code live alongside non-B2B code in the same files, validated continuously by the same CI suite. The marker stripper removes fenced blocks at scaffolding time, producing a clean output without the template's maintenance burden.

**Marker style:** Python comment markers only (`# B2B_START`, `# B2B_END`). TypeScript/frontend B2B code is handled by directory deletion rather than inline markers — the entire B2B frontend pages and components are in dedicated directories.

### Why pyproject.toml deps are removed by string matching (not markers)

TOML file format does not support comment blocks with the same inline-removal semantics as Python. Explicit regex string matching for `django-pghistory` and `django-hijack` in `pyproject.toml` is simpler and more reliable than trying to add marker comments to TOML dependency arrays, which would require TOML-aware parsing.

### Why CI runs manage.py check (not just import tests)

`manage.py check` runs Django's full system checks — it validates `INSTALLED_APPS`, URL conf imports, model consistency, and all registered checks including the ones added for `WEBHOOK_EVENTS` and `API_KEY_SCOPES` validation. An import-only test would not catch missing app registrations or misconfigured settings. `manage.py check` is the ground truth for "does this project start cleanly."
