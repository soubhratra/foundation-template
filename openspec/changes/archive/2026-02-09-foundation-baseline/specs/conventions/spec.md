# Code and Project Conventions

## ADDED Requirements

### Requirement: Python Naming Convention
All Python code MUST use snake_case for modules, functions, and variables; PascalCase for classes; and UPPER_SNAKE_CASE for constants. Pydantic schemas MUST follow suffixed naming (In for input, Out for output).

#### Scenario: Django App Structure Naming
- **WHEN** a new Django app is created
- **THEN** the app name is snake_case plural (accounts, documents, ai)
- **AND** all Python files use snake_case (user_service.py, auth_schemas.py)
- **AND** class names use PascalCase (UserService, AccountController)

#### Scenario: Pydantic Schema Suffixes
- **WHEN** defining API schemas in schemas.py
- **THEN** input schemas use the In suffix (UserCreateIn, LoginIn)
- **AND** output schemas use the Out suffix (UserOut, TokenOut)
- **AND** partial update schemas use the Update suffix (UserUpdateIn)
- **AND** the suffix clearly indicates the schema's direction in the API contract

### Requirement: TypeScript Naming Convention
All TypeScript code MUST use kebab-case for file names, PascalCase for React components and types, camelCase for functions and variables, and UPPER_SNAKE_CASE for constants.

#### Scenario: React Component File Naming
- **WHEN** a React component is created
- **THEN** the file name is kebab-case (user-profile.tsx, auth-form.tsx)
- **AND** the exported component name is PascalCase (UserProfile, AuthForm)
- **AND** utility functions in the same file use camelCase (validateEmail, formatDate)

#### Scenario: Hook Naming Convention
- **WHEN** a custom React hook is created
- **THEN** the file name is kebab-case with use- prefix (use-auth.ts, use-current-user.ts)
- **AND** the hook function is camelCase with use prefix (useAuth, useCurrentUser)
- **AND** the hook follows React hooks rules (only call at top level)

### Requirement: ESLint and Prettier Code Quality
All TypeScript/JavaScript workspaces MUST use ESLint 9 flat config for linting and Prettier for formatting. ESLint and Prettier MUST run as separate tools (NOT via eslint-plugin-prettier).

#### Scenario: ESLint Flat Config Enforcement
- **WHEN** a workspace extends @repo/config-eslint in its eslint.config.js
- **THEN** all base rules (typescript-eslint recommended) are active
- **AND** workspace-specific plugins (React, Next.js) add additional rules
- **AND** running `pnpm lint` fails if any ESLint rules are violated

#### Scenario: Prettier Formatting on Save
- **WHEN** a developer saves a TypeScript file
- **THEN** Prettier auto-formats the file according to .prettierrc
- **AND** ESLint does NOT conflict with Prettier formatting decisions
- **AND** the file passes both lint and format checks

### Requirement: ruff for Python Linting and Formatting
All Python code MUST use ruff for both linting and formatting. The root ruff.toml MUST define rules for all Django apps, replacing black, flake8, and isort.

#### Scenario: ruff Check and Format
- **WHEN** `ruff check .` is run from apps/api/
- **THEN** all Python files are linted against configured rules (E, F, I, N, W, UP, B, A, C4, SIM, TCH)
- **AND** violations are reported with file, line, and rule code
- **AND** `ruff check --fix .` automatically fixes auto-fixable issues

#### Scenario: Import Ordering Enforcement
- **WHEN** ruff lints a Python file with imports
- **THEN** imports are validated against isort-compatible ordering (stdlib, third-party, first-party)
- **AND** incorrect order is flagged or auto-fixed
- **AND** apps and config are recognized as first-party packages

### Requirement: Git Commit Message Format
All commit messages MUST follow conventional commits format: `<type>(<scope>): <description>`. Valid types are feat, fix, chore, docs, refactor, test, ci, style.

#### Scenario: Feature Commit Message
- **WHEN** a developer commits a new API endpoint
- **THEN** the commit message is formatted as `feat(api): add user profile update endpoint`
- **AND** the type is feat (new feature)
- **AND** the scope is api (Django backend)
- **AND** the description is concise and imperative mood

#### Scenario: Multi-Scope Commit Message
- **WHEN** a change affects both API and frontend
- **THEN** the commit message uses the primary scope or omits scope: `feat: add user profile feature`
- **AND** the commit body (optional) describes both changes
- **AND** the format remains consistent with conventional commits

### Requirement: Environment Variable Strategy
Each service MUST have a committed .env.example file with all required variables documented. Actual .env files MUST be gitignored. Client-exposed variables MUST use framework-specific prefixes (NEXT_PUBLIC_, EXPO_PUBLIC_).

#### Scenario: New Developer Onboarding
- **WHEN** a developer clones the repository for the first time
- **THEN** they copy .env.example to .env in each service directory (root, apps/api/, apps/web/)
- **AND** all services start successfully with the example values
- **AND** no secrets are committed to version control

#### Scenario: Next.js Client-Side Environment Variable
- **WHEN** Next.js code accesses process.env.NEXT_PUBLIC_API_URL
- **THEN** the variable is available in both server and client code
- **AND** the value is bundled into the client JavaScript
- **AND** variables without NEXT_PUBLIC_ prefix are NOT exposed to the browser

### Requirement: Pre-commit Hook Integration
The repository MUST use pre-commit framework to run ruff (Python) and lint-staged (JS/TS) before every commit. Hooks MUST be installed automatically after `pnpm install`.

#### Scenario: Python Pre-commit Hook Execution
- **WHEN** a developer commits Python files
- **THEN** pre-commit runs ruff check and ruff format on staged files
- **AND** auto-fixable issues are corrected and re-staged
- **AND** the commit proceeds only if all hooks pass

#### Scenario: TypeScript Pre-commit Hook Execution
- **WHEN** a developer commits TypeScript files
- **THEN** lint-staged runs ESLint and Prettier on staged files
- **AND** auto-fixable issues are corrected and re-staged
- **AND** the commit is blocked if any lint errors remain after fixes

### Requirement: Monorepo Package Scope
All internal packages MUST use the @repo/ scope and be marked `"private": true` in package.json. Internal dependencies MUST use the workspace:* protocol.

#### Scenario: Internal Package Dependency
- **WHEN** apps/web/package.json lists `"@repo/api-client": "workspace:*"`
- **THEN** pnpm resolves the dependency to the local packages/api-client directory
- **AND** no external registry lookup occurs
- **AND** the package is never accidentally published to npm (private: true)

#### Scenario: Package Exports Definition
- **WHEN** a shared package defines `"exports": { ".": "./src/index.ts" }`
- **THEN** consuming workspaces import from "@repo/package-name"
- **AND** TypeScript and bundlers resolve to the specified entry point
- **AND** internal file structure is encapsulated
