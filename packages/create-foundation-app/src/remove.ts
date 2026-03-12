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

/**
 * Remove observability module from generated project
 *
 * Steps:
 * 1. Delete apps/api/apps/core/observability.py
 * 2. Remove ObservabilityMiddleware from MIDDLEWARE in base.py
 * 3. Remove OBSERVABILITY MODULE settings block from base.py
 * 4. Remove task_failure signal handler from apps/api/apps/core/apps.py
 * 5. Remove posthog dep from apps/api/pyproject.toml
 * 6. Remove PostHogProvider + posthog.init from apps/web/app/providers.tsx;
 *    remove PostHog env vars from apps/web/.env.example
 * 7. Remove PostHogProvider + PostHogScreenTracker from apps/mobile/app/_layout.tsx;
 *    remove PostHog env var from apps/mobile/.env.example
 */
export async function removeObservability(outputDir: string): Promise<void> {
  logger.info("Removing observability module...");

  // 1. Delete apps/api/apps/core/observability.py
  const observabilityPyPath = join(outputDir, "apps/api/apps/core/observability.py");
  try {
    await remove(observabilityPyPath);
    logger.info(`  ✓ Deleted ${observabilityPyPath}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete observability.py: ${error}`);
    }
    logger.warning(`  ⚠ observability.py not found (already removed)`);
  }

  // 2 & 3. Modify base.py: remove ObservabilityMiddleware line + OBSERVABILITY MODULE block
  const basePyPath = join(outputDir, "apps/api/config/settings/base.py");
  try {
    let basePyContent = await readFile(basePyPath, "utf-8");

    // Remove "apps.core.middleware.ObservabilityMiddleware" line from MIDDLEWARE
    basePyContent = basePyContent.replace(
      /\s*"apps\.core\.middleware\.ObservabilityMiddleware",[^\n]*\n/g,
      "",
    );

    // Remove the OBSERVABILITY MODULE settings block (delimited by dash comment lines)
    basePyContent = basePyContent.replace(
      /\n# -{10,}\n# OBSERVABILITY MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END OBSERVABILITY MODULE\n# -{10,}/,
      "",
    );

    await writeFile(basePyPath, basePyContent, "utf-8");
    logger.info(`  ✓ Removed observability entries from base.py`);
  } catch (error) {
    throw new Error(`Failed to modify settings/base.py: ${error}`);
  }

  // 4. Remove task_failure signal handler from apps.py (added by Plan 02 — avoids
  //    ImportError after observability.py is deleted)
  const appsPyPath = join(outputDir, "apps/api/apps/core/apps.py");
  try {
    let appsPyContent = await readFile(appsPyPath, "utf-8");

    // Remove the task_failure import line
    appsPyContent = appsPyContent.replace(/^from celery\.signals import task_failure\n/m, "");

    // Remove the @task_failure.connect decorated handler function block
    // Matches: decorator line + def line + body lines up to get_observability_adapter call
    appsPyContent = appsPyContent.replace(
      /@task_failure\.connect[\s\S]*?get_observability_adapter\(\)\.capture_exception[\s\S]*?\n\n/,
      "",
    );

    await writeFile(appsPyPath, appsPyContent, "utf-8");
    logger.info(`  ✓ Removed task_failure signal handler from apps.py`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify apps/core/apps.py: ${error}`);
    }
    logger.warning(`  ⚠ apps/core/apps.py not found (skipping task_failure removal)`);
  }

  // 5. Remove posthog dep from apps/api/pyproject.toml
  const pyprojectPath = join(outputDir, "apps/api/pyproject.toml");
  try {
    let pyprojectContent = await readFile(pyprojectPath, "utf-8");

    const depRegex = /^\s*"posthog[^"]*",?\s*$\n?/gm;
    pyprojectContent = pyprojectContent.replace(depRegex, "");

    await writeFile(pyprojectPath, pyprojectContent, "utf-8");
    logger.info(`  ✓ Removed posthog from pyproject.toml`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify pyproject.toml: ${error}`);
    }
    logger.warning(`  ⚠ pyproject.toml not found (skipping posthog dep removal)`);
  }

  // 6. Remove PostHog from apps/web/app/providers.tsx + env vars from apps/web/.env.example
  const providersTsxPath = join(outputDir, "apps/web/app/providers.tsx");
  try {
    let providersContent = await readFile(providersTsxPath, "utf-8");

    // Remove posthog-js import lines
    providersContent = providersContent.replace(/^import posthog from "posthog-js";\n/m, "");
    providersContent = providersContent.replace(
      /^import \{ PostHogProvider, usePostHog \} from "posthog-js\/react";\n/m,
      "",
    );

    // Remove posthog.init block (if (typeof window !== "undefined") { ... })
    providersContent = providersContent.replace(
      /^if \(typeof window !== "undefined"\) \{[\s\S]*?\n\}\n\n/m,
      "",
    );

    // Remove PostHogPageView component definition
    providersContent = providersContent.replace(
      /^function PostHogPageView\(\) \{[\s\S]*?\n\}\n\n/m,
      "",
    );

    // Remove <PostHogProvider client={posthog}> wrapper (outermost) — unwrap children
    // Remove opening tag
    providersContent = providersContent.replace(/^\s*<PostHogProvider client=\{posthog\}>\n/m, "");
    // Remove <PostHogPageView /> line
    providersContent = providersContent.replace(/^\s*<PostHogPageView \/>\n/m, "");
    // Remove closing tag
    providersContent = providersContent.replace(/^\s*<\/PostHogProvider>\n/m, "");

    await writeFile(providersTsxPath, providersContent, "utf-8");
    logger.info(`  ✓ Removed PostHog from providers.tsx`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify apps/web/app/providers.tsx: ${error}`);
    }
    logger.warning(`  ⚠ providers.tsx not found (skipping PostHog web removal)`);
  }

  // Remove NEXT_PUBLIC_POSTHOG_KEY and NEXT_PUBLIC_POSTHOG_HOST from apps/web/.env.example
  const webEnvExamplePath = join(outputDir, "apps/web/.env.example");
  try {
    let webEnvContent = await readFile(webEnvExamplePath, "utf-8");

    // Remove the PostHog comment line and the two env var lines
    webEnvContent = webEnvContent.replace(/^# PostHog analytics \(optional[^\n]*\)\n/m, "");
    webEnvContent = webEnvContent.replace(/^NEXT_PUBLIC_POSTHOG_KEY=.*$\n?/m, "");
    webEnvContent = webEnvContent.replace(/^NEXT_PUBLIC_POSTHOG_HOST=.*$\n?/m, "");

    await writeFile(webEnvExamplePath, webEnvContent, "utf-8");
    logger.info(`  ✓ Removed PostHog env vars from apps/web/.env.example`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify apps/web/.env.example: ${error}`);
    }
    logger.warning(`  ⚠ apps/web/.env.example not found (skipping)`);
  }

  // 7. Remove PostHog from apps/mobile/app/_layout.tsx + env var from apps/mobile/.env.example
  const layoutTsxPath = join(outputDir, "apps/mobile/app/_layout.tsx");
  try {
    let layoutContent = await readFile(layoutTsxPath, "utf-8");

    // Remove posthog-react-native import line
    layoutContent = layoutContent.replace(
      /^import \{ PostHogProvider, usePostHog \} from "posthog-react-native";\n/m,
      "",
    );

    // Remove useSegments from expo-router import (only if it was added for PostHog)
    // The import line includes other things — remove just useSegments if it's the only extra item
    // Pattern: ", useSegments" or "useSegments, " within the expo-router import
    layoutContent = layoutContent.replace(/,\s*useSegments(?=\s*\})/, "");
    layoutContent = layoutContent.replace(/useSegments,\s*/, "");

    // Remove PostHogScreenTracker component definition
    layoutContent = layoutContent.replace(
      /^function PostHogScreenTracker\(\) \{[\s\S]*?\n\}\n\n/m,
      "",
    );

    // Remove <PostHogProvider ...> wrapper — unwrap children
    // Remove opening PostHogProvider tag (multi-line, safe string splice):
    // Find the tag start, then find the closing standalone ">" line and slice out the whole range
    {
      const tagStart = layoutContent.indexOf("    <PostHogProvider");
      if (tagStart !== -1) {
        // Find the next line that is just whitespace + ">" (the JSX self-closing brace)
        const closeArrow = layoutContent.indexOf("\n    >", tagStart);
        if (closeArrow !== -1) {
          // Remove from tagStart to end of the ">\n" line
          layoutContent =
            layoutContent.slice(0, tagStart) + layoutContent.slice(closeArrow + "\n    >\n".length);
        }
      }
    }
    // Remove <PostHogScreenTracker /> line
    layoutContent = layoutContent.replace(/[ \t]*<PostHogScreenTracker \/>\n/, "");
    // Remove closing </PostHogProvider> tag
    layoutContent = layoutContent.replace(/[ \t]*<\/PostHogProvider>\n/, "");

    await writeFile(layoutTsxPath, layoutContent, "utf-8");
    logger.info(`  ✓ Removed PostHog from _layout.tsx`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify apps/mobile/app/_layout.tsx: ${error}`);
    }
    logger.warning(`  ⚠ _layout.tsx not found (skipping PostHog mobile removal)`);
  }

  // Remove EXPO_PUBLIC_POSTHOG_KEY from apps/mobile/.env.example
  const mobileEnvExamplePath = join(outputDir, "apps/mobile/.env.example");
  try {
    let mobileEnvContent = await readFile(mobileEnvExamplePath, "utf-8");

    // Remove the PostHog comment line and the env var line
    mobileEnvContent = mobileEnvContent.replace(/^# PostHog analytics \(optional[^\n]*\)\n/m, "");
    mobileEnvContent = mobileEnvContent.replace(/^EXPO_PUBLIC_POSTHOG_KEY=.*$\n?/m, "");

    await writeFile(mobileEnvExamplePath, mobileEnvContent, "utf-8");
    logger.info(`  ✓ Removed PostHog env var from apps/mobile/.env.example`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify apps/mobile/.env.example: ${error}`);
    }
    logger.warning(`  ⚠ apps/mobile/.env.example not found (skipping)`);
  }

  logger.info("✓ Observability module removed successfully");
}

/**
 * Remove email module from generated project
 *
 * Steps:
 * 1. Delete apps/api/apps/notifications/ directory
 * 2. Remove "anymail" and "apps.notifications" lines from INSTALLED_APPS in base.py
 * 3. Remove EMAIL MODULE settings block from base.py
 * 4. Remove RESEND_API_KEY and DEFAULT_FROM_EMAIL from apps/api/.env.example
 */
export async function removeEmailModule(outputDir: string): Promise<void> {
  logger.info("Removing email module...");

  // 1. Delete apps/api/apps/notifications/ directory
  const notificationsDir = join(outputDir, "apps/api/apps/notifications");
  try {
    await remove(notificationsDir);
    logger.info(`  ✓ Deleted ${notificationsDir}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to delete notifications directory: ${error}`);
    }
    logger.warning(`  ⚠ notifications directory not found (already removed)`);
  }

  // 2 & 3. Modify base.py: remove INSTALLED_APPS email lines and EMAIL MODULE settings block
  const basePyPath = join(outputDir, "apps/api/config/settings/base.py");
  try {
    let basePyContent = await readFile(basePyPath, "utf-8");

    // Remove "anymail" and "apps.notifications" lines (both have EMAIL MODULE comment sentinel)
    basePyContent = basePyContent.replace(/\s*"anymail",[^\n]*# EMAIL MODULE[^\n]*\n/g, "");
    basePyContent = basePyContent.replace(
      /\s*"apps\.notifications",[^\n]*# EMAIL MODULE[^\n]*\n/g,
      "",
    );

    // Remove EMAIL MODULE settings block (dash-comment fenced)
    basePyContent = basePyContent.replace(
      /\n# -{10,}\n# EMAIL MODULE\n# -{10,}[\s\S]*?# -{10,}\n# END EMAIL MODULE\n# -{10,}/,
      "",
    );

    await writeFile(basePyPath, basePyContent, "utf-8");
    logger.info(`  ✓ Removed email entries from base.py`);
  } catch (error) {
    throw new Error(`Failed to modify settings/base.py: ${error}`);
  }

  // 4. Remove RESEND_API_KEY and DEFAULT_FROM_EMAIL from apps/api/.env.example
  const envExamplePath = join(outputDir, "apps/api/.env.example");
  try {
    let envContent = await readFile(envExamplePath, "utf-8");
    envContent = envContent.replace(/^# Email \(Transactional\)\n/m, "");
    envContent = envContent.replace(/^RESEND_API_KEY=.*\n?/m, "");
    envContent = envContent.replace(/^DEFAULT_FROM_EMAIL=.*\n?/m, "");
    await writeFile(envExamplePath, envContent, "utf-8");
    logger.info(`  ✓ Removed email env vars from .env.example`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw new Error(`Failed to modify .env.example: ${error}`);
    }
    logger.warning(`  ⚠ .env.example not found (skipping)`);
  }

  logger.info("Email module removed.");
}
