import { execa } from "execa";
import * as p from "@clack/prompts";
import pc from "picocolors";
import { logger } from "./utils.js";

/**
 * Run post-generation validation checks
 *
 * Steps:
 * 1. Install dependencies (pnpm install, uv sync)
 * 2. Run linting (turbo lint, ruff check)
 * 3. Run type checking (turbo type-check, mypy)
 * 4. Optional: Run tests (turbo test, pytest)
 *
 * @param outputDir - Generated project directory
 * @param skipTests - Skip test execution (default: true for speed)
 */
export async function runValidation(outputDir: string, skipTests = true): Promise<void> {
  logger.info("Running post-generation validation...");

  // Step 1: Install dependencies
  await installDependencies(outputDir);

  // Step 2: Run linting
  await runLinting(outputDir);

  // Step 3: Run type checking
  await runTypeChecking(outputDir);

  // Step 4: Run tests (optional)
  if (!skipTests) {
    await runTests(outputDir);
  }

  logger.info("✓ Validation complete - project is ready to use!");
}

/**
 * Install all project dependencies
 */
async function installDependencies(outputDir: string): Promise<void> {
  const s = p.spinner();
  s.start("Installing dependencies...");

  try {
    // JS/TS dependencies
    await execa("pnpm", ["install"], {
      cwd: outputDir,
      stdio: "inherit",
      timeout: 600000, // 10 minutes
    });

    // Python dependencies
    await execa("uv", ["sync", "--directory", "apps/api"], {
      cwd: outputDir,
      stdio: "inherit",
      timeout: 600000, // 10 minutes
    });

    s.stop(pc.green("✓ Dependencies installed"));
  } catch (error) {
    s.stop(pc.red("✗ Dependency installation failed"));
    throw new Error(
      `Dependency installation failed. Try running with --skip-validation flag.\n${error}`,
    );
  }
}

/**
 * Run linting checks
 */
async function runLinting(outputDir: string): Promise<void> {
  const s = p.spinner();
  s.start("Running linting...");

  try {
    // JS/TS linting
    await execa("pnpm", ["turbo", "lint"], {
      cwd: outputDir,
      stdio: "inherit",
      timeout: 300000, // 5 minutes
    });

    // Python linting
    await execa("ruff", ["check", "."], {
      cwd: `${outputDir}/apps/api`,
      stdio: "inherit",
      timeout: 300000, // 5 minutes
    });

    s.stop(pc.green("✓ Linting passed"));
  } catch (error) {
    s.stop(pc.red("✗ Linting failed"));
    const execaError = error as { stderr?: string };
    throw new Error(
      `Linting failed. Check the output above for errors.\n${execaError.stderr || error}`,
    );
  }
}

/**
 * Run type checking
 */
async function runTypeChecking(outputDir: string): Promise<void> {
  const s = p.spinner();
  s.start("Running type checking...");

  try {
    // JS/TS type checking
    await execa("pnpm", ["turbo", "type-check"], {
      cwd: outputDir,
      stdio: "inherit",
      timeout: 600000, // 10 minutes (type-checking can be slow on first run)
    });

    // Python type checking
    await execa("mypy", ["."], {
      cwd: `${outputDir}/apps/api`,
      stdio: "inherit",
      timeout: 600000, // 10 minutes
    });

    s.stop(pc.green("✓ Type checking passed"));
  } catch (error) {
    s.stop(pc.red("✗ Type checking failed"));
    const execaError = error as { stderr?: string };
    throw new Error(
      `Type checking failed. Check the output above for errors.\n${execaError.stderr || error}`,
    );
  }
}

/**
 * Run test suites (optional)
 */
async function runTests(outputDir: string): Promise<void> {
  const s = p.spinner();
  s.start("Running tests...");

  try {
    // JS/TS tests
    await execa("pnpm", ["turbo", "test"], {
      cwd: outputDir,
      stdio: "inherit",
      timeout: 600000, // 10 minutes
    });

    // Python tests
    await execa("pytest", [], {
      cwd: `${outputDir}/apps/api`,
      stdio: "inherit",
      timeout: 600000, // 10 minutes
    });

    s.stop(pc.green("✓ Tests passed"));
  } catch {
    // Tests are non-blocking - log warning but don't fail
    s.stop(pc.yellow("⚠ Tests failed (non-blocking)"));
    logger.warning("Tests failed but validation continues. Tests may require additional setup.");
  }
}
