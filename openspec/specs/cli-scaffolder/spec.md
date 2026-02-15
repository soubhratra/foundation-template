## ADDED Requirements

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
