# create-foundation-app

CLI scaffolder for Foundation Template projects. Generates a complete full-stack SaaS monorepo with Django Ninja Extra (backend), Next.js 15 (web), React Native Expo (mobile), and optional AI module.

## Features

- Interactive prompts for project configuration
- Feature selection (web, mobile, landing, AI module)
- Template transformation with project name replacement
- Cryptographic secret generation for Django and database
- Feature removal for excluded platforms
- Post-generation validation (linting + type-checking)
- Automatic rollback on errors

## Installation

### Development Usage

From the monorepo root:

```bash
cd packages/create-foundation-app
pnpm install
pnpm build
node bin/cli.js
```

### After Publishing (Future)

```bash
npx create-foundation-app
# or
pnpm create foundation-app
```

## Usage

### Basic Usage

Run the CLI and follow the interactive prompts:

```bash
node bin/cli.js
```

The CLI will ask for:

1. **Project name**: Must be a valid npm package name (lowercase, hyphens allowed, no spaces)
2. **Features**: Select which platforms to include (web, mobile, landing, ai)
3. **Output directory**: Where to create the project (must be empty or non-existent)

### CLI Flags

#### `--skip-validation`

Skip post-generation validation (dependency installation, linting, type-checking).

Useful for:

- Faster generation during testing
- Offline development
- CI/CD environments where validation runs separately

```bash
node bin/cli.js --skip-validation
```

**Note:** When validation is skipped, you'll need to manually run:

```bash
cd your-project
pnpm install
pnpm turbo db:migrate
```

## Examples

### Full Stack Project (All Features)

```bash
node bin/cli.js
# Select: web, mobile, landing, ai
# Output: ./my-saas-app
```

Generates:

- `apps/web/` - Next.js web application
- `apps/mobile/` - React Native Expo mobile app
- `apps/landing/` - Static marketing site
- `apps/api/` - Django Ninja Extra API (with AI module)
- `packages/` - Shared packages

### Backend + Web Only (No Mobile, No AI)

```bash
node bin/cli.js
# Uncheck: mobile, ai
# Select: web, landing
```

Generates:

- `apps/web/` - Next.js web application
- `apps/landing/` - Static marketing site
- `apps/api/` - Django Ninja Extra API (no AI module)
- `packages/` - Shared packages
- No `apps/mobile/` directory
- No AI dependencies in `pyproject.toml`

### Quick Test Project (Skip Validation)

```bash
node bin/cli.js --skip-validation
```

Generates project without running validation. Validation takes 5-15 minutes depending on machine speed.

## What Gets Generated

### All Projects Include

- Turborepo monorepo configuration
- pnpm workspace setup
- Shared TypeScript configuration
- ESLint and Prettier config
- Pre-commit hooks (lint-staged, ruff, prettier)
- Docker Compose for local development (Postgres, Redis)
- GitHub Actions CI/CD workflows
- Environment file (.env) with unique secrets

### Feature-Specific

| Feature | Adds                                          |
| ------- | --------------------------------------------- |
| web     | Next.js 15 app with Shadcn/UI, Tailwind, auth |
| mobile  | React Native Expo app with Expo Router        |
| landing | Static marketing site (Next.js)               |
| ai      | LangGraph agents, PGVector, Celery task queue |

## Post-Generation Steps

After the CLI completes, follow these steps:

```bash
cd your-project

# If you used --skip-validation, install dependencies first
pnpm install  # (skip if validation ran)

# Start local services
docker compose up -d

# Run database migrations
pnpm turbo db:migrate  # or pnpm db:migrate if --skip-validation

# Start all dev servers
pnpm dev
```

Visit:

- Web app: http://localhost:3000
- API docs: http://localhost:8000/api/docs
- Mobile: Use Expo Go app (scan QR code from terminal)

## Troubleshooting

### "Directory is not empty"

The output directory must be empty or non-existent. Either:

1. Choose a different directory name
2. Delete the existing directory
3. Move files out of the directory

### "Invalid package name"

Project names must:

- Be lowercase
- Use hyphens (not spaces or underscores)
- Not contain special characters
- Follow npm package naming rules

Examples:

- ✓ `my-saas-app`
- ✓ `acme-product`
- ✗ `My SaaS App` (uppercase, spaces)
- ✗ `my_app` (underscores)

### Validation Timeout

If validation times out on slow machines:

1. Run with `--skip-validation` flag
2. Manually run validation after generation:

```bash
cd your-project
pnpm install
pnpm turbo lint
pnpm turbo type-check
```

### Generation Failed / Partial Output

The CLI automatically rolls back on errors. If you see partial files:

1. Delete the output directory manually
2. Check the error message for the root cause
3. Fix the issue (e.g., disk space, permissions)
4. Re-run the CLI

## Architecture

The CLI follows this flow:

1. **Prompts**: Collect project name, features, output directory
2. **Copy**: Copy template files (excluding build artifacts, .git, .planning)
3. **Transform**: Replace placeholders (`foundation-template` → `your-project`)
4. **Secrets**: Generate unique Django SECRET_KEY and database passwords
5. **Remove**: Delete excluded features (AI module, mobile app, landing)
6. **Validate** (optional): Install deps, run linting, run type-checking
7. **Success**: Show next steps

On error, the CLI rolls back (deletes output directory).

## Development

### Build

```bash
pnpm build
```

Compiles TypeScript to `dist/` directory.

### Type Check

```bash
pnpm type-check
```

Runs TypeScript compiler in no-emit mode.

### Watch Mode

```bash
pnpm dev
```

Rebuilds on file changes.

## License

MIT
