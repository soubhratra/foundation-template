# Monorepo Infrastructure

## ADDED Requirements

### Requirement: Turborepo Task Orchestration
The monorepo SHALL use Turborepo 2.x for task orchestration with parallel execution, caching, and dependency-aware build pipelines. The root `turbo.json` MUST define task graphs for build, dev, lint, test, and type-check commands across all workspaces.

#### Scenario: Parallel Development Server Execution
- **WHEN** a developer runs `turbo dev` from the repository root
- **THEN** all dev servers (Next.js web, Expo mobile, Django API) start in parallel
- **AND** each service logs to stdout with workspace-prefixed output
- **AND** the process continues until manually terminated

#### Scenario: Incremental Build with Caching
- **WHEN** a developer runs `turbo build` after changing only the api-client package
- **THEN** only packages/api-client and its dependents (web, mobile) are rebuilt
- **AND** unchanged packages use cached build artifacts
- **AND** the build completes faster than a full rebuild

### Requirement: pnpm Workspace Configuration
The monorepo SHALL use pnpm 9.x as the package manager with workspace protocol for internal dependencies. The `pnpm-workspace.yaml` MUST define workspace packages for all TypeScript/JavaScript applications and packages, excluding the Django project.

#### Scenario: Internal Package Dependency Resolution
- **WHEN** packages/api-client is listed as a dependency in apps/web/package.json using `"@repo/api-client": "workspace:*"`
- **THEN** pnpm links the local package directory instead of fetching from npm
- **AND** changes to api-client are immediately available to web without reinstalling

#### Scenario: Dependency Hoisting
- **WHEN** multiple packages depend on the same version of a third-party library
- **THEN** pnpm installs the library once in the root node_modules
- **AND** creates symlinks in each package's node_modules

### Requirement: Shared Configuration Packages
The monorepo SHALL provide shared configuration packages (@repo/config-eslint, @repo/config-ts) that all TypeScript/JavaScript workspaces extend. These packages MUST have zero internal monorepo dependencies and serve as the foundation layer.

#### Scenario: TypeScript Config Extension
- **WHEN** apps/web/tsconfig.json extends "@repo/config-ts/nextjs.json"
- **THEN** all base strict TypeScript settings are inherited
- **AND** web-specific overrides (paths, jsx) are applied on top
- **AND** changes to the shared config propagate to all consumers on next build

#### Scenario: ESLint Flat Config Composition
- **WHEN** apps/mobile/eslint.config.js imports `reactNativeConfig` from "@repo/config-eslint"
- **THEN** all base ESLint rules are applied
- **AND** React Native-specific plugins and rules are active
- **AND** linting is consistent across all workspaces

### Requirement: Root Package.json Orchestration
The root package.json SHALL define workspace-wide scripts that delegate to Turborepo for task execution. The root MUST NOT contain application code or build artifacts, only orchestration scripts and shared development tooling.

#### Scenario: Root Script Delegation
- **WHEN** a developer runs `pnpm lint` from the repository root
- **THEN** the command delegates to `turbo lint`
- **AND** Turborepo executes the lint task for all workspaces in parallel
- **AND** the exit code reflects the combined status of all lint tasks

### Requirement: Python Integration via Minimal Package.json
The Django project (apps/api) SHALL participate in Turborepo pipelines via a minimal package.json containing only script definitions. Python dependencies MUST be managed by uv/pyproject.toml, NOT by pnpm.

#### Scenario: Django Lint Task Registration
- **WHEN** apps/api/package.json defines `"lint": "ruff check ."`
- **THEN** `turbo lint` includes the Django linting task in its execution graph
- **AND** ruff executes against Python files using the root ruff.toml configuration
- **AND** no pnpm dependencies are installed in apps/api

#### Scenario: OpenAPI Schema Export Integration
- **WHEN** apps/api/package.json defines `"export-schema": "python manage.py export_openapi_schema > ../../packages/api-client/openapi.json"`
- **THEN** `turbo export-schema` writes the OpenAPI spec to the api-client package
- **AND** the api-client generate:types task can depend on this output

### Requirement: Task Pipeline Dependencies
The turbo.json configuration MUST define explicit task dependencies using `dependsOn` to enforce correct execution order. All build-dependent tasks MUST wait for upstream package builds to complete.

#### Scenario: Type Generation Pipeline
- **WHEN** turbo.json defines api-client generate:types task with `"dependsOn": ["@repo/api#export-schema"]`
- **THEN** running `turbo generate:types` first exports the Django OpenAPI schema
- **AND** only after export completes does openapi-typescript generate types
- **AND** type-check tasks for web and mobile wait for generate:types to finish
