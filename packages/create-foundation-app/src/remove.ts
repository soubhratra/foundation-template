import fse from "fs-extra";
const { readFile, writeFile, remove } = fse;
import { join } from "node:path";
import { logger } from "./utils.js";

/**
 * Remove AI module from generated project
 *
 * Steps:
 * 1. Delete apps/api/apps/ai/ directory
 * 2. Remove AI dependencies from pyproject.toml
 * 3. Remove apps.ai from INSTALLED_APPS
 * 4. Remove AI env vars from .env file
 */
export async function removeAIModule(outputDir: string): Promise<void> {
  logger.info("Removing AI module...");

  // 1. Delete AI directory
  const aiDir = join(outputDir, "apps/api/apps/ai");
  try {
    await remove(aiDir);
    logger.info(`  ✓ Deleted ${aiDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete AI directory: ${error}`);
    }
    logger.warning(`  ⚠ AI directory not found (already removed)`);
  }

  // 2. Remove AI dependencies from pyproject.toml
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  try {
    let pyprojectContent = await readFile(pyprojectPath, "utf-8");

    // Remove AI-related dependencies (each on its own line)
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
      // Match lines like: "pgvector>=0.2.0",
      // Handles both with and without trailing comma
      const depRegex = new RegExp(`^\\s*"${dep}[^"]*",?\\s*$`, "gm");
      pyprojectContent = pyprojectContent.replace(depRegex, "");
    }

    await writeFile(pyprojectPath, pyprojectContent, "utf-8");
    logger.info(`  ✓ Removed AI dependencies from pyproject.toml`);
  } catch (error) {
    throw new Error(`Failed to modify pyproject.toml: ${error}`);
  }

  // 3. Remove apps.ai from INSTALLED_APPS
  const settingsPath = join(outputDir, "apps/api/config/settings/base.py");
  try {
    let settingsContent = await readFile(settingsPath, "utf-8");

    // Match lines like: "apps.ai",
    const appsAiRegex = /\s*"apps\.ai",?\n/g;
    settingsContent = settingsContent.replace(appsAiRegex, "");

    await writeFile(settingsPath, settingsContent, "utf-8");
    logger.info(`  ✓ Removed apps.ai from INSTALLED_APPS`);
  } catch (error) {
    throw new Error(`Failed to modify settings/base.py: ${error}`);
  }

  // 4. Remove AI env vars from .env
  const envPath = join(outputDir, ".env");
  try {
    let envContent = await readFile(envPath, "utf-8");

    // Remove Celery and OpenAI lines
    const celeryBrokerRegex = /^CELERY_BROKER_URL=.*$\n?/gm;
    const celeryResultRegex = /^CELERY_RESULT_BACKEND=.*$\n?/gm;
    const openaiKeyRegex = /^#?\s*OPENAI_API_KEY=.*$\n?/gm;

    envContent = envContent.replace(celeryBrokerRegex, "");
    envContent = envContent.replace(celeryResultRegex, "");
    envContent = envContent.replace(openaiKeyRegex, "");

    await writeFile(envPath, envContent, "utf-8");
    logger.info(`  ✓ Removed AI env vars from .env`);
  } catch (error) {
    throw new Error(`Failed to modify .env: ${error}`);
  }

  logger.info("✓ AI module removed successfully");
}

/**
 * Remove mobile app from generated project
 *
 * Steps:
 * 1. Delete apps/mobile/ directory
 * 2. Remove from pnpm-workspace.yaml
 */
export async function removeMobileApp(outputDir: string): Promise<void> {
  logger.info("Removing mobile app...");

  // 1. Delete mobile directory
  const mobileDir = join(outputDir, "apps/mobile");
  try {
    await remove(mobileDir);
    logger.info(`  ✓ Deleted ${mobileDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete mobile directory: ${error}`);
    }
    logger.warning(`  ⚠ Mobile directory not found (already removed)`);
  }

  // 2. Update pnpm-workspace.yaml
  const workspacePath = join(outputDir, "pnpm-workspace.yaml");
  try {
    let workspaceContent = await readFile(workspacePath, "utf-8");

    // Replace wildcard with explicit list (without mobile)
    // Original: packages: ["apps/*", "packages/*"]
    // New: packages: ["apps/web", "apps/landing", "apps/api", "packages/*"]
    if (workspaceContent.includes('"apps/*"')) {
      workspaceContent = workspaceContent.replace(
        /packages:\s*\[\s*"apps\/\*"/,
        'packages: [\n  "apps/web",\n  "apps/landing",\n  "apps/api"',
      );

      await writeFile(workspacePath, workspaceContent, "utf-8");
      logger.info(`  ✓ Removed mobile from pnpm-workspace.yaml`);
    }
  } catch (error) {
    throw new Error(`Failed to modify pnpm-workspace.yaml: ${error}`);
  }

  logger.info("✓ Mobile app removed successfully");
}

/**
 * Remove landing app from generated project
 *
 * Steps:
 * 1. Delete apps/landing/ directory
 * 2. Remove from pnpm-workspace.yaml
 */
export async function removeLandingApp(outputDir: string): Promise<void> {
  logger.info("Removing landing app...");

  // 1. Delete landing directory
  const landingDir = join(outputDir, "apps/landing");
  try {
    await remove(landingDir);
    logger.info(`  ✓ Deleted ${landingDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete landing directory: ${error}`);
    }
    logger.warning(`  ⚠ Landing directory not found (already removed)`);
  }

  // 2. Update pnpm-workspace.yaml
  const workspacePath = join(outputDir, "pnpm-workspace.yaml");
  try {
    let workspaceContent = await readFile(workspacePath, "utf-8");

    // Remove landing from explicit list
    workspaceContent = workspaceContent.replace(/\s*"apps\/landing",?\n?/g, "");

    await writeFile(workspacePath, workspaceContent, "utf-8");
    logger.info(`  ✓ Removed landing from pnpm-workspace.yaml`);
  } catch (error) {
    throw new Error(`Failed to modify pnpm-workspace.yaml: ${error}`);
  }

  logger.info("✓ Landing app removed successfully");
}

/**
 * Remove web app from generated project
 *
 * Steps:
 * 1. Delete apps/web/ directory
 * 2. Remove from pnpm-workspace.yaml
 */
export async function removeWebApp(outputDir: string): Promise<void> {
  logger.info("Removing web app...");

  // 1. Delete web directory
  const webDir = join(outputDir, "apps/web");
  try {
    await remove(webDir);
    logger.info(`  ✓ Deleted ${webDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete web directory: ${error}`);
    }
    logger.warning(`  ⚠ Web directory not found (already removed)`);
  }

  // 2. Update pnpm-workspace.yaml
  const workspacePath = join(outputDir, "pnpm-workspace.yaml");
  try {
    let workspaceContent = await readFile(workspacePath, "utf-8");

    // Remove web from explicit list
    workspaceContent = workspaceContent.replace(/\s*"apps\/web",?\n?/g, "");

    await writeFile(workspacePath, workspaceContent, "utf-8");
    logger.info(`  ✓ Removed web from pnpm-workspace.yaml`);
  } catch (error) {
    throw new Error(`Failed to modify pnpm-workspace.yaml: ${error}`);
  }

  logger.info("✓ Web app removed successfully");
}

/**
 * Remove billing module from generated project
 *
 * Steps:
 * 1. Delete apps/api/apps/billing/ directory
 * 2. Remove "apps.billing" from INSTALLED_APPS in base.py
 * 3. Remove BILLING MODULE settings block from base.py
 * 4. Remove BILLING_ADAPTER line from development.py
 * 5. Remove BILLING_START/BILLING_END URL block from urls.py
 * 6. Remove billing import line from urls.py
 * 7. Delete apps/web/app/(dashboard)/billing/ directory
 * 8. Delete apps/web/billing.config.ts
 * 9. Remove stripe/weasyprint deps from pyproject.toml
 */
export async function removeBillingModule(outputDir: string): Promise<void> {
  logger.info("Removing billing module...");

  // 1. Delete apps/api/apps/billing/ directory
  const billingApiDir = join(outputDir, "apps/api/apps/billing");
  try {
    await remove(billingApiDir);
    logger.info(`  ✓ Deleted ${billingApiDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete billing API directory: ${error}`);
    }
    logger.warning(`  ⚠ Billing API directory not found (already removed)`);
  }

  // 2 & 3. Modify base.py: remove INSTALLED_APPS line and BILLING MODULE block
  const basePyPath = join(outputDir, "apps/api/config/settings/base.py");
  try {
    let basePyContent = await readFile(basePyPath, "utf-8");

    // Remove "apps.billing" line from INSTALLED_APPS
    basePyContent = basePyContent.replace(/\s*"apps\.billing",[^\n]*\n/g, "");

    // Remove the BILLING MODULE settings block (delimited by dash comment lines)
    basePyContent = basePyContent.replace(
      /\n# -{10,}\n# BILLING MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END BILLING MODULE\n# -{10,}/,
      "",
    );

    await writeFile(basePyPath, basePyContent, "utf-8");
    logger.info(`  ✓ Removed billing entries from base.py`);
  } catch (error) {
    throw new Error(`Failed to modify settings/base.py: ${error}`);
  }

  // 4. Remove BILLING_ADAPTER line from development.py only
  const devPyPath = join(outputDir, "apps/api/config/settings/development.py");
  try {
    let devPyContent = await readFile(devPyPath, "utf-8");

    // Remove only the BILLING_ADAPTER line
    devPyContent = devPyContent.replace(/^BILLING_ADAPTER\s*=.*$\n?/m, "");

    await writeFile(devPyPath, devPyContent, "utf-8");
    logger.info(`  ✓ Removed BILLING_ADAPTER from development.py`);
  } catch (error) {
    throw new Error(`Failed to modify settings/development.py: ${error}`);
  }

  // 5 & 6. Modify urls.py: remove BILLING block and billing import
  const urlsPyPath = join(outputDir, "apps/api/config/urls.py");
  try {
    let urlsContent = await readFile(urlsPyPath, "utf-8");

    // Remove the BILLING_START / BILLING_END block (including surrounding whitespace)
    urlsContent = urlsContent.replace(/[ \t]*# BILLING_START\n[\s\S]*?# BILLING_END\n?/, "");

    // Remove the billing import line
    urlsContent = urlsContent.replace(/^from apps\.billing[^\n]*\n/m, "");

    await writeFile(urlsPyPath, urlsContent, "utf-8");
    logger.info(`  ✓ Removed billing URL block and import from urls.py`);
  } catch (error) {
    throw new Error(`Failed to modify urls.py: ${error}`);
  }

  // 7. Delete apps/web/app/(dashboard)/billing/ directory
  const billingWebDir = join(outputDir, "apps/web/app/(dashboard)/billing");
  try {
    await remove(billingWebDir);
    logger.info(`  ✓ Deleted ${billingWebDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete billing web directory: ${error}`);
    }
    logger.warning(`  ⚠ Billing web directory not found (already removed)`);
  }

  // 8. Delete apps/web/billing.config.ts
  const billingConfigPath = join(outputDir, "apps/web/billing.config.ts");
  try {
    await remove(billingConfigPath);
    logger.info(`  ✓ Deleted ${billingConfigPath}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete billing.config.ts: ${error}`);
    }
    logger.warning(`  ⚠ billing.config.ts not found (already removed)`);
  }

  // 9. Remove stripe and weasyprint deps from pyproject.toml
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  try {
    let pyprojectContent = await readFile(pyprojectPath, "utf-8");

    const billingDeps = ["stripe", "weasyprint"];
    for (const dep of billingDeps) {
      const depRegex = new RegExp(`^\\s*"${dep}[^"]*",?\\s*$`, "gm");
      pyprojectContent = pyprojectContent.replace(depRegex, "");
    }

    await writeFile(pyprojectPath, pyprojectContent, "utf-8");
    logger.info(`  ✓ Removed stripe/weasyprint from pyproject.toml`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify pyproject.toml: ${error}`);
    }
    logger.warning(`  ⚠ pyproject.toml not found (skipping dep removal)`);
  }

  logger.info("✓ Billing module removed successfully");
}
